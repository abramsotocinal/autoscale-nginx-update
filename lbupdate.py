from time import sleep
from sys import exit
import os
import json
import re
from includes import Autoscale

try:
    import pika
except ImportError:
    print 'Cannot load pika module. Please make sure you have it installed and is accessible'
    exit(1)


#path of nginx config
fname='nginx.conf'
#write out to temp config; eventually change to open config file as read write
wout='new.conf'


ipregex = '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\.'\
    '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}|0)\.'\
    '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}|0)\.'\
    '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}|0)'\

# Class for parsing (for now) the application config file(conf.yml)
# DON'T FULLY IMPLEMENT YET. NOT YET SURE WHERE I'M GOING WITH THIS
class getconf:

    mqserver = ''
    mqueue = ''

    def __init__(self, type, conffile='conf.yml'):
        try:
            with open(conffile,'r') as stream:
                ##try:
                from yaml import load
                conf = load(stream)
                if type == 'consumer':
                    tmpdict = conf['node']['type'][1]['consumer']
                    self.mqueue = tmpdict['mqueue']
                    self.mqserver = tmpdict['mqserver']
                    self.confpath = tmpdict['confpath']
                    self.confname = tmpdict['confname']
                elif type == 'agent':
                    tmpdict = conf['node']['type'][0]['consumer']
                    self.mqueue = tmpdict['mqueue']
                    self.mqserver = tmpdict['mqserver']

                ##except ImportError:
                    ##print ' Unable to import module! Make sure YAML module is installed'
        except Exception as e:
            print 'Cannot access file %s! Make sure file exists in the \
            same directory and has correct permissions' % conffile
            print str(e)

# add instances to upstream directive, open config, output to new file, accept IPs as list
def appendinstance(fname,wout,asinstances):
    writeout = False
    #Open both files, storing data in fin, writing to fout
    with open(fname, 'r') as fin, open(wout, 'w') as fout:
        for line in fin.readlines():
            # ADD NEW INSTANCES HERE, IN BETWEEN ANCHORS #IPSTART AND #IPEND
            if re.match('\#IPSTART',line.strip()):
                writeout = True
                fout.write(line)
            elif re.match('\#IPEND',line.strip()):
                writeout = False
                fout.write(line)
            elif writeout:
                fout.write('%s\tserver %s;\n' % (line, asinstances))
                writeout = False
            else:
                fout.write(line)

def terminateinstance(fname,wout,terminst):
    writeout=False
    inst = re.compile(ipregex)
    with open(fname, 'r') as fin, open(wout, 'w') as fout:
        lines = fin.readlines()
        for line in lines:
            if re.match('\#IPSTART', line.strip()):
                fout.write(line)
                writeout = True
            elif re.match('\#IPEND', line.strip()):
                fout.write(line)
                writeout = False
            elif writeout:
                #if line contains IP in list of terminable instances, don't write to file, and remove from list
                #otherwise, write out to file
                if inst.search(line.strip()).group() in terminst:
                    print 'instance removed'
                    terminst.remove(inst.search(line.strip()).group())
                else:
                    fout.write(line)
            else:
                fout.write(line)

# Connect to RabbitMQ server AS A FUNCTION, return pika object, implement for final product
def mqconnect(mqserver):
    while True:
        try:
            mqconn = pika.BlockingConnection(pika.ConnectionParameters(host=mqserver))
            return mqconn
            # break
        except pika.exceptions.AMQPConnectionError:
            print 'Can\'t connect to %s' % mqserver
            print 'Retrying in 5 seconds'
            sleep(5)

# Channel declare AS FUNCTION
def declarechannel(mqconn, mqueue):
    while True:
        try:
            mqchan = mqconn.channel()
            mqchan.queue_declare(queue=mqueue)
            return mqchan
            # break
        except pika.exceptions.AMQPChannelError:
            print 'Channel error: %s \n' % pika.exceptions.AMQPChannelError
            print 'Retrying in 5 seconds'
            sleep(5)


# Pika Callback function. Do all stuff here
def callback(ch, method, properties, body):
    print ' Received: %r' % body
    msg = json.loads(body)
    asinstances = msg['IP'].encode("ascii","replace")

    print asinstances

    if msg['Action'] == 'Launch':
        appendinstance(fname, wout, asinstances)
    elif msg['Action'] == 'Terminate':
        terminateinstance(fname, wout, asinstances)

    os.remove(fname)
    os.rename(wout,fname)

    #Reload config
    #os.popen('nginx reload')

def main():

    conf = getconf('consumer','conf.yml')

    # RabbitMQ server
    mqserver = conf.mqserver
    # Queue name
    mqueue = conf.mqueue
    mqroutekey = mqueue

    mqconn = mqconnect(mqserver)
    mqchan = declarechannel(mqconn, mqueue)

    mqchan.basic_consume(callback, queue=mqueue, no_ack=True)
    print 'Waiting for messages'
    mqchan.start_consuming()
    mqconn.close()

def new_main():

    asconnect = Autoscale('service')

    conn = asconnect.mqconnect()

    chan = asconnect.declarechannel(conn)

    chan.basic_consume(callback,asconnect.mqueue,no_ack=True)

    print 'Waiting for messages'

    chan.start_consuming()

    conn.close()

if __name__ == '__main__':

    new_main()