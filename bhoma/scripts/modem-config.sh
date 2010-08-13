#!/bin/sh

# IMPORTANT: To use, do the following:
#
# 1. Edit any parameters necessary below in the EDIT ME section.
#    In most cases the default should be fine.
# 2. Link it into /etc/init.d e.g. > ln -s /var/src/bhoma/bhoma/scripts/modem-config.sh /etc/init.d/modem-config
# 3. Test: sudo /etc/init.d/modem-config
#          Should print out usage.  Start should (try to) start the modem.  Stop should stop it.
# If it complains about permissions make sure the file is executable and you are root
# 4. Once it works, add it to the runlevels, on Ubuntu/Debian there is a nice tool to do this for you:
#    > sudo update-rc.d modem-config defaults
#
# To Remove: On Ubuntu/Debian, you can remove this from the startup scripts by running
#    > sudo update-rc.d modem-config remove
#

### BEGIN INIT INFO
# Provides:          modem config daemon instance
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts instance of modem config daemon
# Description:       starts instance of modem config using start-stop-daemon
### END INIT INFO

ME=`readlink -f $0`
WHERE_AM_I=`dirname $ME`
APP_PATH=$WHERE_AM_I

NAME="bhoma" # change to your project name
SCRIPT_LOCATION="$WHERE_AM_I/modemrunner.py"
DAEMON=/usr/bin/python
RUN_AS=root
BHOMA_PID_FILE=/var/run/${NAME}_modemrunner.pid

test -x $DAEMON || exit 0

do_start() {
    echo "Starting modemrunner for $NAME... "
    echo "Running  $DAEMON -- $SCRIPT_LOCATION"
    start-stop-daemon -d $APP_PATH -c $RUN_AS --start --background --pidfile $BHOMA_PID_FILE  --make-pidfile --exec $DAEMON -- $SCRIPT_LOCATION
    echo "Modemrunner started"
}

stop_modem() {
    for i in `ps aux | grep -i "wvdial" | grep -v grep | awk '{print $2}' ` ; do
        kill -9 $i
    done
    for i in `ps aux | grep -i "pppd" | grep -v grep | awk '{print $2}' ` ; do
        kill -9 $i
    done
    rm $BHOMA_PID_FILE 2>/dev/null
    echo "Hard stopped modem"
}

do_stop() {
    echo -n "Stopping modem for $NAME... "
    stop_modem
    echo "bhoma modem stopped"
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

  restart)
        do_restart
        ;;

  *)
        echo "Usage: $ME {start|stop|restart}" >&2
        exit 1
        ;;
esac

exit 0

