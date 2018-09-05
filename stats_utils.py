import sys
import os
import string
import sqlite3
import re
import datetime
import time
import math
import matplotlib
matplotlib.use('agg')
import pylab
### urllib.urlopen() doesn't raise an error when the object is not found (HTTP
### Error 404) but urllib2.urlopen() does (raises an urllib2.HTTPError object)
import urllib2

import stats_config

#access_logfiles_regex = '^access.log-2008(07|08|09|10).*\.gz$'
#access_logfiles_regex = '^access.log-200[78].*\.gz$'
#access_logfiles_regex = '^(access(-bioc)?.log-20(08|09|10|11|12).*\.gz|bioconductor-access.log-.*)$'
access_logfiles_regex = '^(access(-bioc)?.log-20(08|09|10|11|12).*\.gz|bioconductor-access.log.*)$'

### Follows symlinks (if they are supported).
def getMatchingFiles(dir=".", regex="", full_names=False, recurse=False,
    match_type="match"):
    p = re.compile(regex)
    matching_files = []
    dir_files = []
    ## Note:: with current behavior, if recurse, then code
    ## behaves as though full_names=True, regardless of how it's set.
    if recurse:
        for dirname, dirnames, filenames in os.walk('bioc-access-logs/s3'):
            for filename in filenames:
                dir_files.append(os.path.join(dirname, filename))
    else:
        dir_files = os.listdir(dir)
    for file in dir_files:
        if match_type == "match":
            m = p.match(file)
        else:
            m = p.search(file)
        if not m:
            continue
        if recurse:
            full_name = file
        else:
            full_name = os.path.join(dir, file)
        if not os.path.isfile(full_name):
            continue
        if full_names:
            matching_files.append(full_name)
        else:
            matching_files.append(file)
    return matching_files

def getLogFileDate(logfile):
    p = re.compile('(20[0-9][0-9])-?([0-1][0-9])-?([0-3][0-9])')
    m = p.search(logfile)
    if not m:
        sys.exit("Cannot get date for logfile '%s' ==> EXIT" % logfile)
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

### 'from_date' and 'to_date' must be None or datetime.date objects e.g.
### datetime.date(2009, 01, 10)
def selectLogFilesWithinDates(logfiles, from_date=None, to_date=None):
    if from_date == None:
        from_date = datetime.date(1, 1, 1)  # beginning of times
    if to_date == None:
        to_date = datetime.date(9999, 12, 31)  # end of times
    selected_files = []
    for logfile in logfiles:
        logfile_date = getLogFileDate(logfile)
        if logfile_date < from_date or logfile_date > to_date:
            continue
        selected_files.append(logfile)
    return selected_files

def get_access_logfiles(fmt, access_logdirs, get_logfiles_fun,
                        from_date=None, to_date=None):
    print 
    print "Preparing list of %s access logfiles to process:" % fmt
    files = []
    for dir in access_logdirs:
        print "| Scanning '%s' dir ..." % dir,
        logfiles = get_logfiles_fun(dir)
        print "OK"
        print "| ==> %s %s access logfiles found" % (len(logfiles), fmt)
        files.extend(logfiles)
    if from_date != None or to_date != None:
        print "Total: %s %s access logfiles found" % (len(files), fmt)
        print "Selecting files with dates within %s and %s ..." \
              % (from_date, to_date),
        files = selectLogFilesWithinDates(files, from_date, to_date)
        print "OK"
    print "Number of %s access logfiles to process: %s" % (fmt, len(files))
    files.sort(lambda x, y: cmp(getLogFileDate(x), getLogFileDate(y)))
    return files

def getSquidAccessLogFiles(from_date=None, to_date=None):
    def get_logfiles_fun(dir):
        return getMatchingFiles(dir, access_logfiles_regex, True)
    return get_access_logfiles("Squid",
                               stats_config.squid_access_logdirs,
                               get_logfiles_fun, from_date, to_date)

def getApache2AccessLogFiles(from_date=None, to_date=None):
    def get_logfiles_fun(dir):
        return getMatchingFiles(dir, access_logfiles_regex, True)
    return get_access_logfiles("Apache2",
                               stats_config.apache2_access_logdirs,
                               get_logfiles_fun, from_date, to_date)

def getCloudFrontAccessLogFiles(from_date=None, to_date=None):
    def get_logfiles_fun(dir):
        return getMatchingFiles(dir, "\.gz$", True, True, "search")
    return get_access_logfiles("CloudFront",
                               stats_config.s3_access_logdirs,
                               get_logfiles_fun, from_date, to_date)

def strHasBuildNodeIP(s):
    for ip in stats_config.buildnode_ips:
        if s.find(ip) != -1:
            return True
    return False


### ==========================================================================
### SQL low-level utilities
###

### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
### DB schema
###

access_log_col2type = {
  'ips': 'TEXT NOT NULL',
  'day_month_year': 'TEXT NOT NULL',
  'month_year': 'TEXT NOT NULL',
  'time': 'TEXT NOT NULL',
  'utc_offset': 'TEXT NOT NULL',
  'method': 'TEXT NOT NULL',
  'url': 'TEXT NOT NULL',
  'protocol': 'TEXT NOT NULL',
  'errorcode': 'TEXT NOT NULL',
  'bytes': 'INTEGER NULL',
  'referer': 'TEXT NULL',
  'user_agent': 'TEXT NULL',
  'biocrepo_relurl': 'TEXT NULL',
  'biocrepo': 'TEXT NULL',
  'biocversion': 'TEXT NULL',
  'package': 'TEXT NULL',
  'pkgversion': 'TEXT NULL',
  'pkgtype': 'TEXT NULL',
}

### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
### Making the DB.
###

def SQL_createDB(dbfile):
    if os.path.exists(dbfile):
        print 'Removing existing %s file ...' % dbfile
        os.remove(dbfile)
    return sqlite3.connect(dbfile)

def SQL_createAccessLogTable(c):
    sql = ''
    for colname in access_log_col2type.keys():
        if sql != '':
            sql += ', '
        sql += colname + ' ' + access_log_col2type[colname]
    sql = 'CREATE TABLE access_log (%s)' % sql
    c.execute(sql)
    return

def SQL_insertRow(c, tablename, col2val):
    cols = ','.join(col2val.keys())
    placeholders = []
    for val in col2val.values():
        placeholders.append('?')
    placeholders = ','.join(placeholders)
    sql = 'INSERT INTO %s (%s) VALUES (%s)' % (tablename, cols, placeholders)
    c.execute(sql, tuple(col2val.values()))
    return sql

### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
### Querying the DB.
###

def SQL_connectToDB(dbfile):
    if not os.path.exists(dbfile):
        print '%s file not found. Did you run makeDownloadDbs.sh?' % dbfile
        sys.exit("==> EXIT")
    return sqlite3.connect(dbfile)

def SQL_globalFilter():
    date_is_in_range = "month_year IN ('%s')" % \
                       "','".join(stats_config.lastmonths)
    global_filter = date_is_in_range
    return global_filter

def SQL_getDistinctPackages(c, biocrepo='bioc'):
    sql = "SELECT DISTINCT package FROM access_log WHERE biocrepo='%s' AND %s" \
        % (biocrepo, SQL_globalFilter())
    c.execute(sql)
    pkgs = []
    for row in c:
        pkgs.append(str(row[0]))
    #pkgs.sort(lambda u, v: cmp(string.lower(u), string.lower(v)))
    return pkgs

def SQL_getDistinctPackages_for_year(c, biocrepo, year):
    sql = "SELECT DISTINCT package FROM access_log " + \
          "WHERE biocrepo='%s' AND month_year LIKE '%%/%s'" % (biocrepo, year)
    c.execute(sql)
    pkgs = []
    for row in c:
        pkgs.append(str(row[0]))
    #pkgs.sort(lambda u, v: cmp(string.lower(u), string.lower(v)))
    return pkgs

def SQL_countDownloadsPerMonth(c, sql_where):
    print 'Counting downloads-per-month for "%s" ...' % sql_where,
    sys.stdout.flush()
    sql = "SELECT month_year, count(*) FROM access_log" \
        + " WHERE (%s) AND (%s)" % (SQL_globalFilter(), sql_where) \
        + " GROUP BY month_year"
    c.execute(sql)
    month_to_C = {}
    for month in stats_config.lastmonths:
        month_to_C[month] = 0
    for row in c:
        month = row[0]
        if month in month_to_C.keys():
            month_to_C[month] = row[1]
    print 'OK'
    return month_to_C

def SQL_countDownloadsPerMonthOfYear(c, sql_where, year):
    print 'Counting downloads-per-month for "%s" and year %s ...' \
          % (sql_where, year),
    sys.stdout.flush()
    sql = "SELECT month_year, count(*) FROM access_log" \
        + " WHERE (%s) AND month_year LIKE '%%/%s'" % (sql_where, year) \
        + " GROUP BY month_year"
    c.execute(sql)
    month_to_C = {}
    for m in range(1, 13):
        month = datetime.date(year, m, 1).strftime('%b/%Y')
        month_to_C[month] = 0
    for row in c:
        month = row[0]
        if month in month_to_C.keys():
            month_to_C[month] = row[1]
    print 'OK'
    return month_to_C

def SQL_countIPsPerMonth(c, sql_where):
    print 'Counting distinct IPs-per-month for "%s" ...' % sql_where,
    sys.stdout.flush()
    sql = "SELECT month_year, count(DISTINCT ips) FROM access_log" \
        + " WHERE (%s) AND (%s)" % (SQL_globalFilter(), sql_where) \
        + " GROUP BY month_year"
    c.execute(sql)
    month_to_C = {}
    for month in stats_config.lastmonths:
        month_to_C[month] = 0
    for row in c:
        month = row[0]
        if month in month_to_C.keys():
            month_to_C[month] = row[1]
    print 'OK'
    return month_to_C

def SQL_countIPsPerMonthOfYear(c, sql_where, year):
    print 'Counting distinct IPs-per-month for "%s" and year %s ...' \
          % (sql_where, year),
    sys.stdout.flush()
    sql = "SELECT month_year, count(DISTINCT ips) FROM access_log" \
        + " WHERE (%s) AND month_year LIKE '%%/%s'" % (sql_where, year) \
        + " GROUP BY month_year"
    c.execute(sql)
    month_to_C = {}
    for m in range(1, 13):
        month = datetime.date(year, m, 1).strftime('%b/%Y')
        month_to_C[month] = 0
    for row in c:
        month = row[0]
        if month in month_to_C.keys():
            month_to_C[month] = row[1]
    print 'OK'
    return month_to_C

def SQL_countIPs(c, sql_where):
    print 'Counting distinct IPs for "%s" ...' % sql_where,
    sys.stdout.flush()
    sql = "SELECT count(DISTINCT ips) FROM access_log" \
        + " WHERE (%s) AND (%s)" % (SQL_globalFilter(), sql_where)
    c.execute(sql)
    for row in c:
        print 'OK'
        return row[0]

def SQL_countIPsForYear(c, sql_where, year):
    print 'Counting distinct IPs for "%s" and year %s ...' \
          % (sql_where, year),
    sys.stdout.flush()
    sql = "SELECT count(DISTINCT ips) FROM access_log" \
        + " WHERE (%s) AND month_year LIKE '%%/%s'" % (sql_where, year)
    c.execute(sql)
    for row in c:
        print 'OK'
        return row[0]

def SQL_countDownloadsPerIP(c, sql_where):
    print 'Counting downloads-per-IP for "%s" ...' % sql_where,
    sys.stdout.flush()
    sql = "SELECT ips, count(*) FROM access_log" \
        + " WHERE (%s) AND (%s)" % (SQL_globalFilter(), sql_where) \
        + " GROUP BY ips"
    c.execute(sql)
    ip_to_C = {}
    for row in c:
        ip_to_C[row[0]] = row[1]
    print 'OK'
    return ip_to_C


### ==========================================================================
### Extract the stats from the DB.
###

def extract_stats_for_year(c, year_stats_filepath, sql_where, year):
    month_to_C1 = SQL_countIPsPerMonthOfYear(c, sql_where, year)
    allmonths_c1 = SQL_countIPsForYear(c, sql_where, year)
    month_to_C2 = SQL_countDownloadsPerMonthOfYear(c, sql_where, year)
    out = open(year_stats_filepath, 'w')
    out.write('%s\t%s\t%s\t%s\n' \
              % ("Year", "Month", "Nb_of_distinct_IPs", "Nb_of_downloads"))
    allmonths_c2 = 0
    for m in range(1, 13):
        d = datetime.date(year, m, 1)
        month = d.strftime('%b')
        key = '%s/%s' % (month, year)
        c1 = month_to_C1[key]
        c2 = month_to_C2[key]
        out.write('%s\t%s\t%s\t%s\n' % (year, month, c1, c2))
        allmonths_c2 += c2
    out.write('%s\t%s\t%s\t%s\n' % (year, "all", allmonths_c1, allmonths_c2))
    out.close()
    return

def extract_biocrepo_stats_for_year(c, biocrepo, year):
    year_stats_filepath = '%s_%s_stats.tab' % (biocrepo, year)
    sql_where = "biocrepo='%s'" % biocrepo
    extract_stats_for_year(c, year_stats_filepath, sql_where, year)
    return

def extract_package_stats_for_year(c, biocrepo, pkg, year):
    year_stats_filepath = '%s_%s_stats.tab' % (pkg, year)
    sql_where = "biocrepo='%s' AND package='%s'" % (biocrepo, pkg)
    extract_stats_for_year(c, year_stats_filepath, sql_where, year)
    return

def extract_all_stats_for_year(c, biocrepo, year):
    extract_biocrepo_stats_for_year(c, biocrepo, year)
    packages_filepath = '%s_packages.txt' % biocrepo
    packages = open(packages_filepath, 'aw')
    pkgs = SQL_getDistinctPackages_for_year(c, biocrepo, year)
    for pkg in pkgs:
        if not os.path.exists(pkg):
            os.mkdir(pkg)
            packages.write('%s\n' % pkg)
        os.chdir(pkg)
        extract_package_stats_for_year(c, biocrepo, pkg, year)
        os.chdir('..')
    packages.close()
    return

def load_package_list(packages_filepath):
    if not os.path.exists(packages_filepath):
        print '%s file not found. Did you run extractDownloadStats*.sh?' \
              % packages_filepath
        sys.exit("==> EXIT")
    packages = open(packages_filepath, 'r')
    pkgs = []
    for line in packages:
        pkgs.append(line.strip())
    packages.close()
    return pkgs

def append_package_stats_for_year(out, pkg, year, write_header):
    year_stats_filepath = '%s_%s_stats.tab' % (pkg, year)
    if not os.path.exists(year_stats_filepath):
        return write_header
    year_stats = open(year_stats_filepath, 'r')
    regex = '^([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)$'
    p = re.compile(regex)
    lineno = 0
    for line in year_stats:
        lineno += 1
        m = p.match(line.strip())
        y = m.group(1)
        month = m.group(2)
        c1 = m.group(3)
        c2 = m.group(4)
        if lineno == 1:
            if y != 'Year' or month != 'Month' or \
               c1 != 'Nb_of_distinct_IPs' or c2 != 'Nb_of_downloads':
                sys.exit("Unexpected header in %s ==> EXIT" \
                         % year_stats_filepath)
            if write_header:
                out.write(line)
                write_header = False
            continue
        if y != str(year):
            sys.exit("Unexpected year found in %s ==> EXIT" \
                     % year_stats_filepath)
        out.write(line)
    year_stats.close()
    return write_header

def make_package_stats_file(pkg, from_year, to_year):
    pkg_stats_filepath = '%s_stats.tab' % pkg
    pkg_stats = open(pkg_stats_filepath, 'w')
    write_header = True
    year = to_year
    while year >= from_year:
        write_header = append_package_stats_for_year(pkg_stats,
                                                     pkg, year,
                                                     write_header)
        year -= 1
    pkg_stats.close()
    return

def make_biocrepo_stats_file(biocrepo, from_year, to_year):
    print 'Make %s repo all-year stats file ...' % biocrepo,
    biocrepo_stats_filepath = '%s_stats.tab' % biocrepo
    biocrepo_stats = open(biocrepo_stats_filepath, 'w')
    write_header = True
    year = to_year
    while year >= from_year:
        write_header = append_package_stats_for_year(biocrepo_stats,
                                                     biocrepo, year,
                                                     write_header)
        year -= 1
    biocrepo_stats.close()
    print 'OK'
    return

def make_package_stats_files(biocrepo, from_year, to_year):
    print 'Make package all-year stats files ...',
    packages_filepath = '%s_packages.txt' % biocrepo
    pkgs = load_package_list(packages_filepath)
    for pkg in pkgs:
        os.chdir(pkg)
        make_package_stats_file(pkg, from_year, to_year)
        os.chdir('..')
    print 'OK'
    return

def make_allpkg_stats_file(allpkg_stats_filepath, biocrepo):
    print 'Make all-package stats file ...',
    packages_filepath = '%s_packages.txt' % biocrepo
    pkgs = load_package_list(packages_filepath)
    allpkg_stats = open(allpkg_stats_filepath, 'w')
    pkgno = 0
    for pkg in pkgs:
        pkgno += 1
        pkg_stats_filename = '%s_stats.tab' % pkg
        pkg_stats_filepath = os.path.join(pkg, pkg_stats_filename)
        pkg_stats = open(pkg_stats_filepath, 'r')
        lineno = 0
        for line in pkg_stats:
            lineno += 1
            if lineno == 1:
                if pkgno == 1:
                    allpkg_stats.write('%s\t%s' % ('Package', line))
                continue
            allpkg_stats.write('%s\t%s' % (pkg, line))
        pkg_stats.close()        
    allpkg_stats.close()
    print 'OK'
    return

## The package download score is the average nb of distinct IPs over the last
## 12 *completed* months.
def compute_package_download_score(pkg_stats_filepath, today):
    pkg_stats = open(pkg_stats_filepath, 'r')
    current_year = today.year
    current_month = today.month
    score = 0
    regex = '^([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)$'
    p = re.compile(regex)
    lineno = 0
    for line in pkg_stats:
        lineno += 1
        m = p.match(line.strip())
        y = m.group(1)
        month = m.group(2)
        c1 = m.group(3)
        c2 = m.group(4)
        if lineno == 1:
            if y != 'Year' or month != 'Month' or \
               c1 != 'Nb_of_distinct_IPs' or c2 != 'Nb_of_downloads':
                sys.exit("Unexpected header in %s ==> EXIT" \
                         % pkg_stats_filepath)
            continue
        if month == 'all':
            continue
        year = int(y)
        ## Replace month name with month number
        month = datetime.datetime.strptime(month, '%b').month
        if year == current_year and month < current_month or \
           year == current_year - 1 and month >= current_month:
            score += int(c1)
    pkg_stats.close()
    return int(math.ceil(score / 12.0))

def make_allpkg_scores_file(allpkg_scores_filepath, biocrepo):
    print 'Make all-package scores file ...',
    packages_filepath = '%s_packages.txt' % biocrepo
    pkgs = load_package_list(packages_filepath)
    allpkg_scores = open(allpkg_scores_filepath, 'w')
    allpkg_scores.write('%s\t%s\n' % ("Package", "Download_score"))
    today = datetime.date.today()
    for pkg in pkgs:
        pkg_stats_filename = '%s_stats.tab' % pkg
        pkg_stats_filepath = os.path.join(pkg, pkg_stats_filename)
        score = compute_package_download_score(pkg_stats_filepath, today)
        allpkg_scores.write('%s\t%s\n' % (pkg, score))
    allpkg_scores.close()
    print 'OK'
    return

def load_pkg2score(allpkg_scores_filepath):
    allpkg_scores = open(allpkg_scores_filepath, 'r')
    pkg2score = {}
    regex = '^([^\t]*)\t([^\t]*)$'
    p = re.compile(regex)
    lineno = 0
    for line in allpkg_scores:
        lineno += 1
        m = p.match(line.strip())
        pkg = m.group(1)
        score = m.group(2)
        if lineno == 1:
            if pkg != 'Package' or score != 'Download_score':
                sys.exit("Unexpected header in %s ==> EXIT" \
                         % allpkg_scores_filepath)
            continue
        pkg2score[pkg] = int(score)
    allpkg_scores.close()
    return pkg2score


### ==========================================================================
### Make HTML report.
###

def write_top_asHTML(out, title, css_file):
    out.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"')
    out.write(' "http://www.w3.org/TR/html4/loose.dtd">\n')
    out.write('<HTML>\n')
    out.write('<HEAD>')
    out.write('<TITLE>%s</TITLE>' % title)
    out.write('<LINK rel="stylesheet" href="%s" type="text/css">' % css_file)
    out.write('</HEAD>\n')
    return

def write_topright_links_asHTML(out, href1, text1, href2, text2, href3, text3):
    out.write('<TABLE style="width: 100%; border-spacing: 0px; ')
    out.write('border-collapse: collapse;"><TR>')
    out.write('<TD style="padding: 0px; text-align: right;">')
    out.write('<I><A HREF="%s">%s</A></I>' % (href1, text1))
    out.write('&nbsp;&nbsp;&nbsp;&nbsp;')
    out.write('<I><A HREF="%s">%s</A></I>' % (href2, text2))
    out.write('&nbsp;&nbsp;&nbsp;&nbsp;')
    out.write('<I><A HREF="%s">%s</A></I>' % (href3, text3))
    out.write('</TD>')
    out.write('</TR></TABLE>\n')
    return

def write_goback_asHTML(out, href, index_page_title):
    out.write('<TABLE style="width: 100%; border-spacing: 0px; border-collapse: collapse;"><TR>')
    out.write('<TD style="padding: 0px; text-align: left;">')
    out.write('<I><A HREF="%s">Back to the &quot;%s&quot;</A></I>' \
              % (href, index_page_title))
    out.write('</TD>')
    out.write('</TR></TABLE>\n')
    return

# 'tm' must be a <type 'time.struct_time'> object as returned by
# time.localtime(). See http://docs.python.org/lib/module-time.html
# for more info.
# Example:
#   >>> dateString(time.localtime())
#   '2007-12-07 10:03:15 -0800 (Fri, 07 Dec 2007)'
# Note that this is how 'svn log' and 'svn info' format the dates.
def dateString(tm):
    if tm.tm_isdst:
        utc_offset = time.altzone # 7 hours in Seattle
    else:
        utc_offset = time.timezone # 8 hours in Seattle
    utc_offset /= 3600
    format = "%%Y-%%m-%%d %%H:%%M:%%S -0%d00 (%%a, %%d %%b %%Y)" % utc_offset
    return time.strftime(format, tm)

def currentDateString():
    return dateString(time.localtime())

def write_timestamp_asHTML(out):
    out.write('<P style="text-align: center;">\n')
    out.write('<I>This page was generated on %s.</I>\n' % currentDateString())
    out.write('</P>\n')
    return

def get_link_to_package_home(pkg, biocversion):
    for biocrepo in ['bioc', 'data/annotation', 'data/experiment', 'workflows']:
        url = 'http://bioconductor.org/packages/%s/%s/html/%s.html' % \
              (biocversion, biocrepo, pkg)
        try:
            urllib2.urlopen(url)
        except urllib2.HTTPError:
            continue
        return url
    return None

def write_links_to_package_home(out, pkg):
    url1 = get_link_to_package_home(pkg, "release")
    url2 = get_link_to_package_home(pkg, "devel")
    out.write('<P style="text-align: center;">')
    if url1 == None and url2 == None:
        out.write('Note that <B>%s</B> doesn\'t belong to the ' % pkg)
        out.write('current release or devel version of Bioconductor anymore.')
        out.write('</P>\n')
        return
    out.write('<B>%s</B> home page: ' % pkg)
    if url1 != None:
        out.write('<A HREF="%s">release version</A>' % url1)
    if url2 != None:
        if url1 != None:
            out.write(', ')
        out.write('<A HREF="%s">devel version</A>' % url2)
    out.write('.</P>\n')
    return

def make_barplot2ylog(title, barplot_filepath, barlabels,
                      barlabel_to_C1, C1_label, C1_color,
                      barlabel_to_C2, C2_label, C2_color, Cmax=None):
    c1_vals = []
    c2_vals = []
    Cmax0 = 0
    for label in barlabels:
        C1 = barlabel_to_C1[label]
        if C1 > Cmax0:
            Cmax0 = C1
        c1_vals.append(math.log10(1 + C1))
        C2 = barlabel_to_C2[label]
        if C2 > Cmax0:
            Cmax0 = C2
        c2_vals.append(math.log10(1 + C2))
    pylab.clf()
    xtickat = pylab.arange(len(c1_vals)) + 0.5
    width = 0.40  # the width of the bars
    rects1 = pylab.bar(xtickat - width, c1_vals, width, color=C1_color)
    rects2 = pylab.bar(xtickat,         c2_vals, width, color=C2_color)
    xlabels = []
    for i in range(0, len(barlabels)):
        if i % 3 != 2:
            label = ''
        else:
            label = barlabels[i]
        xlabels.append(label)
    pylab.xticks(xtickat, xlabels)
    if Cmax == None:
        Cmax = Cmax0
    if Cmax < 100:
        nb_pow10ticks = 3
    else:
        nb_pow10ticks = int(math.log10(Cmax)) + 2
    ytickat = [0]
    ylabels = ['0']
    for i in range(0, nb_pow10ticks):
        at = 10 ** i
        y = math.log10(1 + at)
        ytickat.append(y)
        ylabels.append(str(at))
        if i < nb_pow10ticks - 1:
            pylab.axhline(y, color='black', alpha=0.16)
            for j in range(1, 10):
                y = math.log10(1 + j * at)
                ytickat.append(y)
                if nb_pow10ticks <= 6 and (j == 2 or j == 5):
                    ylabel = str(j *at)
                else:
                    ylabel = ''
                ylabels.append(ylabel)
                pylab.axhline(y, color='black', alpha=0.08)
    pylab.yticks(ytickat, ylabels)
    pylab.title(title)
    pylab.legend((rects1[0], rects2[0]), (C1_label, C2_label), loc=8)
    pylab.savefig(barplot_filepath, format='png')
    return

def write_HTML_stats_TABLE(out, months,
                           month_to_C1, C1_label, C1_color,
                           month_to_C2, C2_label, C2_color,
                           allmonths_label, allmonths_c1, allmonths_c2=None):
    C1_style = 'style="text-align: right; background: %s"' % C1_color
    C2_style = 'style="text-align: right; background: %s"' % C2_color
    out.write('<TABLE class="stats" align="center">\n')
    out.write('<TR>')
    out.write('<TH style="text-align: right">Month</TH>')
    out.write('<TH %s>%s</TH>' % (C1_style, C1_label))
    out.write('<TH %s>%s</TH>' % (C2_style, C2_label))
    out.write('</TR>\n')
    sum2 = 0
    for month in months:
        c1 = month_to_C1[month]
        c2 = month_to_C2[month]
        sum2 += c2
        out.write('<TR>')
        out.write('<TD style="text-align: right">%s</TD>' % month)
        out.write('<TD %s>%d</TD>' % (C1_style, c1))
        out.write('<TD %s>%d</TD>' % (C2_style, c2))
        out.write('</TR>\n')
    if allmonths_c2 == None:
        allmonths_c2 = sum2
    elif allmonths_c2 != sum2:
        sys.exit("allmonths_c2 != sum2 ==> EXIT")
    out.write('<TR>')
    out.write('<TH style="text-align: right">%s</TH>' % allmonths_label)
    out.write('<TH %s>%d</TH>' % (C1_style, allmonths_c1))
    out.write('<TH %s>%d</TH>' % (C2_style, allmonths_c2))
    out.write('</TR>\n')
    out.write('</TABLE>\n')
    return

def write_HTML_stats_for_year(out, pkg, year):
    year_stats_filepath = '%s_%s_stats.tab' % (pkg, year)
    if not os.path.exists(year_stats_filepath):
        return
    out.write('<H2 style="text-align: center;">%s</H2>\n' % year)
    year_stats = open(year_stats_filepath, 'r')
    months = []
    month_to_C1 = {}
    month_to_C2 = {}
    regex = '^([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)$'
    p = re.compile(regex)
    lineno = 0
    for line in year_stats:
        lineno += 1
        m = p.match(line.strip())
        y = m.group(1)
        month = m.group(2)
        c1 = m.group(3)
        c2 = m.group(4)
        if lineno == 1:
            if y != 'Year' or month != 'Month' or \
               c1 != 'Nb_of_distinct_IPs' or c2 != 'Nb_of_downloads':
                sys.exit("Unexpected header in %s ==> EXIT" \
                         % year_stats_filepath)
            continue
        if y != str(year):
            sys.exit("Unexpected year found in %s ==> EXIT" \
                     % year_stats_filepath)
        c1 = int(c1)
        c2 = int(c2)
        key = '%s/%s' % (month, year)
        if month == 'all':
            allmonths_c1 = c1
            allmonths_c2 = c2
        else:
            months.append(key)
            month_to_C1[key] = c1
            month_to_C2[key] = c2
    year_stats.close()
    C1_color = '#8888ff'
    C2_color = '#ddddff'
    barplot_filepath = '%s_%s_stats.png' % (pkg, year)
    make_barplot2ylog('%s %s' % (pkg, year), barplot_filepath, months,
                      month_to_C1, 'Nb of distinct IPs', C1_color,
                      month_to_C2, 'Nb of downloads', C2_color)
    #out.write('<P style="text-align: center">\n')
    out.write('<TABLE WIDTH="90%" align="center"><TR>\n')
    out.write('<TD style="text-align: center">')
    out.write('<IMG SRC="%s" WIDTH="520px" HEIGHT="390px">' % barplot_filepath)
    out.write('</TD>')
    out.write('<TD style="text-align: center">')
    write_HTML_stats_TABLE(out, months,
        month_to_C1, 'Nb&nbsp;of&nbsp;distinct&nbsp;IPs', C1_color,
        month_to_C2, 'Nb&nbsp;of&nbsp;downloads', C2_color,
        year, allmonths_c1, allmonths_c2)
    out.write('<A HREF="%s">%s</A>' \
              % (year_stats_filepath, year_stats_filepath))
    out.write('</TD>')
    out.write('</TR></TABLE>\n')
    #out.write('</P>\n')
    return

def make_package_HTML_report(pkg, biocrepo, from_year, to_year,
                             index_page_href, index_page_title):
    print 'Make download stats HTML report for package %s ...' % pkg,
    sys.stdout.flush()
    package_page = 'index.html'
    out = open(package_page, 'w')
    biocrepo_label = stats_config.biocrepo2label[biocrepo]
    title = 'Download stats for %s package %s' % (biocrepo_label, pkg)
    write_top_asHTML(out, title, '../../main.css')
    out.write('<BODY>\n')
    write_goback_asHTML(out, index_page_href, index_page_title)
    out.write('<H1 style="text-align: center;">%s</H1>\n' % title)
    write_timestamp_asHTML(out)
    write_links_to_package_home(out, pkg)
    out.write('<P style="text-align: center">')
    out.write('Number of downloads ')
    out.write('for %s package %s, ' % (biocrepo_label, pkg))
    out.write('year by year, from %s back to %s ' % (to_year, from_year))
    out.write('(years with no downloads are omitted):')
    out.write('</P>\n')
    year = to_year
    while year >= from_year:
        write_HTML_stats_for_year(out, pkg, year)
        year -= 1
    out.write('<P style="text-align: center">')
    out.write('All years in one file:&nbsp;')
    pkg_stats_filepath = '%s_stats.tab' % pkg
    out.write('<A HREF="%s">%s</A>' \
              % (pkg_stats_filepath, pkg_stats_filepath))
    out.write('</P>\n')
    out.write('</BODY>\n')
    out.write('</HTML>\n')
    out.close()
    print 'OK'
    sys.stdout.flush()
    return

## So old URLs like https://bioconductor.org/packages/stats/bioc/pathview.html
## still work.
def make_redirect_page_from_old_to_new_package_HTML_report(pkg, biocrepo):
    package_page = '%s.html' % pkg
    out = open(package_page, 'w')
    biocrepo_subdir = stats_config.biocrepo2subdir[biocrepo]
    biocrepo_label = stats_config.biocrepo2label[biocrepo]
    title = 'Download stats for %s package %s' % (biocrepo_label, pkg)
    write_top_asHTML(out, title, '../main.css')
    out.write('<BODY>\n')
    out.write('<P>')
    out.write('Sorry, this page has moved to ')
    new_url = 'https://bioconductor.org/packages/stats/%s/%s/' \
              % (biocrepo_subdir, pkg)
    out.write('<A HREF="%s">%s</A>' % (new_url, new_url))
    out.write('</P>\n')
    out.write('<P>Please update your bookmarks.</P>\n')
    out.write('<P>Thanks!</P>\n')
    out.write('</BODY>\n')
    out.write('</HTML>\n')
    out.close()
    return

def make_biocrepo_HTML_report(biocrepo_page, biocrepo_page_title,
                              biocrepo, from_year, to_year,
                              index_page_href, index_page_title):
    print 'Make download stats HTML report for %s repo ...' % biocrepo,
    sys.stdout.flush()
    out = open(biocrepo_page, 'w')
    write_top_asHTML(out, biocrepo_page_title, '../main.css')
    out.write('<BODY>\n')
    write_goback_asHTML(out, index_page_href, index_page_title)
    out.write('<H1 style="text-align: center">%s</H1>\n' % biocrepo_page_title)
    write_timestamp_asHTML(out)
    biocrepo_label = stats_config.biocrepo2label[biocrepo]
    out.write('<P style="text-align: center">')
    out.write('Number of package downloads from the ')
    out.write('Bioconductor %s package repository, ' % biocrepo_label)
    out.write('year by year, from %s back to %s ' % (to_year, from_year))
    out.write('(years with no downloads are omitted):')
    out.write('</P>\n')
    year = to_year
    while year >= from_year:
        write_HTML_stats_for_year(out, biocrepo, year)
        year -= 1
    out.write('<P style="text-align: center">')
    out.write('All years in one file:&nbsp;')
    biocrepo_stats_filepath = '%s_stats.tab' % biocrepo
    out.write('<A HREF="%s">%s</A>' \
              % (biocrepo_stats_filepath, biocrepo_stats_filepath))
    out.write('</P>\n')
    out.write('</BODY>\n')
    out.write('</HTML>\n')
    out.close()
    print 'OK'
    sys.stdout.flush()
    return

def make_package_HTML_reports(biocrepo, from_year, to_year,
                              index_page_href, index_page_title):
    packages_filepath = '%s_packages.txt' % biocrepo
    pkgs = load_package_list(packages_filepath)
    for pkg in pkgs:
        os.chdir(pkg)
        make_package_HTML_report(pkg, biocrepo, from_year, to_year,
                                 index_page_href, index_page_title)
        os.chdir('..')
        make_redirect_page_from_old_to_new_package_HTML_report(pkg, biocrepo)
    return

def write_HTML_package_index(out, biocrepo, pkgs, pkg2score, n=None):
    if n == None:
        pkgs.sort(lambda u, v: cmp(string.lower(u), string.lower(v)))
    else:
        pkgs.sort(lambda u, v: pkg2score[v] - pkg2score[u])
        pkgs = pkgs[0:n]
    ncol = 3
    nrow = (len(pkgs) + ncol - 1) / ncol
    out.write('<TABLE class="pkg_index"><TR>\n')
    for j in range(ncol):
        out.write('<TD style="vertical-align: top; width:300px;">\n')
        if j * nrow < len(pkgs):
            out.write('<TABLE>\n')
            for i in range(nrow):
                p = j * nrow + i
                if p >= len(pkgs):
                    break
                out.write('<TR class="pkg_index">')
                out.write('<TD style="width:25px; text-align: right">')
                if n != None:
                    out.write(str(p + 1))
                out.write('</TD>')
                pkgname_html = pkg = pkgs[p]
                biocrepo_subdir = stats_config.biocrepo2subdir[biocrepo]
                package_page_href = '%s/%s/' % (biocrepo_subdir, pkg)
                if pkg in stats_config.bioclite_pkgs:
                    pkgname_html = '<B>%s</B>' % pkgname_html
                out.write('<TD><A HREF="%s">%s&nbsp;(%d)</A></TD>' % \
                          (package_page_href, pkgname_html, pkg2score[pkg]))
                out.write('</TR>\n')
            out.write('</TABLE>\n')
        out.write('</TD>\n')
    out.write('</TR></TABLE>\n')
    return

def write_HTML_top_packages(out, biocrepo, allpkg_scores_filepath, n):
    pkg2score = load_pkg2score(allpkg_scores_filepath)
    pkgs = pkg2score.keys()
    write_HTML_package_index(out, biocrepo, pkgs, pkg2score, n)

def write_HTML_package_alphabetical_index(out, biocrepo,
                                          allpkg_scores_filepath):
    pkg2score = load_pkg2score(allpkg_scores_filepath)
    pkgs = pkg2score.keys()
    letter2pkgs = {}
    ## Packages are grouped by first letter
    for pkg in pkgs:
        first_letter = pkg[0].upper()
        if letter2pkgs.has_key(first_letter):
            letter2pkgs[first_letter].append(pkg)
        else:
            letter2pkgs[first_letter] = [pkg]
    ## Write stats for each group
    letters = letter2pkgs.keys()
    letters.sort(lambda u, v: cmp(string.lower(u), string.lower(v)))
    for letter in letters:
        out.write('<H3 style="font-family: monospace; font-size: larger;">%s</H3>\n' % letter)
        write_HTML_package_index(out, biocrepo, letter2pkgs[letter], pkg2score)
    return

