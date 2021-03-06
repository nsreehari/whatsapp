#! /bin/sh


OPENERP_HOME="/home/bitnami1/whatsapp"
GEVENT_START="$OPENERP_HOME/telegram_mgmt.py"
GEVENT_PROGRAM="telegram_mgmt.py"
GEVENT_STATUS=""
GEVENT_PID=""
GEVENT_STATUS=""
ERROR=0

is_service_running() {
    GEVENT_PID=`ps ax | awk '/\/[t]elegram_mgmt.py/ {print $1}'`
    if [ "x$GEVENT_PID" != "x" ]; then
        RUNNING=1
    else
        RUNNING=0
    fi
    return $RUNNING
}

is_gevent_running() {
    is_service_running "$GEVENT_PROGRAM"
    RUNNING=$?
    if [ $RUNNING -eq 0 ]; then
        GEVENT_STATUS="telegram_mgmt.py not running"
    else
        GEVENT_STATUS="telegram_mgmt.py already running"
    fi
    return $RUNNING
}

start_gevent() {
    test -f /home/bitnami1/whatsapp/.notelegrammgmt && echo .notelegrammgmt exists: exiting &&exit
    is_gevent_running
    RUNNING=$?
    if [ $RUNNING -eq 1 ]; then
        echo "$0 $ARG: telegram_mgmt.py already running"
        exit
    fi
    if [ `id -u` != 0 ]; then
        /bin/sh -c "((cd $OPENERP_HOME && $GEVENT_START 2>&1) >/dev/null) &"
    else
        su - daemon -s /bin/sh -c "((cd $OPENERP_HOME && $GEVENT_START 2>&1) >/dev/null) &"
    fi
    sleep 4
    is_gevent_running
    RUNNING=$?
    if [ $RUNNING -eq 0 ]; then
        ERROR=1
    fi

    if [ $ERROR -eq 0 ]; then
        echo "$0 $ARG: telegram_mgmt.py started"
        sleep 2
    else
        echo "$0 $ARG: telegram_mgmt.py could not be started"
        ERROR=3
    fi
}

stop_gevent() {
    NO_EXIT_ON_ERROR=$1
    is_gevent_running
    RUNNING=$?
    if [ $RUNNING -eq 0 ]; then
        echo "$0 $ARG: $GEVENT_STATUS"
        if [ "x$NO_EXIT_ON_ERROR" != "xno_exit" ]; then
            exit
        else
            return
        fi
    fi

    kill $GEVENT_PID
    sleep 6

    is_gevent_running
    RUNNING=$?
    if [ $RUNNING -eq 0 ]; then
            echo "$0 $ARG: telegram_mgmt.py stopped"
        else
            echo "$0 $ARG: telegram_mgmt.py could not be stopped"
            ERROR=4
    fi
}

if [ "x$1" = "xstart" ]; then
    start_gevent
elif [ "x$1" = "xstop" ]; then
    stop_gevent
elif [ "x$1" = "xrestart" ]; then
    stop_gevent
    sleep 3
    start_gevent
elif [ "x$1" = "xstatus" ]; then
    is_gevent_running
    echo "$GEVENT_STATUS"
fi

exit $ERROR
