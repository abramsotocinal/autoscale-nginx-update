import signal
import sys
import os
import json
from includes import Autoscale
from time import sleep


# Get host details, send to MQ server
def messagebody(action='Launch'):
    hostip = os.popen("ip -f inet addr show eth0 | grep -Po 'inet \K[\d.]+'").read()
    hostname = os.popen('hostname').read()
    mqbody = {'IP': hostip.strip(), 'Hostname': hostname.strip(), 'Action': action}
    mqbody = json.dumps(mqbody)
    return mqbody

def main():

    # Init Autoscale object as 'agent' type
    asconnect = Autoscale('agent')

    # Create Pika connection object
    conn = asconnect.mqconnect()

    # Pika Channel object
    chan = asconnect.declarechannel(conn)

    # Send message to RabbitMQ server using Pika channel object
    asconnect.sendmessage(chan, messagebody())

    # Catching system signals, still need to implement. Fucking signals. I don't want to make a single class just for
    #  this
    # NOTE: intention is, when SIGTERM is received, send Termination message to RabbitMQ server.
    # EDIT: I've no fucking clue how to do it anymore so I'm putting the handler function inside main(). I'll move it
    # once I've figured it out. fuck it
    def sigtermhandler(signal, frame):
        print 'SIGTERM signal received. Program Terminated'
        asconnect.sendmessage(conn, messagebody(action='Terminate'))
        conn.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigtermhandler)

    #Keep program running FOREVER, or until system halt
    while True:
        sleep(300)

if __name__ == '__main__':

    main()