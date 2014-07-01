#coding=gb18030


import sys,threading,time;
import serial;
import binascii,encodings;
import re;
import socket;


class ReadThread:
def __init__(self, Output=None, Port=0, Log=None, i_FirstMethod=True):
self.l_serial = None;
self.alive = False;
self.waitEnd = None;
self.bFirstMethod = i_FirstMethod;
self.sendport = '';
self.log = Log;
self.output = Output;
self.port = Port;
self.re_num = None;


def waiting(self):
if not self.waitEnd is None:
self.waitEnd.wait();


def SetStopEvent(self):
if not self.waitEnd is None:
self.waitEnd.set();
self.alive = False;
self.stop();


def start(self):
self.l_serial = serial.Serial();
self.l_serial.port = self.port;
self.l_serial.baudrate = 9600;
self.l_serial.timeout = 2;


self.re_num = re.compile('\d');


try:
if not self.output is None:
self.output.WriteText(u'��ͨѶ�˿�\r\n');
if not self.log is None:
self.log.info(u'��ͨѶ�˿�');
self.l_serial.open();
except Exception, ex:
if self.l_serial.isOpen():
self.l_serial.close();


self.l_serial = None;


if not self.output is None:
self.output.WriteText(u'����\r\n %s\r\n' % ex);
if not self.log is None:
self.log.error(u'%s' % ex);
return False;


if self.l_serial.isOpen():
if not self.output is None:
self.output.WriteText(u'������������\r\n');
if not self.log is None:
self.log.info(u'������������');
self.waitEnd = threading.Event();
self.alive = True;
self.thread_read = None;
self.thread_read = threading.Thread(target=self.FirstReader);
self.thread_read.setDaemon(1);
self.thread_read.start();
return True;
else:
if not self.output is None:
self.output.WriteText(u'ͨѶ�˿�δ��\r\n');
if not self.log is None:
self.log.info(u'ͨѶ�˿�δ��');
return False;


def InitHead(self):
#���ڵ�������һЩ����
try:
time.sleep(3);
if not self.output is None:
self.output.WriteText(u'���ݽ�������ʼ��������\r\n');
if not self.log is None:
self.log.info(u'���ݽ�������ʼ��������');
self.l_serial.flushInput();
self.l_serial.write('\x11');
data1 = self.l_serial.read(1024);
except ValueError,ex:
if not self.output is None:
self.output.WriteText(u'����\r\n %s\r\n' % ex);
if not self.log is None:
self.log.error(u'%s' % ex);
self.SetStopEvent();
return;


if not self.output is None:
self.output.WriteText(u'��ʼ��������\r\n');
if not self.log is None:
self.log.info(u'��ʼ��������');
self.output.WriteText(u'===================================\r\n');


def SendData(self, i_msg):
lmsg = '';
isOK = False;
if isinstance(i_msg, unicode):
lmsg = i_msg.encode('gb18030');
else:
lmsg = i_msg;
try:
#�������ݵ���Ӧ�Ĵ������
pass
except Exception, ex:
pass;
return isOK;


def FirstReader(self):
data1 = '';
isQuanJiao = True;
isFirstMethod = True;
isEnd = True;
readCount = 0;
saveCount = 0;
RepPos = 0;
#read Head Infor content
self.InitHead();


while self.alive:
try:
data = '';
n = self.l_serial.inWaiting();
if n:
data = data + self.l_serial.read(n);
#print binascii.b2a_hex(data),


for l in xrange(len(data)):
if ord(data[l])==0x8E:
isQuanJiao = True;
continue;
if ord(data[l])==0x8F:
isQuanJiao = False;
continue;
if ord(data[l]) == 0x80 or ord(data[l]) == 0x00:
if len(data1)>10:
if not self.re_num.search(data1,1) is None:
saveCount = saveCount + 1;
if RepPos==0:
RepPos = self.output.GetInsertionPoint();
self.output.Remove(RepPos,self.output.GetLastPosition());


self.SendData(data1);
data1 = '';
continue;
except Exception, ex:
if not self.log is None:
self.log.error(u'%s' % ex);


self.waitEnd.set();
self.alive = False;


def stop(self):
self.alive = False;
self.thread_read.join();
if self.l_serial.isOpen():
self.l_serial.close();
if not self.output is None:
self.output.WriteText(u'�ر�ͨѸ�˿ڣ�[%d] \r\n' % self.port);
if not self.log is None:
self.log.info(u'�ر�ͨѸ�˿ڣ�[%d]' % self.port);


def printHex(self, s):
s1 = binascii.b2a_hex(s);
print s1;


#�����ò���
if __name__ == '__main__':
rt = ReadThread();
f = open("sendport.cfg", "r")
rt.sendport = f.read()
f.close()
try:
if rt.start():
rt.waiting();
rt.stop();
else:
pass;
except Exception,se:
print str(se);


if rt.alive:
rt.stop();


print 'End OK .';
del rt; 