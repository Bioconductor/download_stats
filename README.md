# download_stats

IMPORTANT NOTE: This repository contains the old code for producing the _Bioconductor package download stats_. **The new code is in the [bio-web-stats](https://github.com/Bioconductor/bio-web-stats) repository.**

This repository contains the code used for producing the _Bioconductor package download stats_ that are displayed at https://bioconductor.org/packages/oldstats/
Note that this code is still occasionally running on a Jetstream2 VM (m3.quad Linux instance named `biocstats`).


## Installation

### Install Python modules boto3, matplotlib, and duckdb

The `boto3` and `matplotlib` are both available via `apt-get install`
as Debian packages `python3-boto3` and `python3-matplotlib`:

    sudo apt-get install python3-boto3 python3-matplotlib

However, there's no `python3-duckdb` yet in Ubuntu 24.04 (as of September
2024), so we'll use `pip3` to install `duckdb`.

- Make sure `python3-full` is installed:

    sudo apt-get install python3-full

- Note that, starting with Ubuntu 24.04, using `pip3` to install modules
  system-wide is **strongly** discouraged. We must use a virtual environment
  instead. In the following steps, we'll create a virtual environment in
  `~/.venv` and make it the default.

- Create virtual environment in `~/.venv`:
    ```
    python3 -m venv ~/.venv
    ```

- Add `/home/biocstats/.venv/bin` to `biocstats`'s `PATH`. Best way to do
  this is to add the following line at the end of the `.profile` file:
    ```
    PATH="$HOME/.venv/bin:$PATH"
    ```

- Logout and login again for the new `PATH` to take effect. Then try:
    ```
    which python3    # /home/biocstats/.venv/bin/python3
    which pip3       # /home/biocstats/.venv/bin/pip3
    ```

- Install any missing module with `pip3 install -U <module>`. This will
  install the specified module in the `~/.venv` virtual environment.
  You can check that the module is effectively installed and loadable
  by trying `import <module>` in an interactive Python3 session.

### Clone the download_stats repo

    git clone https://github.com/Bioconductor/download_stats

Then create `STATS` symlink in `biocstats`'s home:

    cd
    ln -s /path/to/download_stats STATS

### Create folders bioc-access-logs/, download_dbs/, public_html/stats/, and cron.log/

Create `bioc-access-logs/` and `download_dbs/` in `STATS`:

    cd ~/STATS
    mkdir bioc-access-logs download_dbs
    cd bioc-access-logs
    mkdir apache2 s3 squid

Create `public_html/stats/` and `cron.log/` in `biocstats`'s home:

    cd
    mkdir -p public_html/stats
    mkdir cron.log

### Add the following lines to the crontab for biocstats@biocstats

    USER=biocstats
    
    # By default, PATH is set to /usr/bin:/bin only.
    # We need /home/biocstats/.venv/bin in the PATH so we can find
    # /home/biocstats/.venv/bin/python3 which has all the required
    # modules installed (e.g. duckdb etc..)
    # Make sure to place /home/biocstats/.venv/bin **before** /usr/bin.
    PATH="/home/biocstats/.venv/bin:/usr/bin:/bin"
    
    # ==============================================================================
    # DOWNLOAD STATS
    # ------------------------------------------------------------------------------
    
    # Sunday afternoon: Get the latest logs from S3
    # ---------------------------------------------
    #55 15 * * 0 cd /home/biocstats/STATS && ./rsync_all_logs2.sh >>/home/biocstats/cron.log/rsync_all_logs2.log 2>&1
    00 14 * * 0 cd /home/biocstats/STATS && ./get_s3_logs.sh >>/home/biocstats/cron.log/get_s3_logs-`date +\%Y\%m\%d`.log 2>&1
    
    # Sunday evening: Import logs in duckdb DBs
    # -----------------------------------------
    00 17 * * 0 cd /home/biocstats/STATS && ./makeDownloadDbs.sh >>/home/biocstats/cron.log/makeDownloadDbs-`date +\%Y\%m\%d`.log 2>&1
    
    # Tuesday: Make download stats for software packages
    # --------------------------------------------------
    00 06 * * 2 cd /home/biocstats/STATS && (./extractDownloadStats-for-bioc.sh >>/home/biocstats/cron.log/extractDownloadStats-for-bioc-`date +\%Y\%m\%d`.log 2>&1) && (./makeDownloadStatsHTML-for-bioc.sh >>/home/biocstats/cron.log/makeDownloadStatsHTML-for-bioc-`date +\%Y\%m\%d`.log 2>&1)
    
    # Wednesday: Make download stats for annotation packages
    # ------------------------------------------------------
    00 08 * * 3 cd /home/biocstats/STATS && (./extractDownloadStats-for-data-annotation.sh >>/home/biocstats/cron.log/extractDownloadStats-for-data-annotation-`date +\%Y\%m\%d`.log 2>&1) && (./makeDownloadStatsHTML-for-data-annotation.sh >>/home/biocstats/cron.log/makeDownloadStatsHTML-for-data-annotation-`date +\%Y\%m\%d`.log 2>&1)
    
    # Thursday: Make download stats for experiment packages
    # -----------------------------------------------------
    00 07 * * 4 cd /home/biocstats/STATS && (./extractDownloadStats-for-data-experiment.sh >>/home/biocstats/cron.log/extractDownloadStats-for-data-experiment-`date +\%Y\%m\%d`.log 2>&1) && (./makeDownloadStatsHTML-for-data-experiment.sh >>/home/biocstats/cron.log/makeDownloadStatsHTML-for-data-experiment-`date +\%Y\%m\%d`.log 2>&1)
    
    # Friday: Make download stats for workflow packages
    # -------------------------------------------------
    00 06 * * 5 cd /home/biocstats/STATS && (./extractDownloadStats-for-workflows.sh >>/home/biocstats/cron.log/extractDownloadStats-for-workflows-`date +\%Y\%m\%d`.log 2>&1) && (./makeDownloadStatsHTML-for-workflows.sh >>/home/biocstats/cron.log/makeDownloadStatsHTML-for-workflows-`date +\%Y\%m\%d`.log 2>&1)

This will update the online reports at:

  https://bioconductor.org/packages/oldstats/

once a week.

