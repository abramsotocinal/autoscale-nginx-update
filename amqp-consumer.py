import pika
from time import sleep
import os
import json
import re

#Globals
mqserver = '192.168.0.79'
mqchan = ''
mqueue = 'Test'

#path of nginx config
fname='nginx.conf'
#write out to temp config; eventually change to open config file as read write
wout='new.conf'

ipregex = '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\.'\
    '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}|0)\.'\
    '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}|0)\.'\
    '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}|0)'\

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
    # RabbitMQ server
    mqserver = '192.168.0.79'
    # Queue name
    mqueue = 'Test'
    mqroutekey = mqueue

    mqconn = mqconnect(mqserver)
    mqchan = declarechannel(mqconn, mqueue)

    mqchan.basic_consume(callback, queue=mqueue, no_ack=True)
    print 'Waiting for messages'
    mqchan.start_consuming()
    mqconn.close()

if __name__ == '__main__':
    main()