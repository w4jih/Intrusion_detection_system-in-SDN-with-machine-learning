from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch, RemoteController
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import setLogLevel

class SimpleTopology(Topo):
    def build(self):
        # Create the switch
        switch = self.addSwitch('s1')

        # Create two hosts and connect them to the switch
        host1 = self.addHost('h1')
        host2 = self.addHost('h2')
        self.addLink(host1, switch)
        self.addLink(host2, switch)

        # Connect the switch to the Ryu controller
        # Here we assume that the controller is running on localhost:6653 (default)
        self.addLink(switch, self.addHost('controller'))

def run():
    # Set the logging level to display information about what's going on
    setLogLevel('info')

    # Create the network with the custom topology
    topo = SimpleTopology()

    # Define the controller (remote controller on localhost)
    net = Mininet(topo=topo, controller=RemoteController)

    # Start the network
    net.start()

    # Start the CLI to interact with the Mininet network
    CLI(net)

    # Stop the network after exiting the CLI
    net.stop()

if __name__ == '__main__':
    run()