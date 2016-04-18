#!/bin/bash
cd /home/josh/twitter-bot
python main.py $*
while [ 1 ]
do
    secs=$((3))

    while [ $secs -gt 0 ]; do
        echo -ne "Restarting in $secs\033[0K\r"
        sleep 1
        : $((secs--))
    done

    python main.py $*
done
