#! /usr/bin/env python
#coding=utf-8
import thread
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import ServerProxy
from Tkinter import *

wnd = Tk()
wnd.lab = Label(wnd, text="Client")
wnd.ent = Entry(wnd)
wnd.btn = Button(wnd, text="Send")
wnd.lab.pack()
wnd.ent.pack(side=LEFT)
wnd.btn.pack(side=LEFT)

my_server   = SimpleXMLRPCServer( ("localhost", 48001) )
your_server = ServerProxy("http://localhost:48002")

def msg(s):
  wnd.lab.config(text=s)
  return True
def run_server():
  my_server.register_function(msg)
  my_server.serve_forever()
def send():
  msg = wnd.ent.get()
  wnd.ent.select_range(0, len(msg))
  your_server.msg(msg)  
wnd.btn.config(command=send)
thread.start_new_thread( run_server, () )
wnd.mainloop()
