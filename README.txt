install mininet in Ubuntu
install openflow Library
install ryu controller
install hping3 for attack simulation
run the the convert.py after modifiying the path to the dataset to convert all labels that are not begnin to malicious.
run the topo.py with commande:sudo mn --custom topo.py --controller=remote,ip=127.0.0.1
run the simple_monitor.py on the ryu controller by this command:ryu-manager ryu.app.simple_switch
run the final_model.py to predict the labels on the non labeled dataset
 