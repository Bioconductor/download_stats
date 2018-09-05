#!/bin/sh
#

set -e  # Exit immediately if a simple command exits with a non-zero status

STATS_HOME=/home/biocadmin/STATS
HTML_STATS_HOME=/home/biocadmin/public_html/stats

cd $STATS_HOME
cp main.css $HTML_STATS_HOME
./makeDownloadStatsHTML-for-workflows.py

rsync --delete -ave ssh $HTML_STATS_HOME/ webadmin@master.bioconductor.org:/extra/www/bioc/packages/stats/

