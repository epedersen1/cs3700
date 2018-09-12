import argparse

parser = argparse.ArgumentParser("")
parser.add_argument("hostname")
parser.add_argument("neuid", type=int)
parser.add_argument("-p", dest='port', type=int, nargs='?')
parser.add_argument("-s", dest='encrypted', action='store_true')
args = parser.parse_args()

hostname = args.hostname
neuid = args.neuid
encrypted = args.encrypted
port = args.port if args.port else 27993

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((hostname, port))

