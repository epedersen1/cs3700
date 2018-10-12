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
        self.myport = {}
        self.updates = []
        self.revokes = []
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

    def does_match(self, dest, prefix, mask):
        dest_num = self.ip2num(dest)
        prefix_num = self.ip2num(prefix)
        mask_num = self.ip2num(mask)
        return (dest_num & mask_num) == (prefix_num & mask_num)

    def lookup_routes(self, daddr):
        """ Lookup all valid routes for an address """
        outroutes = []
        for route in self.routes:
            if self.does_match(daddr, route[NTWK], route[NMSK]):
                outroutes.append(route)
        return outroutes

    def get_longest_prefix(self, routes):
        outroutes = []
        max_prefix = 0
        for route in routes:
            ipnum = self.ip2num(route[NMSK])
            if ipnum == max_prefix:
                outroutes.append(route)
            elif max_prefix < ipnum:
                outroutes = [route]
                max_prefix = ipnum
        return outroutes

    def get_shortest_as_path(self, routes):
        """ select the route with the shortest AS Path """
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
        outroutes = []
        for route in routes:
            if route[SORG]:
                outroutes.append(route)
        return outroutes if len(outroutes) > 0 else routes

    def get_origin_routes(self, routes):
        """ select origin routes: EGP > IGP > UNK """
        outroutes = []
        max_orig = -1
        for route in routes:
            if route[ORIG] > max_orig:
                outroutes = [route]
                max_orig = route[ORIG]
            elif route[ORIG] == max_orig:
                outroutes.append(route)
        return outroutes

    def ip2num(self, ip):
        ip = map(int, ip.split("."))
        return ip[0]*pow(2,24)+ip[1]*pow(2,16)+ip[2]*pow(2,8)+ip[3]

    def num2ip(self, num):
        ip = ""
        ip += str(num//pow(2,24)) + "."
        ip += str((num%pow(2,24))//pow(2,16)) + "."
        ip += str((num%pow(2,16))//pow(2,8)) + "."
        ip += str(num%pow(2,8))
        return ip

    def get_lowest_ip(self, routes):
        outroutes = []
        min_ip = self.ip2num("256.256.256.256")
        for route in routes:
            ipnum = self.ip2num(route[NTWK])
            if min_ip >= ipnum:
                outroutes = [route]
                min_ip = ipnum
        return outroutes

    def filter_relationships(self, srcif, routes):
        """ Don't allow Peer->Peer, Peer->Prov, or Prov->Peer forwards """
        outroutes = []
        return routes

    def get_route(self, srcif, daddr):
        """	Select the best route for a given address	"""
        peer = None
        routes = self.lookup_routes(daddr)
        # Rules go here
        if routes:
            routes = self.get_longest_prefix(routes)
            # 1. Highest Preference
            routes = self.get_highest_preference(routes)
            # 2. Self Origin
            routes = self.get_self_origin(routes)
            # 3. Shortest ASPath
            routes = self.get_shortest_as_path(routes)
            # 4. EGP > IGP > UNK
            routes = self.get_origin_routes(routes)
            # 5. Lowest IP Address
            routes = self.get_lowest_ip(routes)
            # Final check: enforce peering relationships
            routes = self.filter_relationships(srcif, routes)
        return routes[0] if len(routes) > 0 else None

    def forward(self, srcif, packet):
        """	Forward a data packet	"""
        route = self.get_route(srcif, packet[DEST])
        if route and (self.relations[srcif] == CUST or self.relations[route['nextHop']] == CUST):
            self.sockets[route['nextHop']].send(json.dumps(packet).encode('utf-8'))
        else:
            self.send_message(srcif, self.myport[srcif], packet[SRCE], "no route", {})
        return True

    def is_adj(self, r1, r2):
        if r1['nextHop'] != r2['nextHop'] or r1[ORIG] != r2[ORIG] or r1[LPRF] != r2[LPRF] or r1[SORG] != r2[SORG] or r1[APTH] != r2[APTH] or r1[NMSK] != r2[NMSK]:
            return False
        ip1 = self.ip2num(r1[NTWK])
        ip2 = self.ip2num(r2[NTWK])
        mask = self.ip2num(r1[NMSK])
        new_mask = mask & (mask-1)
        return ip1 & mask != ip2 & mask and ip1 & new_mask == ip2 & new_mask

    def coalesce(self, r1, r2):
        """	coalesce any routes that are right next to each other	"""
        route = {}
        nmsk = self.ip2num(r1[NMSK])
        new_nmsk = nmsk & (nmsk-1)
        route[NMSK] = self.num2ip(new_nmsk)
        route[NTWK] = self.num2ip(self.ip2num(r1[NTWK]) & new_nmsk)
        route[LPRF] = r1[LPRF]
        route[SORG] = r1[SORG]
        route[APTH] = r1[APTH]
        route[ORIG] = r1[ORIG]
        route['nextHop'] = r1['nextHop']
        return route

    def add_to_table(self, route):
        for r in self.routes:
            if self.is_adj(route, r):
                self.add_to_table(self.coalesce(route,r))
                self.routes.remove(r)
                return
        self.routes.append(route)


    def update(self, srcif, packet):
        """	handle update packets	"""
        self.updates.append(packet)
        self.myport[packet[SRCE]] = packet[DEST]
        route = {}
        route[NTWK] = packet[MESG][NTWK]
        route[NMSK] = packet[MESG][NMSK]
        route[LPRF] = int(packet[MESG][LPRF])
        route[SORG] = packet[MESG][SORG] == 'True'
        route[APTH] = len(packet[MESG][APTH])
        if packet[MESG][ORIG] == 'IGP':
            route[ORIG] = 2
        elif packet[MESG][ORIG] == 'EGP':
            route[ORIG] = 1
        else:
            route[ORIG] = 0
        route['nextHop'] = srcif
        self.add_to_table(route)
        for neighbor in self.sockets:
            if neighbor != srcif and (self.relations[srcif] == CUST or self.relations[neighbor] == CUST):
                self.send_message(neighbor, packet[DEST], neighbor, UPDT, packet[MESG])
        return True
    
    def revoke(self, packet):
        """	handle revoke packets	"""
        # TODO
        self.revokes.append(packet)
        for ip in packet[MESG]:
            self.routes = filter(lambda r: r[NTWK] != ip[NTWK] or r[NMSK] != ip[NMSK] or r['nextHop'] != packet[SRCE], self.routes)
        for neighbor in self.sockets:
            if neighbor != packet[SRCE] and (self.relations[packet[SRCE]] == CUST or self.relations[neighbor] == CUST):
                self.send_message(neighbor, packet[DEST], neighbor, RVKE, packet[MESG])
        return True

    def dump(self, packet):
        """	handles dump table requests	"""
        msg = []
        for route in self.routes:
            msg.append({'network':route[NTWK], 'netmask':route[NMSK], 'peer':route['nextHop']})
        self.send_message(packet[SRCE], packet[DEST], packet[SRCE], 'table', msg)
        return True

    def handle_packet(self, srcif, packet):
        """	dispatches a packet """
        if packet[TYPE] == UPDT:
			return self.update(srcif, packet)
        if packet[TYPE] == DATA:
            return self.forward(srcif, packet)
        if packet[TYPE] == DUMP:
            return self.dump(packet)
        if packet[TYPE] == RVKE:
            return self.revoke(packet)
        return False

    def send_message(self, sendto, src, dst, typ, msg):
        packet = {}
        packet[SRCE] = src
        packet[DEST] = dst
        packet[TYPE] = typ
        packet[MESG] = msg
        self.sockets[sendto].send(json.dumps(packet).encode('utf-8'))

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
