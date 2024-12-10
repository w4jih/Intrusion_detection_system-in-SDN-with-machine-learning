from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import hub

import joblib
import pandas as pd
import csv


class PredictModel(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PredictModel, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.mac_to_port = {}  # Dictionary to store MAC-to-port mappings
        self.model = joblib.load('flow_model.pkl')  # Load trained model
        self.scaler = joblib.load('scaler.pkl')    # Load scaler
        self.csv_file = 'predicted_dataset.csv'

        # Initialize output CSV with headers
        with open(self.csv_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Datapath ID', 'Flow Duration', 'Total Fwd Packets',
                'Flow Bytes/s', 'Fwd Packet Length Mean', 'Bwd Packet Length Std',
                'Predicted Class'
            ])

        # Start periodic flow stats request
        self.monitor_thread = hub.spawn(self._start_flow_stats_request)

    def _start_flow_stats_request(self):
        """Periodically request flow stats from all datapaths."""
        while True:
            for dp in self.datapaths.values():
                self._send_flow_stats_request(dp)
            hub.sleep(10)  # Request flow stats every 10 seconds

    def _send_flow_stats_request(self, datapath):
        """Send flow stats request to a datapath."""
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, CONFIG_DISPATCHER])
    def state_change_handler(self, ev):
        """Track datapath registration."""
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info("Registering datapath: %016x", datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == CONFIG_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info("Unregistering datapath: %016x", datapath.id)
                del self.datapaths[datapath.id]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Install table-miss flow entry."""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Table-miss flow entry: send unmatched packets to the controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        """Add a flow entry."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        """Handle flow stats reply, predict labels, and display results."""
        datapath_id = ev.msg.datapath.id
        body = ev.msg.body

        for stat in body:
            # Gather metrics
            flow_duration = stat.duration_sec + stat.duration_nsec / 1e9
            total_fwd_packets = stat.packet_count
            flow_bytes_per_sec = stat.byte_count / flow_duration if flow_duration > 0 else 0
            fwd_packet_length_mean = stat.byte_count / stat.packet_count if stat.packet_count > 0 else 0
            bwd_packet_length_std = 0  # Placeholder

            # Prepare row for prediction
            row = [flow_duration, total_fwd_packets, flow_bytes_per_sec,
                   fwd_packet_length_mean, bwd_packet_length_std]

            # Preprocess data
            X_row = pd.DataFrame([row], columns=[
                'Flow Duration', 'Total Fwd Packets', 'Flow Bytes/s',
                'Fwd Packet Length Mean', 'Bwd Packet Length Std'
            ])
            X_scaled = self.scaler.transform(X_row)

            # Predict label
            predicted_label = self.model.predict(X_scaled)[0]

            # Display results
            self.logger.info("Datapath ID: %s, Row: %s, Predicted Class: %s",
                             datapath_id, row, predicted_label)

            # Append results to CSV
            with open(self.csv_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datapath_id, flow_duration, total_fwd_packets,
                    flow_bytes_per_sec, fwd_packet_length_mean, bwd_packet_length_std,
                    predicted_label
                ])

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Handle packets arriving at the controller."""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # Learn the MAC address to avoid FLOOD next time
        self.mac_to_port[dpid][src] = in_port

        # Determine output port
        out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)

        # Install flow rule to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            actions = [parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, 1, match, actions)

        # Forward the packet
        actions = [parser.OFPActionOutput(out_port)]
        data = msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
