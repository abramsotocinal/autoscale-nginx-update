from time import sleep
from sys import exit
from includes import Autoscale

try:
    import pika
except ImportError:
    print 'Cannot load pika module. Please make sure you have it installed and is accessible'
    exit(1)


def main():
    # Connect to RabbitMQ, create channel
    asconnect = Autoscale('service')
    conn = asconnect.mqconnect()
    chan = asconnect.declarechannel(conn)

    # Receive message from MQ and perform acction
    asconnect.recvmessage(chan)

    conn.close()

if __name__ == '__main__':

    main()