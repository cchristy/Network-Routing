'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import network
import link
import threading
from time import sleep
import sys

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 1 #give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads
    
    #create network hosts
    host1 = network.Host(1) #formerly client
    object_L.append(host1)
    host2 = network.Host(2) #formerly server
    object_L.append(host2)
    #host3 = network.Host(3)
    #object_L.append(host3)

    #first topology
    #create routers and routing tables for connected clients (subnets)
    router_a_rt_tbl_D = {1: {0: 1}}#,{2: {2: 2}} # packet to host 1 through interface 0 for cost 1
    #router_a_rt_tbl_D[2] = {1: 4}
    #y = router_a_rt_tbl_D[2][1].
    print(router_a_rt_tbl_D)
    #int length = router_a_rt_tbl_D.
    print(router_a_rt_tbl_D[1])
    router_a = network.Router(name='A', 
                              intf_cost_L=[1,1], 
                              rt_tbl_D = router_a_rt_tbl_D, 
                              max_queue_size=router_queue_size)
    object_L.append(router_a)
    router_b_rt_tbl_D = {2: {1: 3}} # packet to host 2 through interface 1 for cost 3
    router_b = network.Router(name='B', 
                              intf_cost_L=[1,3], 
                              rt_tbl_D = router_b_rt_tbl_D, 
                              max_queue_size=router_queue_size)
    object_L.append(router_b)

    """
    #create routers and routing tables for connected clients (subnets)
    router_a_rt_tbl_D = {1: {0: 1}}, {2: {1: 4} # packet to host 1 through interface 0 for cost 1
    router_a = network.Router(name='A',
                              intf_cost_L=[1,1],
                              rt_tbl_D = router_a_rt_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_a)
    router_b_rt_tbl_D = None
    router_b = network.Router(name='B',
                              intf_cost_L=[1,3],
                              rt_tbl_D = router_b_rt_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_b)
    #create routers and routing tables for connected clients (subnets)
    router_c_rt_tbl_D = None#{1: {0: 1}} # packet to host 1 through interface 0 for cost 1
    router_c = network.Router(name='C',
                              intf_cost_L=[1,1],
                              rt_tbl_D = router_a_rt_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_c)
    router_d_rt_tbl_D = {2: {1: 3}} # packet to host 2 through interface 1 for cost 3
    router_d = network.Router(name='D',
                              intf_cost_L=[1,3],
                              rt_tbl_D = router_b_rt_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_d)
    #"""
    
    #create a Link Layer to keep track of links between network nodes
    link_layer = link.LinkLayer()
    object_L.append(link_layer)


    ## creates a link between two objects by looking up and linking node interfaces.
    # @param node_1: node from which data will be transfered
    # @param node_1_intf: number of the interface on that node
    # @param node_2: node to which data will be transfered
    # @param node_2_intf: number of the interface on that node
    # def __init__(self, node_1, node_1_intf, node_2, node_2_intf):
    # add all the links
    #"""
    # The first router topology
    link_layer.add_link(link.Link(host1, 0, router_a, 0))
    link_layer.add_link(link.Link(router_a, 1, router_b, 0))
    link_layer.add_link(link.Link(router_b, 1, host2, 0))


    """
    #The second router topology
    #router_a and associated links
    link_layer.add_link(link.Link(router_a, 0, host1, 0))
    link_layer.add_link(link.Link(router_a, 1, host2, 0))
    link_layer.add_link(link.Link(router_a, 2, router_b, 0))
    link_layer.add_link(link.Link(router_a, 3, router_c, 0))
    #router_d and associated links
    link_layer.add_link(link.Link(router_d, 0, router_b, 1))
    link_layer.add_link(link.Link(router_d, 1, router_c, 1))
    link_layer.add_link(link.Link(router_d, 2, host3, 0))
    #"""

    
    #start all the objects
    thread_L = []
    for obj in object_L:
        thread_L.append(threading.Thread(name=obj.__str__(), target=obj.run)) 
    
    for t in thread_L:
        t.start()
    
    #send out routing information from router A to router B interface 0
    router_a.send_routes(1)
    
    #create some send events    
    for i in range(1):
        host1.udt_send(2, 'Sample client data %d' % i)
        
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)
    
    #print the final routing tables
    for obj in object_L:
        if str(type(obj)) == "<class 'network.Router'>":
            obj.print_routes()
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically
