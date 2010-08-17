#!/bin/sh

ME=`readlink -f $0`
WHERE_AM_I=`dirname $ME`
APP_PATH=$WHERE_AM_I

NAME="bhoma" # change to your project name
SCRIPT_LOCATION="$WHERE_AM_I/xrestart.py"
DAEMON=/usr/bin/python
RUN_AS=root

test -x $DAEMON || exit 0

do_start() {
    /sbin/start-stop-daemon -d $APP_PATH -c $RUN_AS --start --background --exec $DAEMON -- $SCRIPT_LOCATION
}

case "$1" in
  start)
        do_start
        ;;

  *)
        echo "Usage: $ME {start}" >&2
        exit 1
        ;;
esac

exit 0

