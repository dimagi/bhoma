#!/bin/bash

IFACE=$1
INTERVAL=600

BASEDIR=$(dirname $0)

#call nethogs in a loop to protect against modem disconnects/reconnects

while [ true ]
do
  $BASEDIR/nethogs -d $INTERVAL -c 1 $IFACE
  sleep 3
done