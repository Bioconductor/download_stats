#!/bin/sh
#

set -e  # Exit immediately if a simple command exits with a non-zero status

STATS_HOME=/home/biocadmin/STATS

cd $STATS_HOME
./get_billing_logs.py


