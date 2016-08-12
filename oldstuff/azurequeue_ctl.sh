#! /bin/sh



OPENERP_HOME="/home/bitnami1/whatsapp/azure"
GEVENT_START="$OPENERP_HOME/serve_azure.py"
GEVENT_PROGRAM="serve_azure.py"
GEVENT_STATUS=""
GEVENT_PID=""
GEVENT_STATUS=""
ERROR=0

is_service_running() {
    GEVENT_PID=`ps ax | awk '/\/[s]erve_azure.py/ {print $1}'`
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
        GEVENT_STATUS="serve_azure.py not running"
    else
        GEVENT_STATUS="serve_azure.py already running"
    fi
    return $RUNNING
}

start_gevent() {
    test -f /home/bitnami1/whatsapp/.noazure && echo .noazure exists: exiting &&exit
    is_gevent_running
    RUNNING=$?
    if [ $RUNNING -eq 1 ]; then
        echo "$0 $ARG: serve_azure.py already running"
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
        echo "$0 $ARG: serve_azure.py started"
        sleep 2
    else
        echo "$0 $ARG: serve_azure.py could not be started"
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
    sleep 3

    is_gevent_running
    RUNNING=$?
    if [ $RUNNING -eq 0 ]; then
            echo "$0 $ARG: serve_azure.py stopped"
        else
            echo "$0 $ARG: serve_azure.py could not be stopped"
            ERROR=4
    fi
}

if [ "x$1" = "xstart" ]; then
    start_gevent >/tmp/Xrestart.log
elif [ "x$1" = "xstop" ]; then
    stop_gevent >/tmp/Xrestart.log
elif [ "x$1" = "xstatus" ]; then
    is_gevent_running >/tmp/Xrestart.log
    echo "$GEVENT_STATUS"
fi

exit $ERROR
