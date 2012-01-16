#!/bin/sh

### BEGIN INIT INFO
# Provides:          mani runner daemon instance
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts instance of modem config daemon
# Description:       starts instance of modem config using start-stop-daemon
### END INIT INFO

ME=`readlink -f $0`
WHERE_AM_I=`dirname $ME`
SCRIPTS="$WHERE_AM_I/conflict-resolver.sh
$WHERE_AM_I/patient-formlistener.sh
$WHERE_AM_I/patient-upgrader.sh"

test -x $DAEMON || exit 0

do_start() {
    echo "Starting bhoma central server scripts... "
    for script in $SCRIPTS; do
        $script start
    done
    echo "Central server scripts started"
}

do_stop() {
    echo -n "Stopping bhoma central server scripts. "
    for script in $SCRIPTS; do
        $script stop
    done
    echo "bhoma scripts stopped"
}
do_restart() {
    do_stop
    sleep 2
    do_start
}

case "$1" in
  start)
        do_start
        ;;

  stop)
        do_stop
        ;;

  restart|force-reload)
        do_restart
        ;;

  *)
        echo "Usage: $ME {start|stop|restart|force-reload}" >&2
        exit 1
        ;;
esac

exit 0