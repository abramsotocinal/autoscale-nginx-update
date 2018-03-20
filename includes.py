from time import sleep
from yaml import load

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
                if type == 'consumer':
                    tmpdict = conf['node']['type'][1]['consumer']
                    self.confpath = tmpdict['confpath']
                    self.confname = tmpdict['confname']
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
    def __declarechannel__(self, mqconn):
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
    def sendmessage(self, mqconn, mqbody):
        mqchan = self.__declarechannel__(mqconn)
        mqchan.queue_declare(queue=self.mqueue)
        mqchan.basic_publish(exchange='', routing_key=self.mqroutekey, body=mqbody)
        print '[x] Message sent to AMQP server'