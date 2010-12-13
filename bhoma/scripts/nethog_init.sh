#!/bin/bash

IFACE=ppp0
LOGFILE=/var/lib/bhoma/netlog

/var/src/bhoma/bhoma/scripts/nethog_wrapper.sh $IFACE >> $LOGFILE &

