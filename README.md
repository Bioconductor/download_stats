# download_stats

Scripts used for generating the package download stats displayed at https://bioconductor.org/packages/stats/

These scripts are currently installed and running on nebbiolo2.


===============================================================================
Installation
===============================================================================

1. Install Python modules duckdb and boto3
------------------------------------------

  - On Ubuntu:

      sudo apt-get install python3-boto3
      ## No python3-duckdb yet in Ubuntu 24.04 so use pip to install duckdb:
      sudo apt-get install python3-pip3
      pip3 install -U duckdb

2. Install Python module matplotlib
-----------------------------------

  - On Ubuntu:

      apt-get install python-matplotlib

  - From source:

      a. Get the source tarball from http://matplotlib.sourceforge.net/
      b. Extract
      c. cd matplotlib-x.y.z
      d. python setup.py build
      e. sudo python setup.py install
      f. Test by starting python and trying: import pylab

3. Add the following lines to the crontab for hpages@nebbiolo2
--------------------------------------------------------------

# Sunday afternoon: Get the latest logs from S3
# ---------------------------------------------
#55 15 * * 0 cd /home/hpages/STATS && ./rsync_all_logs2.sh >>/home/hpages/cron.log/stats/rsync_all_logs2.log 2>&1
00 16 * * 0 cd /home/hpages/STATS && ./get_s3_logs.sh >>/home/hpages/cron.log/stats/get_s3_logs-`date +\%Y\%m\%d`.log 2>&1

# Sunday evening: Import logs in duckdb DBs
# -----------------------------------------
00 20 * * 0 cd /home/hpages/STATS && ./makeDownloadDbs.sh >>/home/hpages/cron.log/stats/makeDownloadDbs-`date +\%Y\%m\%d`.log 2>&1

# Monday: Make download stats for software packages
# -------------------------------------------------
07 09 * * 1 cd /home/hpages/STATS && (./extractDownloadStats-for-bioc.sh >>/home/hpages/cron.log/stats/extractDownloadStats-for-bioc-`date +\%Y\%m\%d`.log 2>&1) && (./makeDownloadStatsHTML-for-bioc.sh >>/home/hpages/cron.log/stats/makeDownloadStatsHTML-for-bioc-`date +\%Y\%m\%d`.log 2>&1)

# Tuesday: Make download stats for annotation packages
# ----------------------------------------------------
00 13 * * 2 cd /home/hpages/STATS && (./extractDownloadStats-for-data-annotation.sh >>/home/hpages/cron.log/stats/extractDownloadStats-for-data-annotation-`date +\%Y\%m\%d`.log 2>&1) && (./makeDownloadStatsHTML-for-data-annotation.sh >>/home/hpages/cron.log/stats/makeDownloadStatsHTML-for-data-annotation-`date +\%Y\%m\%d`.log 2>&1)

# Wednesday: Make download stats for experiment packages
# ------------------------------------------------------
00 12 * * 3 cd /home/hpages/STATS && (./extractDownloadStats-for-data-experiment.sh >>/home/hpages/cron.log/stats/extractDownloadStats-for-data-experiment-`date +\%Y\%m\%d`.log 2>&1) && (./makeDownloadStatsHTML-for-data-experiment.sh >>/home/hpages/cron.log/stats/makeDownloadStatsHTML-for-data-experiment-`date +\%Y\%m\%d`.log 2>&1)

# Thursday: Make download stats for workflow packages
# ---------------------------------------------------
00 11 * * 4 cd /home/hpages/STATS && (./extractDownloadStats-for-workflows.sh >>/home/hpages/cron.log/stats/extractDownloadStats-for-workflows-`date +\%Y\%m\%d`.log 2>&1) && (./makeDownloadStatsHTML-for-workflows.sh >>/home/hpages/cron.log/stats/makeDownloadStatsHTML-for-workflows-`date +\%Y\%m\%d`.log 2>&1)

This will update the online reports at:

  https://bioconductor.org/packages/oldstats/

once a week.

