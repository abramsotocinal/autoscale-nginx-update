import pika
import time
import signal
import os
import json

mqserver = '192.168.0.79'
mqueue='Test'
mqroutekey=mqueue
mqbody='Hello'


# Get host details, send to MQ server
hostip = os.popen("ip -f inet addr show eth0 | grep -Po 'inet \K[\d.]+'").read()
hostname = os.popen('hostname').read()
mqbody = {'IP': hostip.strip(), 'Hostname': hostname.strip(), 'Action': 'Launch'}
mqbody = json.dumps(mqbody)


'''
#connect to rabbitmq server
while True:
    try:
        mqconn = pika.BlockingConnection(pika.ConnectionParameters(host=mqserver))
        break
    except pika.exceptions.AMQPConnectionError:
        print 'Can\'t connect to %s' % mqserver
        print 'Retrying in 5 seconds'
        time.sleep(5)

# Declare channel
try:
    mqchan = mqconn.channel()
    mqchan.queue_declare(queue=mqueue)
except pika.exceptions.AMQPChannelError:
    print 'Channel error: %s' % pika.exceptions.AMQPChannelError


# Send Message
mqchan.queue_declare(queue=mqueue)
mqchan.basic_publish(exchange='', routing_key=mqroutekey, body=mqbody)
print '[x] Message sent to server: %s' % mqserver

time.sleep(30)

#while signal.SIGINT
mqconn.close()

'''

#Connect to RabbitMQ server AS A FUNCTION, return pika object, implement for final product
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

#Send Messgage AS A FUNCTION, implement in final product
def sendmessage(mqchan,mqroutekey,mqbody):
    mqchan.queue_declare(queue=mqueue)
    mqchan.basic_publish(exchange='', routing_key=mqroutekey, body=mqbody)
    print '[x] Message sent to server: %s' % mqserver




if __name__ == '__main__':

    mqconn = mqconnect(mqserver)
    mqchan = declarechannel(mqconn,mqueue)
    sendmessage(mqchan, mqroutekey, mqbody)

    mqconn.close()