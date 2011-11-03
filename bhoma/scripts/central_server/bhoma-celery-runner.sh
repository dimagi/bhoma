#!/bin/sh

### BEGIN INIT INFO
# Provides:          runs celery for bhoma 
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts instance of bhoma celery
# Description:       starts instance of bhoma celery
### END INIT INFO

ME=`readlink -f $0`
WHERE_AM_I=`dirname $ME`
TMP_PATH=`dirname $WHERE_AM_I`
APP_PATH=`dirname $TMP_PATH`

NAME="bhoma" 
MANAGE_PY_LOCATION="$APP_PATH/manage.py"
DAEMON=/usr/bin/python
RUN_AS=root
BHOMA_PID_FILE=/var/run/${NAME}_celery.pid

test -x $DAEMON || exit 0

do_start() {
    echo -n "Starting bhoma celery... "
    start-stop-daemon -d $APP_PATH -c $RUN_AS --start --background --pidfile $BHOMA_PID_FILE  --make-pidfile --exec $DAEMON -- $MANAGE_PY_LOCATION celeryd
    echo "celery started"
}

hard_stop_bhoma() {
    for i in `ps aux | grep -i "celeryd" | grep -v grep | awk '{print $2}' ` ; do
        kill -9 $i
    done
    rm $BHOMA_PID_FILE 2>/dev/null
    echo "Hard stopped celery"
}

do_hard_restart() {
    do_hard_stop_all
    do_start
}

do_hard_stop_all() {
    hard_stop_bhoma
}

do_stop() {
    echo -n "Stopping bhoma celery.. "
    start-stop-daemon --stop --pidfile $BHOMA_PID_FILE
    rm $BHOMA_PID_FILE 2>/dev/null
    echo "celery Stopped"
}
do_restart() {
    do_stop
    sleep 2
    do_start
}
# check on PID's, if not running, restart
do_check_restart() {
    for pidf in $BHOMA_PID_FILE ; do
        if [ -f $pidf ] ; then
            pid=`cat $pidf`
            if [ ! -e /proc/$pid ] ; then
                echo "Process for file $pidf not running. Performing hard stop, restart"
                do_hard_restart
                return
            fi
        else
            do_hard_restart
        fi
    done
}

case "$1" in
  start)
        do_start
        ;;

  stop)
        do_stop
        ;;

  check-restart)
        do_check_restart
        ;;

  hard-stop)
        do_hard_stop_all
        ;;

  hard-restart)
        do_hard_restart
        ;;
  restart|force-reload)
        do_restart
        ;;

  *)
        echo "Usage: $ME {start|stop|restart|force-reload|check-restart|hard-stop|hard-restart}" >&2
        exit 1
        ;;
esac

exit 0