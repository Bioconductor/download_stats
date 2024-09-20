#!/bin/bash
#

STATS_HOME=/home/biocstats/STATS
HTML_STATS_HOME=/home/biocstats/public_html/stats

notify()
{
	addr="$1"
	stats_script="$0"
	stats_logdir="~biocstats/cron.log/"
	stats_host="stats.bioconductor.org"
	subject="Download stats problem: $stats_script returned an error!"
	msg1="Check the logs in $stats_logdir at $stats_host for the details."
	msg2="Please do NOT reply."
	# Make sure to set SMTP settings in ~/.mutt/muttrc
	echo -e "$msg1\n\n$msg2" | mutt -s "$subject" "$addr"
}

cd $STATS_HOME
rm -rf $HTML_STATS_HOME/bioc
./extractDownloadStats-for-bioc.py
if [ $? -ne 0 ]; then
	notify maintainer@bioconductor.org
	exit 2
fi

