#!/usr/bin/env python -u

import argparse, socket, time, json, select, struct, math

DEBUG = True
#DEBUG = False

parser = argparse.ArgumentParser(description='route packets')
parser.add_argument('networks', metavar='networks', type=str, nargs='+', help="networks")
args = parser.parse_args()

##########################################################################################

# Message Fields
TYPE = "type"
SRCE = "src"
DEST = "dst"
MESG = "msg"
TABL = "table"

# Message Types
DATA = "data"
DUMP = "dump"
UPDT = "update"
RVKE = "revoke"
NRTE = "no route"

# Update Message Fields
NTWK = "network"
NMSK = "netmask"
ORIG = "origin"
LPRF = "localpref"
APTH = "ASPath"
SORG = "selfOrigin"

# internal route info
CUST = "cust"
PEER = "peer"
PROV = "prov"


##########################################################################################

class Router:

    routes = None
    updates = None
    relations = None
    sockets = None

    def __init__(self, networks):
        self.routes = []
        self.updates = []
        self.relations = {}
        self.sockets = {}
        for relationship in networks:
            network, relation = relationship.split("-")
            if DEBUG: 
                print "Starting socket for", network, relation
            self.sockets[network] = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            self.sockets[network].setblocking(0)
            self.sockets[network].connect(network)
            self.relations[network] = relation
        return

    def does_match(self, daddr, prefix, mask):
        prefix_parts = [int(x) for x in prefix.split('.')]
        daddr_parts = [int(x) for x in daddr.split('.')]
        mask_parts = [int(x) for x in mask.split('.')]
        p = [prefix_parts[i] & mask_parts[i] for i in range(4)]
        d = [daddr_parts[i] & mask_parts[i] for i in range(4)]
        return d[0]==p[0] and d[1]==p[1] and d[2]==p[2] and d[3]==p[3]

    def lookup_routes(self, daddr):
        """ Lookup all valid routes for an address """
        # TODO
        outroutes = []
        for route in self.routes:
            if self.does_match(daddr, route[NTWK], route[NMSK]):
                outroutes.append(route)
        #print(outroutes)
        return outroutes

    def get_shortest_as_path(self, routes):
        """ select the route with the shortest AS Path """
        # TODO
        outroutes = []
        min_path = 99999
        for route in routes:
            if route[APTH] < min_path:
                outroutes = [route]
                min_path = route[APTH]
            elif route[APTH] == min_path:
                outroutes.append(route)
        return outroutes
            
    def get_highest_preference(self, routes):
        """ select the route with the shortest AS Path """
        # TODO
        outroutes = []
        max_pref = -1
        for route in routes:
            if route[LPRF] > max_pref:
                outroutes = [route]
                max_pref = route[LPRF]
            elif route[LPRF] == max_pref:
                outroutes.append(route)
        return outroutes
         
    def get_self_origin(self, routes):
        """ select self originating routes """
        # TODO
        outroutes = []
        for route in routes:
            if route[SORG]:
                outroutes.append(route)
        return outroutes if len(outroutes) > 0 else routes

    def get_origin_routes(self, routes):
        """ select origin routes: EGP > IGP > UNK """
        # TODO
        outroutes = []
        max_orig = -1
        for route in routes:
            if route[ORIG] > max_orig:
                outroutes = [route]
                max_orig = route[ORIG]
            elif route[ORIG] == max_orig:
                outroutes.append(route)
        return outroutes

    def is_lower_ip(self, ip1, ip2):
        ip1 = map(int, ip1.split("."))
        ip2 = map(int, ip2.split("."))
        for i in range(4):
            if ip1[i] > ip2[i]:
                return False
        return True

    def get_lowest_ip(self, routes):
        outroutes = []
        min_ip = "256.256.256.256"
        for route in routes:
            if self.is_lower_ip(route[NTWK], min_ip):
                outroutes = [route]
                min_ip = route[NTWK]
        return outroutes

    def filter_relationships(self, srcif, routes):
        """ Don't allow Peer->Peer, Peer->Prov, or Prov->Peer forwards """
        outroutes = []
        return routes

    def get_route(self, srcif, daddr):
        """	Select the best route for a given address	"""
        # TODO
        peer = None
        routes = self.lookup_routes(daddr)
        # Rules go here
        if routes:
            # 1. Highest Preference
            routes = self.get_highest_preference(routes)
            # 2. Self Origin
            routes = self.get_self_origin(routes)
            # 3. Shortest ASPath
            routes = self.get_shortest_as_path(routes)
            # 4. EGP > IGP > UNK
            routes = self.get_origin_routes(routes)
            # 5. Lowest IP Address
            # TODO
            routes = self.get_lowest_ip(routes)
            # Final check: enforce peering relationships
            routes = self.filter_relationships(srcif, routes)
        return routes[0] if len(routes) > 0 else None

    def forward(self, srcif, packet):
        """	Forward a data packet	"""
        # TODO
        route = self.get_route(srcif, packet[DEST])
        self.sockets[route['nextHop']].send(json.dumps(packet).encode('utf-8'))
        return True

    def coalesce(self):
        """	coalesce any routes that are right next to each other	"""
        # TODO (this is the most difficult task, save until last)
        return False

    def update(self, srcif, packet):
        """	handle update packets	"""
        # TODO
        self.updates.append(packet)
        route = {}
        route[NTWK] = packet[MESG][NTWK]
        route[NMSK] = packet[MESG][NMSK]
        route[LPRF] = int(packet[MESG][LPRF])
        route[SORG] = True if packet[MESG][SORG] == 'True' else False
        route[APTH] = len(packet[MESG][APTH])
        if packet[MESG][ORIG] == 'IGP':
            route[ORIG] = 2
        elif packet[MESG][ORIG] == 'EGP':
            route[ORIG] = 1
        else:
            route[ORIG] = 0
        route['nextHop'] = srcif
        self.routes.append(route)
        for neighbor in self.sockets:
            if neighbor != srcif:
                self.send_message(packet[DEST], neighbor, UPDT, packet[MESG])
        return True
    
    def revoke(self, packet):
        """	handle revoke packets	"""
        # TODO
        return True

    def dump(self, packet):
        """	handles dump table requests	"""
        # TODO
        msg = []
        for route in self.routes:
            msg.append({'network':route[NTWK], 'netmask':route[NMSK], 'peer':route['nextHop']})
        self.send_message(packet[DEST], packet[SRCE], 'table', msg)
        return True

    def handle_packet(self, srcif, packet):
        """	dispatches a packet """
        if packet[TYPE] == UPDT:
			return self.update(srcif, packet)
        if packet[TYPE] == DATA:
            return self.forward(srcif, packet)
        if packet[TYPE] == DUMP:
            return self.dump(packet)
        return False

    def send_error(self, conn, msg):
        """ Send a no_route error message """
        # TODO
        return

    def send_message(self, src, dst, typ, msg):
        packet = {}
        packet[SRCE] = src
        packet[DEST] = dst
        packet[TYPE] = typ
        packet[MESG] = msg
        self.sockets[dst].send(json.dumps(packet).encode('utf-8'))

    def run(self):
        while True:
            socks = select.select(self.sockets.values(), [], [], 0.1)[0]
            for conn in socks:
                try:
                    k = conn.recv(65535)
                except:
                    # either died on a connection reset, or was SIGTERM's by parent
                    return
                if k:
                    for sock in self.sockets:
                        if self.sockets[sock] == conn:
                            srcif = sock
                    msg = json.loads(k)
                    if not self.handle_packet(srcif, msg):
                        self.send_error(conn, msg)
                else:
                    return
        return

if __name__ == "__main__":
    router = Router(args.networks)
    router.run()
