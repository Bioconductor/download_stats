#!/usr/bin/env python3
#

import os
import datetime

import stats_config
import stats_utils

html_stats_home = '/home/biocadmin/public_html/stats'
biocrepo = 'bioc'
from_year = 2009
to_year = datetime.date.today().year  # current year

biocrepo_subdir = stats_config.biocrepo2subdir[biocrepo]
biocrepo_dirpath = os.path.join(html_stats_home, biocrepo_subdir)
allpkg_stats_filename = '%s_pkg_stats.tab' % biocrepo
allpkg_scores_filename = '%s_pkg_scores.tab' % biocrepo

def extractDownloadStatsForYear(year):
    print('')
    print('===================================================================')
    print('===================================================================')
    print('START EXTRACTING SOFTARE PACKAGE DOWNLOAD STATS FOR YEAR %s' % year)
    print('===================================================================')
    print('===================================================================')
    print('')
    wd0 = os.getcwd()
    dbfile_path = 'download_db_' + str(year) + '.sqlite'
    dbfile_path = os.path.join('download_dbs', dbfile_path)
    conn = stats_utils.SQL_connectToDB(dbfile_path)
    cur = conn.cursor()
    if not os.path.exists(biocrepo_dirpath):
        os.mkdir(biocrepo_dirpath)
    os.chdir(biocrepo_dirpath)
    stats_utils.extract_all_stats_for_year(cur, biocrepo, year)
    cur.close()
    conn.close()
    os.chdir(wd0)
    print('')
    print('===================================================================')
    print('===================================================================')
    print('DONE EXTRACTING SOFTARE PACKAGE DOWNLOAD STATS FOR YEAR %s' % year)
    print('===================================================================')
    print('===================================================================')
    print('')
    return

for year in range(from_year, to_year + 1):
    extractDownloadStatsForYear(year)

os.chdir(biocrepo_dirpath)
stats_utils.make_package_stats_files(biocrepo, from_year, to_year)
stats_utils.make_biocrepo_stats_file(biocrepo, from_year, to_year)
stats_utils.make_allpkg_stats_file(allpkg_stats_filename, biocrepo)
stats_utils.make_allpkg_scores_file(allpkg_scores_filename, biocrepo)

