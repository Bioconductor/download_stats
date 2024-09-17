#!/usr/bin/env python3

from time import localtime, strftime
import os

## Code migrated from boto to boto3 on Sep 17, 2024.
## Make sure AWS credentials are in ~/.aws/config
import boto3
#import warnings
#with warnings.catch_warnings():
#    warnings.simplefilter("ignore")
#    from boto.s3.connection import S3Connection

#from boto.s3.bucket import Bucket


start = strftime("%Y-%m-%d %H:%M:%S", localtime())
print("get_s3_logs.py starting at %s" % start)


print("Getting bucket object....")

#import configparser
#config = configparser.RawConfigParser()
#config.read('aws.cfg')
#access_key = config.get('aws_credentials', 'access_key')
#secret_key = config.get('aws_credentials', 'secret_key')
#conn = S3Connection(access_key, secret_key)
#b = conn.get_bucket("bioc-cloudfront-logs")

b = boto3.resource('s3').Bucket('bioc-cloudfront-logs')

downloadcount = 0

print("Iterating through bucket list...")

## Original code based on boto.
#for key in b.list():
#    name = key.name
#    segs = name.split(".")
#    segs2 = segs[1].split("-")
#    segs2.pop()
#    date = "-".join(segs2)
#    destdir = "bioc-access-logs/s3/%s" % date
#    if not os.path.exists(destdir):
#        print("Creating directory %s." % destdir)
#        os.mkdir(destdir)
#    destfile = "%s/%s" % (destdir, name)
#    if not os.path.exists(destfile):
#        key.get_contents_to_filename("%s/%s" % (destdir, name))
#        if (downloadcount > 0 and downloadcount % 50 == 0):
#            print("Count of downloaded log files: %s" % downloadcount)
#        downloadcount += 1

## New code based on boto3.
#for obj in b.objects.all():
for obj in b.objects.all():
    name = obj.key
    segs = name.split(".")
    segs2 = segs[1].split("-")
    ignored = segs2.pop()
    date = "-".join(segs2)
    destdir = "bioc-access-logs/s3/%s" % date
    if not os.path.exists(destdir):
        print("Creating directory %s." % destdir)
        os.mkdir(destdir)
    destfile = "%s/%s" % (destdir, name)
    if not os.path.exists(destfile):
        print('Downloading %s to %s ... ' % (name, destfile), end=' ')
        b.download_file(name, destfile)
        print('ok')
        downloadcount += 1
        if (downloadcount % 50 == 0):
            print('Count of downloaded log files: %d' % downloadcount)

print("Total files downloaded: %s." % downloadcount)
end = strftime("%Y-%m-%d %H:%M:%S", localtime())
print("get_s3_logs.py end at %s" % end)

