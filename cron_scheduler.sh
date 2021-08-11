#!/bin/bash

echo "Setting up cron!";
# Change timezone
ln -sf /usr/share/zoneinfo/Brazil/East /etc/localtime;
# Set job vars
cronjob1="0 0 * * * cd $( pwd ); $( which python3 ) $( pwd )/reset_notif.py";
cronjob2="55 23 * * * cd $( pwd ); $( which python3 ) $( pwd )/timeseries.py";
# Set cronjobs
( echo "$cronjob1" && echo "$cronjob2" ) | crontab - ;
# List them
crontab -l;

echo "Finishing script!";