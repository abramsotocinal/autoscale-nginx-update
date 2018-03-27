# Nginx Loadbalancer Updater

Script updates the upstream directive in the nginx.conf everytime a new Autoscale instance is launched. Originally designed for AWS but aim is for it to be platform agnostic.

This requires RabbitMQ as a message broker for for autoscaling messages sent during instance launch. An agent(lbupdate-agent.py) will need to be installed on the instance.

A service on the load balancer(lbupdate.py) will be listening for those messages queued on the RabbitMQ server and apply those changes.

## Getting Started

To be updated

### Prerequisites

RabbitMQ

Pika client - Defined in the requirement.txt

More to be added

### Installing

To be updated

