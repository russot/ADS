from socket import *
import const

HOST = 'localhost'
const.PORT = 20001
BUFSIZ = 1024
ADDR = (HOST,const.PORT)

tcpCliSock = socket(AF_INET,SOCK_STREAM)
tcpCliSock.connect(ADDR)

data = raw_input('>')
tcpCliSock.send(data)
while True:
	data = tcpCliSock.recv(BUFSIZ)
	if not data:
		continue
	print data

tcpCliSock.close()
