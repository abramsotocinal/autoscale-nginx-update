from time import sleep
from yaml import load
import json
import os
import re

try:
    import pika
except ImportError as e:
    print 'Cannot load Pika module. Make sure it is installed or is accessible. '
    print 'Exiting...'
    exit(e)

# DON'T FULLY IMPLEMENT YET. NOT YET SURE WHERE I'M GOING WITH THIS
class Autoscale:
    mqserver = ''
    mqueue = ''
    # Create Autoscale obect, getting configuration from conf.yml in the same directory
    def __init__(self, type, conffile='conf.yml'):
        try:
            with open(conffile,'r') as stream:
                conf = load(stream)
                defs = conf['defaults']
                # Default/Common settings
                self.mqueue = defs['mqueue']
                self.mqserver = defs['mqserver']
                self.mqroutekey = defs['mqroutekey']

                # If calling program is the config parser service on LB
                if type == 'service':
                    tmpdict = conf['node']['type'][1]['consumer']
                    self.confpath = tmpdict['confpath']
                    self.confname = tmpdict['confname']
                    self.conf = self.confpath + self.confname
        except Exception as e:
            print 'Cannot access file %s! Make sure file exists in the \
            same directory and has correct permissions' % conffile
            print str(e)

    # Connect to RabbitMQ server, return Pika connection object
    def mqconnect(self):
        while True:
            try:
                mqconn = pika.BlockingConnection(pika.ConnectionParameters(host=self.mqserver))
                return mqconn
                # break
            except pika.exceptions.AMQPConnectionError:
                print 'Can\'t connect to %s' % self.mqserver
                print 'Retrying in 5 seconds'
                sleep(5)

    # Channel declare; private method
    # uses Pika connection object as parameter
    # return channel object mqchan
    def declarechannel(self, mqconn):
        while True:
            try:
                mqchan = mqconn.channel()
                mqchan.queue_declare(queue=self.mqueue)
                return mqchan
                # break
            except pika.exceptions.AMQPChannelError:
                print 'Channel error: %s \n' % pika.exceptions.AMQPChannelError
                print 'Retrying in 5 seconds'
                sleep(5)

    # Send Messgage AS A FUNCTION, implement in final product, messagebody as mqbody
    # Calling declarechannel()
    def sendmessage(self, mqchan, mqbody):
        mqchan.queue_declare(queue=self.mqueue)
        mqchan.basic_publish(exchange='', routing_key=self.mqroutekey, body=mqbody)
        print '[x] Message sent to AMQP server'

    # receive messages from RabbitMQ server and append/remove instances from nginx.conf
    def recvmessage(self, mqchan):

        fname = self.conf
        wout = self.confpath + 'new.conf'

        ipregex = '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\.' \
                  '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}|0)\.' \
                  '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}|0)\.' \
                  '(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}|0)' \

        def appendinstance(fname, wout, asinstances):
            writeout = False

            # Open both files, storing data in fin, writing to fout
            with open(fname, 'r') as fin, open(wout, 'w') as fout:
                for line in fin.readlines():
                    # ADD NEW INSTANCES HERE, IN BETWEEN ANCHORS #IPSTART AND #IPEND
                    if re.match('\#IPSTART', line.strip()):
                        writeout = True
                        fout.write(line)
                    elif re.match('\#IPEND', line.strip()):
                        writeout = False
                        fout.write(line)
                    elif writeout:
                        fout.write('%s\tserver %s;\n' % (line, asinstances))
                        writeout = False
                    else:
                        fout.write(line)

        def terminateinstance(fname, wout, terminst):
            writeout = False
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
                        # if line contains IP in list of terminable instances, don't write to file, and remove from list
                        # otherwise, write out to file
                        match = inst.search(line.strip())
                        if match and match.group() in terminst:
                            print 'instance removed: %s' % match.group()
                        else:
                            fout.write(line)
                    else:
                        fout.write(line)

        def callback(ch, method, properties, body):
            print ' Received: %r' % body
            msg = json.loads(body)
            asinstances = msg['IP'].encode("ascii", "replace")

            print msg

            if msg['Action'] == 'Launch':
                appendinstance(fname, wout, asinstances)
            elif msg['Action'] == 'Terminate':
                terminateinstance(fname, wout, asinstances)

            # os.remove(fname)
            # os.rename(wout, fname)

            # Reload config
            # os.popen('nginx reload')

        mqchan.basic_consume(callback, self.mqueue, no_ack=True)

        print 'Waiting for messages... '

        mqchan.start_consuming()



