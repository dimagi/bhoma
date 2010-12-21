#!/bin/bash

# thin wrapper around nethog bandwidth monitoring tool to call it in
# a loop, to protect against the interface going down and back up

IFACE=$1
INTERVAL=600

BASEDIR=$(dirname $0)

#call nethogs in a loop to protect against modem disconnects/reconnects

while [ true ]
do
  $BASEDIR/nethogs -d $INTERVAL -c 1 $IFACE
  sleep 3
done