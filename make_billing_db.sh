#!/bin/sh
#

set -e  # Exit immediately if a simple command exits with a non-zero status

STATS_HOME=/home/biocstats/STATS

cd $STATS_HOME
./make_billing_db.py

