#!/bin/sh
#

set -e  # Exit immediately if a simple command exits with a non-zero status

STATS_HOME=/home/biocadmin/STATS
HTML_STATS_HOME=/home/biocadmin/public_html/stats

cd $STATS_HOME
rm -rf $HTML_STATS_HOME/workflows
./extractDownloadStats-for-workflows.py

