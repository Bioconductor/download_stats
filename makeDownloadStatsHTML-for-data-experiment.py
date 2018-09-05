#! /usr/bin/env python
#

import os
import datetime

import stats_config
import stats_utils

html_stats_home = '/home/biocadmin/public_html/stats'
biocrepo = 'experiment'
from_year = 2009
to_year = datetime.date.today().year  # current year

biocrepo_subdir = stats_config.biocrepo2subdir[biocrepo]
biocrepo_label = stats_config.biocrepo2label[biocrepo]

index_page = '%s.html' % biocrepo_subdir
index_page_title = 'Download stats for Bioconductor %s packages' \
                   % biocrepo_label

biocrepo_page = 'index.html'
biocrepo_page_title = 'Download stats for Bioconductor %s repository' \
                      % biocrepo_label

biocrepo_dirpath = os.path.join(html_stats_home, biocrepo_subdir)
allpkg_stats_filename = '%s_pkg_stats.tab' % biocrepo
allpkg_scores_filename = '%s_pkg_scores.tab' % biocrepo

def makeDownloadStatsHTML():
    os.chdir(biocrepo_dirpath)

    stats_utils.make_package_HTML_reports(biocrepo, from_year, to_year,
                                          '../../%s' % index_page,
                                          index_page_title)

    stats_utils.make_biocrepo_HTML_report(biocrepo_page, biocrepo_page_title,
                                          biocrepo, from_year, to_year,
                                          '../%s' % index_page,
                                          index_page_title)

    ## ------ Make the index page ------ ##

    out = open(os.path.join('..', index_page), 'w')
    stats_utils.write_top_asHTML(out, index_page_title, 'main.css')
    out.write('<BODY>\n')

    stats_utils.write_topright_links_asHTML(out,
        'index.html',
        'Bioconductor software packages',
        'data-annotation.html',
        'Bioconductor annotation packages',
        'workflows.html',
        'Bioconductor workflow packages')

    out.write('<H1 style="text-align: center;">%s</H1>\n' % index_page_title)
    stats_utils.write_timestamp_asHTML(out)

    #out.write('<P style="text-align: center">')
    out.write('<P>')
    out.write('The number reported next to each package name is the ')
    out.write('<I>download score</I>, that is, the average number of ')
    out.write('distinct IPs that &ldquo;hit&rdquo; the package each month ')
    out.write('for the last 12 months (not counting the current month). ')
    out.write('</P>\n')

    out.write('<HR>\n')

    ## Top 15.
    out.write('<H2>%s</H2>\n' % 'Top 15')

    stats_utils.write_HTML_top_packages(out, biocrepo,
                                        allpkg_scores_filename, 15)

    out.write('<HR>\n')

    ## All experiment packages.
    out.write('<H2>All %s packages</H2>' % biocrepo_label)

    #out.write('<P style="text-align: center">')
    out.write('<P>')
    out.write('All %s package stats in one file:&nbsp;' % biocrepo_label)
    out.write('<A HREF="%s/%s">%s</A>' \
              % (biocrepo_subdir, allpkg_stats_filename,
                 allpkg_stats_filename))
    out.write('</P>\n')

    #out.write('<P style="text-align: center">')
    out.write('<P>')
    out.write('All %s package download scores in one file:&nbsp;' \
              % biocrepo_label)
    out.write('<A HREF="%s/%s">%s</A>' \
              % (biocrepo_subdir, allpkg_scores_filename,
                 allpkg_scores_filename))
    out.write('</P>\n')

    biocrepo_page_href = '%s/%s' % (biocrepo_subdir, biocrepo_page)
    out.write('<P style="text-align: center"><A HREF="%s">%s</A></P>\n' \
              % (biocrepo_page_href, biocrepo_page_title))

    stats_utils.write_HTML_package_alphabetical_index(out, biocrepo,
                                                      allpkg_scores_filename)

    out.write('</BODY>\n')
    out.write('</HTML>\n')
    out.close()
    return

makeDownloadStatsHTML()

