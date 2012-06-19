'''
Created on Jan 4, 2012

@author: penteado
'''

import socket
import re
import time
import array

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class SocketError(Error):
    """Exception raised for errors in the socket.

    Attributes:
        expr -- input expression in which the error occurred
        msg  -- explanation of the error
    """

    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg
        print expr
        print msg
        
class MaxTries(Error):
    """Exception raised for errors in the socket.

    Attributes:
        expr -- input expression in which the error occurred
        msg  -- explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg
        print 'max_tries was reached without the expected answer for the message. Last answer was\n'+str(msg)

from threading import Thread
    


class Receiver(Thread):
    def __init__(self,tpl2):
        self.tpl2=tpl2
        self.keeplistening=True
        Thread.__init__(self)
    def run(self):
        print 'Starting to listen on socket '+str(self.tpl2.sock)
        while True:
            buf=self.tpl2.recv(quiet=True)
            if not self.keeplistening:
                break

class TPL2(object):
    '''
    classdocs
    '''
    

    buffersize=1024


    def __init__(self,host='localhost',port=65442,user='',password='',bufsize=buffersize,max_tries=10,verbose=True,
                 timeout=2,echo=True,debug=False):
        '''
        Constructor
        '''

        self.bufsize=bufsize
        self.host=host
        self.port=port
        self.user=user
        self.password=password
        self.max_tries=max_tries
        self.log=[]
        self.sent=[]
        self.received=[]
        self.verbose=verbose
        self.next_command_id=1
        self.commands_sent={0:{'sent':None,'status':None,'received':[],'events':[],type:None,'allstatus':[],'ok':False,'complete':False}}
        self.receiver=None
        self.timeout=timeout
        self.received_objects={}
        self.echo=echo
        self.debug=debug
        self.sleep=0.5
        self.events=[]
        


        #Open the socket
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.connect((host,port))
        self.sock.settimeout(self.timeout)
        s=self.expect('TPL2\s+(?P<TPL2>\S+)\s+CONN\s+(?P<CONN>\d+)\s+AUTH\s+(?P<AUTH>\S+(,\S+)*)')
        if not s:
            self.sock.close()
            raise SocketError('self.sock.connect(('+self.host+str(self.port)+')','Got None as answer.')
        self.protocol_version,self.conn,self.auth_methods=s.group('TPL2'),s.group('CONN'),s.group('AUTH')     
        self.send('AUTH PLAIN "'+user+'" "'+password+'"\r\n')
        s=self.expect('AUTH\s+((?P<OK>OK)|(?P<FAILED>FAILED)|(?P<ERROR>ERROR)'
                    '|(?P<USUPPORTED>UNSUPPORTED)|(?P<DISABLED>DISABLED))(\s+(?P<read_level>\d))?(\s+(?P<write_level>\d))?')
        try:
            last=s.string
        except:
            last=s
        if (not s) or (not s.group('OK')):
            self.sock.close()
            print 'self.sock.recv()','Not authorized; Last answer from server was'+last
            raise SocketError('self.sock.recv()','Not authorized; Last answer from server was'+last)
        self.read_level,self.write_level=int(s.group('read_level')),int(s.group('write_level'))
        self.listen()


    def listen(self):
        if (not self.receiver) or (not self.receiver.isAlive()):
            self.receiver=Receiver(self)
            self.receiver.daemon=True
            self.receiver.start()
    
    def stoplistening(self):
        if self.isListening():
            self.receiver.keeplistening=False
            self.receiver.join(float(self.timeout+0.5))
            
    def isListening(self):
        return (self.receiver) and (self.receiver.isAlive())
                               
    def disconnect(self):
        print "Disconnecting from ",self.host,':',self.port
        self.stoplistening()
        self.send('DISCONNECT')
#        try:
#            s=self.expect('DISCONNECT\s+OK')
#        except MaxTries:
#            pass
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        
    def __del__(self):
        self.disconnect()

        
    def recv(self,bufsize=buffersize,quiet=False):
        try:
            buf=self.sock.recv(bufsize)
        except socket.timeout:
            if (not quiet):
                print "recv() timed out"
            buf=None
        if self.verbose and self.echo and buf:
            print buf
        if buf:
            self.log.append(('r',buf))
            self.received.append((len(self.log),buf))
            self.parseAnswer(buf)
        return buf
    
    def parseAnswer(self,buf):
        
        id=None
        
        s=re.search('(?P<id>\d+)\s+COMMAND\s+(?P<status>(OK)|(ERROR UNAUTHENTICATED)|(ERROR IDBUSY (?P<bcmdid>\d+))'
                    '|(ERROR IDRANGE (?P<rcmdid>\d+))|(ERROR SYNTAX)|(ERROR TOOMANY)|(ERROR TOOLONG)|'
                    '(ERROR DENIED)|(ERROR NOTRUNNING)|(ERROR UNKNOWN))(\s+(?P<message>\S+.*))?',buf)
        if s:
            d=s.groupdict()
            id=int(d['id'])
            if d['bcmdid']:
                id=int(d['cmdid'])
            if d['rcmdid']:
                id=int(d['rmdid'])
            self.commands_sent[id]['status']=d['status']
            self.commands_sent[id]['allstatus'].append(d['status'])
            self.commands_sent[id]['ok']=(d['status']=='OK')
                    
        s=re.search('(?P<id>\d+)\s+(?P<data>DATA INLINE) (?P<object>\S+.*?)=(?P<value>\S+.*?)\r?\n?',buf)
        if s:
            id=int(s.group('id'))
            self.commands_sent[id]['data']=True
            value=s.group('value')
            s=re.search('"(.*)"',value)
            if s:
                value=s.group(1)
            obj=self.commands_sent[id]['object']
            self.received_objects[obj]=value
            if self.verbose:
                print buf
        
        s=re.search('(?P<id>\d+)\s+(?P<data>DATA BINARY) (?P<object>\S+.*?):(?P<bytes>\S+.*?)\r?\n?',buf)
        if s:
            id=int(s.group('id'))
            self.commands_sent[id]['data']=True
            bytes=int(s.group('bytes'))
            obj=self.commands_sent[id]['object']
            if self.verbose:
                print buf
            buffer=self.sock.recv(bytes)
            arr=array('B')
            self.received_objects[obj]=arr.fromstring(buffer)
            
        s=re.search('(?P<id>\d+)\s+COMMAND\s+(?P<status>(COMPLETE)|(ABORTED BY (?P<cmdid>\d+))'
                    '|(FAILED))(\s+(?P<message>\S+.*))?',buf)
        if s:
            id=int(s.group('id'))
            self.commands_sent[id]['status']=s.group('status')
            self.commands_sent[id]['allstatus'].append(s.group('status'))
            self.commands_sent[id]['complete']=(s.group('status')=='COMPLETE')

            
        s=re.search('(?P<id>\d+)\s+DATA (?P<ok>OK|ERROR)(\s+(?P<object>\S+.*?))\s+(?P<error>(BUSY)|(DENIED)'
                    '|(DIMENSION)|(RANGE)|(INVALID)|(TYPE)|(UNKNOWN)|(FAILED(\s+\S+.*?)?)|(LOCKEDBY(\s+\d+)?)|(AUTHFAIL)|(ABORTED)|(CONNFAIL(\s+\S+.*?)?))?',buf)
        if s:
            id=int(s.group('id'))
            status=s.group('ok') if s.group('ok')=='OK' else s.group('ok')+' '+str(s.group('error'))
            self.commands_sent[id]['status']=status
            self.commands_sent[id]['allstatus'].append(status)
            self.commands_sent[id]['data']=(s.group('ok')=='OK')
            
        s=re.search('(?P<id>\d+)\s+(?P<abortedby>ABORTED BY\s+(?P<cmdid>\d+))',buf)
        if s:
            id=int(s.group('id'))  
            self.commands_sent[id]['status']=s.group('abortedby')
            self.commands_sent[id]['allstatus'].append(s.group('abortedby'))
            
        s=re.search('(?P<id>\d+)\s+EVENT\s+(?P<type>\S.*?)\s+(?P<object>\S.*?):(?P<number>\d+)\s+(?P<description>\S+.*?)?',buf)
        if s:
            id=int(s.group('id'))
            if id in self.commands_sent:
                self.commands_sent[id]['events'].append(s.groupdict())
            self.events.append(s.groupdict())
        
        if id in self.commands_sent:
            self.commands_sent[id]['received'].append(buf)
            

    def succeeded(self,cmdid):
        ret=cmdid in self.commands_sent
        if ret:
            ret=self.commands_sent[cmdid]['complete']
        if ret:
            if 'data' in self.commands_sent[cmdid]:
                ret=self.commands_sent[cmdid]['data']
        return ret 
                    
            
    def getobject(self,object):
        ocmid=self.get(object+'!TYPE',wait=True)
        st=self.commands_sent[ocmid]['status']
        if st!='COMPLETE':
            print st 
            return None
        ocmid=self.get(object,wait=True)
        st=self.commands_sent[ocmid]['status']
        if st!='COMPLETE':
            print st 
            return None
        if self.debug:
            print self.received_objects
        if self.received_objects[object+'!TYPE']=='0':
            self.received_objects[object]=None
        elif self.received_objects[object+'!TYPE']=='1':
            self.received_objects[object]=int(self.received_objects[object])
        elif self.received_objects[object+'!TYPE']=='2':
            self.received_objects[object]=float(self.received_objects[object])
        elif self.received_objects[object+'!TYPE']=='3':
            self.received_objects[object]=str(self.received_objects[object])
        else:
             self.received_objects[object]=None
        return self.received_objects[object]

            
        
    def send(self,message='\r\n'):
        if self.verbose:
            print message
        self.sock.send(message)
        self.log.append(('s',message))
        self.sent.append((len(self.log),message))
        
    def expect(self,message='\r\n'):
        res=''
        for i in range(self.max_tries):
            res+=str(self.recv())
            if res:
                s=re.search(message,res)
            else:
                s=None
            if s:
                break
        if (not s):
            raise MaxTries(res)
        if s:
            return s
        else:
            return res
    
    def sendcomm(self,comm,object,wait=False):
        ocmid=self.next_command_id
        command=str(ocmid)+' '+comm+' '+object+'\r\n'
        self.send(command)
        self.commands_sent[ocmid]={'sent':command,'status':'sent','received':[],'comm':comm,'object':object,'events':[],'allstatus':[],'ok':False,'complete':False}
        if comm in ('GET','SET'):
            self.commands_sent[ocmid]['data']=False
        self.next_command_id+=1
        if wait:
            while self.commands_sent[ocmid]['status']=='sent':
                if self.debug:
                    print 'Waiting for command completion'
                time.sleep(self.sleep)
        return ocmid
        
    def get(self,object,wait=False):
        ret=self.sendcomm('GET',object,wait)
        if wait:
            while not self.commands_sent[ret]['data']:
                if self.debug:
                    print 'Waiting for command completion'
                time.sleep(self.sleep)
        return ret
    
    def set(self,object,value,wait=False,binary=False):
        if not binary:
            obj=object+'='+str(value)
            cmid=self.sendcomm('SET',obj,wait)
        else:
            obj=object+':',len(value)
            cmid=self.sendcomm('SET',obj,wait)
            self.sock.send(value.tostring())
        if wait:
            while not (self.commands_sent[cmid]['status'].split())[0] in ('OK','COMPLETE','ABORTED'):
                if self.debug:
                    print 'Waiting for command completion'
                time.sleep(self.sleep)
        return cmid
         
    def abort(self,commandid,wait=False):
        return self.sendcomm('ABORT',commandid,wait)
         


        

#bufsize=1024
#HOST,PORT="sim.tt-data.eu",65442 #85.214.112.166
#AUTH='AUTH PLAIN "admin" "a8zfuoad1"\r\n'
#
#sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#sock.connect((HOST,PORT))
#print sock.recv(bufsize)
#print AUTH
#sock.send(AUTH)
#print sock.recv(bufsize)
#print '1 GET SERVER.INFO.DEVICE\r\n'
#sock.send('1 GET SERVER.INFO.DEVICE\r\n')
#print sock.recv(bufsize)
#print 'DISCONNECT'
#sock.send('DISCONNECT')
#print sock.recv(bufsize)
#sock.close()
#

        
if __name__ == "__main__":
    print "Ruuning TPL2.py's main"
    t=TPL2(user='admin',password='a8zfuoad1',host='sim.tt-data.eu',port=65442,echo=False)
    t
    t.get('SERVER.INFO.DEVICE')
    t.received_objects
    print t.getobject('SERVER.UPTIME')
    t
    
    



