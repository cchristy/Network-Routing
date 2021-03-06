'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import queue
import threading


## wrapper class for a queue of packets



class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    #  @param cost - of the interface used in routing
    def __init__(self, cost=0, maxsize=0):
        self.in_queue = queue.Queue(maxsize);
        self.out_queue = queue.Queue(maxsize);
        self.cost = cost
    
    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
#                 if pkt_S is not None:
#                     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
#                 if pkt_S is not None:
#                     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
#             print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
#             print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)
            
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths 
    dst_addr_S_length = 5
    src_addr_S_length = 5
    prot_S_length = 1 #protocal string
    
    ##@param dst_addr: address of the destination host
    # @param src_addr: address of the source host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst_addr, src_addr, prot_S, data_S):
        self.dst_addr = dst_addr
        self.src_addr = src_addr
        self.data_S = data_S
        self.prot_S = prot_S

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = (str(self.dst_addr) + str(self.src_addr)).zfill(self.dst_addr_S_length + self.src_addr_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += (self.data_S)
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0 : NetworkPacket.dst_addr_S_length])
        src_addr = (byte_S[NetworkPacket.dst_addr_S_length : NetworkPacket.dst_addr_S_length + NetworkPacket.src_addr_S_length])
        prot_S = byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.src_addr_S_length : NetworkPacket.dst_addr_S_length + NetworkPacket.src_addr_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        data_S = str(byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length : ])
        return self(dst_addr, src_addr, prot_S, data_S)
    

    

## Implements a network host for receiving and transmitting data
class Host:


    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
        src_addr = str(self.addr).zfill(5 - len(str(self.addr)));
        p = NetworkPacket(dst_addr, src_addr, 'data', data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out') #send packets always enqueued successfully
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router described in class

class Router:
    
    ##@param name: friendly router name for debugging
    # @param intf_cost_L: outgoing cost of interfaces (and interface number) 
    # @param rt_tbl_D: routing table dictionary (starting reachability), eg. {1: {1: 1}} # packet to host 1 through interface 1 for cost 1
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_cost_L, rt_tbl_D, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        #note the number of interfaces is set up by out_intf_cost_L
        self.intf_L = []
        for cost in intf_cost_L:
            self.intf_L.append(Interface(cost, max_queue_size))
        #set up the routing table for connected hosts
        self.rt_tbl_D = rt_tbl_D
        #router_List.append(self)

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and 
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p,i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))
            
    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the 
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is (i+1)%2
            self.intf_L[(i+1)%2].put(p.to_byte_S(), 'out', True)
            print('%s: forwarding packet "%s" from interface %d to %d' % (self, p, i, (i+1)%2))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass
        
    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    #  @param i interface that is sending routing information
    def update_routes(self, p, i):
        #TODO: add logic to update the routing tables and
        # possibly send out routing updates
        table = eval(p.data_S)
        flag = False;
        for host in table:
            for interface in table.get(host):
                if host in self.rt_tbl_D and not (self.rt_tbl_D[host] is None):
                    if interface in self.rt_tbl_D.get(host) and not (self.rt_tbl_D[host][interface] is None):
                        if int(self.rt_tbl_D[host][interface]) > int(table[host][interface]):
                            flag = True
                            self.rt_tbl_D[host][interface] =  {host: {i: int(table[host][interface])}}
                    else:
                        self.rt_tbl_D[host][interface] =  int(table[host][interface])
                        flag = True
                else:
                    self.rt_tbl_D[host] =  {i: int(table[host][interface])}
                    flag = True

        print('%s: Received routing update %s from interface %d' % (self, p, i))
        if (flag):
            self.send_routes(i)
        
    ## send out route update to nearby routers so they can update their tables
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        # a sample route update packet
        # p = NetworkPacket(0, 'control', 'Sample routing table packet')
        p = NetworkPacket(0, self.name, 'control', repr(self.rt_tbl_D))
        try:
            #TODO: add logic to send out a route update
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
            self.intf_L[i].put(p.to_byte_S(), 'out', True)
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass
        
    ## Print routing table
    def print_routes(self):
        print('%s: routing table' % self)
        #TODO: print the routes as a two dimensional table for easy inspection
        # Currently the function just prints the route table as a dictionary
        print(self.rt_tbl_D)
    #rename this back to print_routes when you get it working
    def print_route(self):
        print('%s: routing table' % self)
        #TODO: print the routes as a two dimensional table for easy inspection
        # Currently the function just prints the route table as a dictionary
        # Distance vector algorithm
        # {2: {1: 3}} # packet to host 2 through interface 1 for cost 3
        # column index, interface row index, cost
        i = 0
        j = 0
        print("**Row is host,Column is interface** \n\tCost to\n", end='\t'),
        for interface in range(len(self.rt_tbl_D)):
            j = j + 1
            print(j, end='\t')
            for interface in range(len(self.intf_L)):
                print('\n')
                for host in self.rt_tbl_D:
                    i = i + 1
                    print(i, end='\t'),
                    if interface in list(self.rt_tbl_D[host].keys()):
                        print(self.rt_tbl_D[host][interface], end='\t'),
                    else:
                        print("-", end='\t'),
        print("\n")
        
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 
