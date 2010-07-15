#!/bin/sh

#
# IMPORTANT: To use, do the following:
#
# 1. Change 'NAME' variable to the name of your project. E.g. "bhoma"
# 2. Place this file in the TOP-LEVEL of your project, right where 'manage.py' is
# 3. Link it into /etc/init.d e.g. > ln -s /usr/local/my_project/route-init.sh /etc/init.d/
# 4. Add it to the runlevels, on Ubuntu/Debian there is a nice tool to do this for you:
#    > sudo update-rc.d route-init.sh defaults
#
# To Remove: On Ubuntu/Debian, you can remove this from the startup scripts by running
#    > sudo update-rc.d route-init.sh remove
#

### BEGIN INIT INFO
# Provides:          bhoma formentry daemon instance
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts instance of bhoma daemon
# Description:       starts instance of bhoma using start-stop-daemon
### END INIT INFO

# set -e

ME=`readlink -f $0`
WHERE_AM_I=`dirname $ME`

############### EDIT ME ##################
NAME="bhoma" # change to your project name
JAVA_OPTIONS="-Xmx512m -Xss1024k -classpath /etc/jython2.5.1/jython.jar: -Dpython.home=/etc/jython2.5.1 -Dpython.executable=/etc/jython2.5.1/jython org.python.util.jython"
PLAYER_LOCATION="$WHERE_AM_I/../formentry/backend/xformserver.py"
PORT="4444"
DAEMON=/usr/lib/jvm/java-6-openjdk/jre/bin/java
DAEMON_OPTS="$JAVA_OPTIONS $PLAYER_LOCATION $PORT"
RUN_AS=root
APP_PATH=$WHERE_AM_I
BHOMA_PID_FILE=/var/run/${NAME}_formplayer.pid
############### END EDIT ME ##################
test -x $DAEMON || exit 0

do_start() {
    echo -n "Starting xformplayer for $NAME... "
    start-stop-daemon -d $APP_PATH -c $RUN_AS --start --background --pidfile $BHOMA_PID_FILE  --make-pidfile --exec $DAEMON -- $DAEMON_OPTS
    echo "Form Player Started"
}

hard_stop_bhoma() {
    for i in `ps aux | grep -i "xformserver.py" | grep -v grep | awk '{print $2}' ` ; do
        kill -9 $i
    done
    rm $BHOMA_PID_FILE 2>/dev/null
    echo "Hard stopped bhoma"
}

do_hard_restart() {
    do_hard_stop_all
    do_start
}

do_hard_stop_all() {
    hard_stop_bhoma
}

do_stop() {
    echo -n "Stopping bhoma for $NAME... "
    start-stop-daemon --stop --pidfile $BHOMA_PID_FILE
    rm $BHOMA_PID_FILE 2>/dev/null
    echo "bhoma Stopped"
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





