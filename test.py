import os, re, urllib2, time, datetime, operator, sys, gzip, tinyurl

contents = "empty"
bad_files = []
good_files = []

url = "http://thewirecutter.com/"

req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
try:
    resp = urllib2.urlopen(req)
    good_files.append(url)
except urllib2.HTTPError, e:
    print e.code
    bad_files.append(url)

for b in bad_files:
    print "bad: " + b

for g in good_files:
    print "good: " + g