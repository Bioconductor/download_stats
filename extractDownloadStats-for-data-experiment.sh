#!/bin/bash
#

STATS_HOME=/home/biocadmin/STATS
HTML_STATS_HOME=/home/biocadmin/public_html/stats

notify()
{
	addr="$1"
	stats_script="$0"
	stats_logdir="~biocadmin/cron.log/stats/"
	stats_host="stats.bioconductor.org"
	subject="Download stats problem: $stats_script returned an error!"
	msg1="Check the logs in $stats_logdir on $stats_host for the details."
	msg2="Please do NOT reply."
	# Make sure to set SMTP settings in ~/.mutt/muttrc
	echo -e "$msg1\n\n$msg2" | mutt -s "$subject" "$addr"
}

cd $STATS_HOME
rm -rf $HTML_STATS_HOME/data-experiment
./extractDownloadStats-for-data-experiment.py
if [ $? -ne 0 ]; then
	notify maintainer@bioconductor.org
fi

