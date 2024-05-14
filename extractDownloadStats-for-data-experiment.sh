#!/bin/bash
#

STATS_HOME=/home/hpages/STATS
HTML_STATS_HOME=/home/hpages/public_html/stats

notify()
{
	addr="$1"
	stats_script="$0"
	stats_logdir="~hpages/cron.log/stats/"
	stats_host="nebbiolo2"
	subject="Download stats problem: $stats_script returned an error!"
	msg1="Check the logs in $stats_logdir at $stats_host for the details."
	msg2="Please do NOT reply."
	# Make sure to set SMTP settings in ~/.mutt/muttrc
	echo -e "$msg1\n\n$msg2" | mutt -s "$subject" "$addr"
}

cd $STATS_HOME
rm -rf $HTML_STATS_HOME/data-experiment
./extractDownloadStats-for-data-experiment.py
if [ $? -ne 0 ]; then
	#notify maintainer@bioconductor.org
	notify hpages.on.github@gmail.com
	exit 2
fi

