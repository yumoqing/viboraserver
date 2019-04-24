# wrap sock with ssl

import socket
import ssl

def openSslSock(host,port,cert,key):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
	sock.bind((host,port))
	sock.listen(5)
	context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
	context.load_cert_chain(cert,key)
	ssock = context.wrap_socket(sock,server_side=True)
	return ssock
