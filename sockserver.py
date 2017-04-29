import socket
import select
import threading
local_host = '127.0.0.1'
local_port = 8080


def new_client(client):
	 	 	
	b = client.recv(1)
	if ord(b) != 5:
		print "Error. not Socks 5 protocol"
		return
	l = ord(client.recv(1))
	buff = client.recv(l)
	if len(buff) < l:
		print "bad size"
		return
	success = 0
	byte = ord(buff[0])
	if byte == 0:
		client.send("\x05\x00")
		success+=1
	else:
		print "Bad option. Auth not supported"
		return
	buff = client.recv(3)
	if buff[0] == "\x05" and buff[2] == "\x00":
		#option 1
		host, raw_host = get_host(client)
		if host == "":
			print "Unable to get host..."
			return
		port, raw_port = get_port(client)
		command = ord(buff[1])
		reply = "\x05\x00\x00" + raw_host+raw_port
		client.send(reply)
		socks_do(command, client, host, port)
	else:
		client.send("\x05\xFF")

	client.close()

def socks_do(command, client, host, port):
	print "Openning connection for %s:%s" % (host, port)
	print "Command: %s" % command
	if command == 1:
		socks_connect(client, host, port)
	elif command == 2:
		socks_bind(client, host, port)
	elif command == 3:
		socks_udp(client, host, port)
	else:
		return 0

def socks_connect(client, host, port):
	print "Connect required!"
	target = socket.socket()
	try:
		target.connect((host, port))
	except Exception as ex:
		print "Connection Error"
		print ex
		print type(ex)
	closed = False
	while not closed:
		tbuffer = ""
		cbuffer = ""
		reads, writes, errs = select.select([client, target],[],[client, target], 120)
		if reads == [] and errs == []:
			print "Nothing."
			return
		if client in reads or client in errs:
			tbuffer = client.recv(1024)
		if target in reads or target in errs:
			cbuffer = target.recv(1024)
		
		while len(tbuffer) > 0:
			c = target.send(tbuffer)
			if c > 0: 
				tbuffer = tbuffer[c:]
			else:
				return
		while len(cbuffer) > 0:
			c = client.send(cbuffer)
			if c > 0:
				cbuffer = cbuffer[c:]
			else:
				return

def get_host(client):
	raw = ""
	host = ""
	rawflag = ""
	rawflag = client.recv(1)
	flag = ord(rawflag)
	if flag == 1:
		print "ipv4 used"
		raw = client.recv(4)
		host = ".".join(map(lambda x: str(ord(x)), raw))
	elif flag == 3:
		print "name used"
		size = ord(client.recv(1))
		raw = client.recv(size)
		host = raw
	elif flag==4:
		print "IPV6 not supported"
	return (host, rawflag+raw)

def get_port(client):
	portstr = client.recv(2)
	return (((ord(portstr[0])<<8) | ord(portstr[1])), portstr)

sock = socket.socket()
sock.bind((local_host, local_port))
sock.listen(10000)

while True:
	a = sock.accept()
	t = threading.Thread(target=new_client, args=(a[0],))
	t.start()