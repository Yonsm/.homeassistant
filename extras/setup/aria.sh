#!/bin/sh

apt install aria2c
cat <<\EOF > /etc/init.d/aria
#!/bin/sh

start()
{
  if [ ! -z "$1" ]; then
    DDIR="$1"
  elif [ -d /mnt/STORE/Downloads ]; then
    DDIR=/mnt/STORE/Downloads
  elif [ -d ~/Downloads ]; then
    DDIR=~/Downloads
  else
    DDIR=$(pwd)
  fi

  TASK=$DDIR/aria.task
  if [ ! -r $TASK ]; then touch $TASK; fi

  ARIA2C=$(cd "${0%/*}"; pwd)/aria2c
  if [ ! -x $ARIA2C ]; then ARIA2C=aria2c; fi

  XOPT="--rpc-certificate=/root/.homeassistant/fullchain.cer --rpc-private-key=/root/.homeassistant/privkey.pem --rpc-secure=true"
  $ARIA2C -D -d $DDIR -c -i $TASK --save-session=$TASK --enable-rpc --rpc-listen-all --rpc-allow-origin-all --file-allocation=falloc --disable-ipv6 $XOPT
}

case "$1" in
  start)
    echo "Starting aria2c daemon..."
    start $2
    ;;
  stop)
    echo "Shutting down aria2c daemon..."
    killall aria2c
    ;;
  restart)
    killall aria2c
    sleep 1
    start $2
    ;;
  '')
    echo "Aria2c helper by Yonsm"
    echo
    echo "Usage: $0 [start|stop|restart|<DIR>] [DIR]"
    echo
    ;;
  *)
    start $1
    ;;
esac

EOF

chmod 755 /etc/init.d/aria
#ln -s /mnt/STORE/Downloads ~
update-rc.d aria defaults
