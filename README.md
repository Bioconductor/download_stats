# download_stats

Scripts used for generating the package download stats displayed at https://bioconductor.org/packages/stats/

These scripts are currently installed and running on stats.bioconductor.org


===============================================================================
Installation
===============================================================================

1. Install Python module boto
-----------------------------

  - On Ubuntu:

      sudo apt-get install python-pip
      sudo pip install --upgrade pip
      sudo pip install -U boto

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

3. Add the following lines to the crontab for biocadmin@stats.bioconductor.org
------------------------------------------------------------------------------

# Make the SQLite DBs for the download stats (Monday and Thursday each week)
# --------------------------------------------------------------------------
55 04 * * 1,4 cd /home/biocadmin/STATS && (./rsync_all_logs2.sh && ./get_s3_logs.sh) >>/home/biocadmin/cron.log/stats/get_logs.log 2>&1
55 11 * * 1,4 cd /home/biocadmin/STATS && ./makeDownloadDbs.sh >>/home/biocadmin/cron.log/stats/makeDownloadDbs.log 2>&1

# Download stats for software packages (Tuesday and Friday each week)
# -------------------------------------------------------------------
55 05 * * 2,5 cd /home/biocadmin/STATS && ./extractDownloadStats-for-bioc.sh >>/home/biocadmin/cron.log/stats/extractDownloadStats-for-bioc.log 2>&1
55 07 * * 2,5 cd /home/biocadmin/STATS && ./makeDownloadStatsHTML-for-bioc.sh >>/home/biocadmin/cron.log/stats/makeDownloadStatsHTML-for-bioc.log 2>&1

# Download stats for annotation packages (Tuesday and Friday each week)
# ---------------------------------------------------------------------
55 09 * * 2,5 cd /home/biocadmin/STATS && ./extractDownloadStats-for-data-annotation.sh >>/home/biocadmin/cron.log/stats/extractDownloadStats-for-data-annotation.log 2>&1
55 11 * * 2,5 cd /home/biocadmin/STATS && ./makeDownloadStatsHTML-for-data-annotation.sh >>/home/biocadmin/cron.log/stats/makeDownloadStatsHTML-for-data-annotation.log 2>&1

# Download stats for experiment packages (Tuesday and Friday each week)
# ---------------------------------------------------------------------
55 13 * * 2,5 cd /home/biocadmin/STATS && ./extractDownloadStats-for-data-experiment.sh >>/home/biocadmin/cron.log/stats/extractDownloadStats-for-data-experiment.log 2>&1
55 15 * * 2,5 cd /home/biocadmin/STATS && ./makeDownloadStatsHTML-for-data-experiment.sh >>/home/biocadmin/cron.log/stats/makeDownloadStatsHTML-for-data-experiment.log 2>&1

This will update the online reports at:

  http://bioconductor.org/packages/stats/

every Tuesday and Friday morning.

