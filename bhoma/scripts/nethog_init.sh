#!/bin/bash

# startup launch script for nethog bandwidth monitor

# place in /etc/init.d
# set as executable
# update-rc.d nethog_init.sh defaults

IFACE=ppp0
LOGFILE=/var/lib/bhoma/netlog

/var/src/bhoma/bhoma/scripts/nethog_wrapper.sh $IFACE >> $LOGFILE &

