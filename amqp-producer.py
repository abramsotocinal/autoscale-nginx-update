import pika
from time import sleep
import signal, sys
import os
import json





# Get host details, send to MQ server
def messagebody(action='Launch'):
    hostip = os.popen("ip -f inet addr show eth0 | grep -Po 'inet \K[\d.]+'").read()
    hostname = os.popen('hostname').read()
    mqbody = {'IP': hostip.strip(), 'Hostname': hostname.strip(), 'Action': action}
    mqbody = json.dumps(mqbody)
    return mqbody

#Send Messgage AS A FUNCTION, implement in final product, messagebody as mqbody
def sendmessage(mqchan,mqueue,mqroutekey,mqbody):
    mqchan.queue_declare(queue=mqueue)
    mqchan.basic_publish(exchange='', routing_key=mqroutekey, body=mqbody)
    print '[x] Message sent to AMQP server'


# Connect to RabbitMQ server AS A FUNCTION, return pika object, implement for final product
def mqconnect(mqserver):
    while True:
        try:
            mqconn = pika.BlockingConnection(pika.ConnectionParameters(host=mqserver))
            return mqconn
            break
        except pika.exceptions.AMQPConnectionError:
            print 'Can\'t connect to %s' % mqserver
            print 'Retrying in 5 seconds'
            time.sleep(5)

#Channel declare AS FUNCTION

def declarechannel(mqconn,mqueue):
    while True:
        try:
            mqchan = mqconn.channel()
            mqchan.queue_declare(queue=mqueue)
            return mqchan
            break
        except pika.exceptions.AMQPChannelError:
            print 'Channel error: %s \n' % pika.exceptions.AMQPChannelError
            print 'Retrying in 5 seconds'
            time.sleep(5)


def main():
    # RabbitMQ server
    mqserver = '192.168.0.79'
    # Queue name
    mqueue = 'Test'
    mqroutekey = mqueue

    mqconn = mqconnect(mqserver)
    mqchan = declarechannel(mqconn, mqueue)
    sendmessage(mqchan, mqueue, mqroutekey, messagebody())

    # Catching system signals, still need to implement. Fucking signals. I don't want to make a single class just for
    #  this
    # NOTE: intention is, when SIGTERM is received, send Termination message to RabbitMQ server.
    # EDIT: I've no fucking clue how to do it anymore so I'm putting the handler function inside main(). I'll move it
    # once I've figured it out. fuck it
    def sigtermhandler(signal, frame):
        print 'INT signal received. Program Terminated'
        sendmessage(mqchan, mqueue, mqroutekey, messagebody(action='Terminate'))
        mqconn.close()
        sys.exit(0)

    #signal.signal(signal.SIGTERM, sigtermhandler)
    signal.signal(signal.SIGINT, sigtermhandler)
    #Keep program running FOREVER, or until system halt
    while True:
        sleep(300)



if __name__ == '__main__':

    main()
