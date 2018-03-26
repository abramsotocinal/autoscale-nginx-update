#!/bin/bash

# Place startup script in /etc/rc.d and run script from /opt/lb-update or /path/to/script
# For Ubuntu, add this line to the rc.local script

python -b /opt/lbupdate-agent/lbupdate-agent.py &
