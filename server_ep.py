# -*- coding: utf-8 -*-
"""---endpoints server module---"""


from socket import *
from time import ctime
import sys
import const
import string
import threading
import time
import random
import re
from Queue import Queue
import serial
import struct 
import eut 
import refer_entry 
import usb.core
import usb.util
from server_endpoints_new import Server_Endpoints

PORT=8088
IP_ADDRESS = '127.0.0.1'

if __name__=='__main__':
	server = Server_Endpoints(host=IP_ADDRESS,port=PORT)
	try:
		server.start()
	except:
		pass


	
	
	
