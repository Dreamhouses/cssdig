import os, re, urllib2, time, datetime, operator, sys, gzip, tinyurl

contents = "empty"
bad_files = []
good_files = []

url = "https://ssl.typography.com/652324/768840/css/fonts.css"

req = urllib2.Request(url)
try:
    resp = urllib2.urlopen(req)
    good_files.append(url)
except urllib2.HTTPError, e:
    bad_files.append(url)

for b in bad_files:
    print "bad: " + b

for g in good_files:
    print "good: " + g