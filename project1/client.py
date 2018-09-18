import argparse
import socket

MAX_MSG_LEN = 8192

parser = argparse.ArgumentParser("")
parser.add_argument("hostname")
parser.add_argument("neuid")
parser.add_argument("-p", dest='port', type=int, nargs='?')
parser.add_argument("-s", dest='encrypted', action='store_true')
args = parser.parse_args()

hostname = args.hostname
neuid = args.neuid
encrypted = args.encrypted
port = args.port if args.port else 27993

secret_flag = ""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((hostname, port))
message = b"cs3700fall2018 HELLO {}\n".format(neuid)
s.send(message)
msg = ""
while(True):
	data = s.recv(MAX_MSG_LEN)
	if data[-1] != "\n":
		msg += data
		continue
	msg += data
	msg_type = msg.split()[1]
	if msg_type == "BYE":
		secret_flag = msg.split()[2]
		break
	key = msg.split()[2]
	rand_str = msg.split()[3]
	count = rand_str.count(key)
	count_msg = b"cs3700fall2018 COUNT {}\n".format(count)
	s.send(count_msg)
	msg = ""

print(secret_flag)
s.close()
