#!/usr/bin/env python

#-----------------------------------------------------------------------
# twitter-stream-format:
#  - ultra-real-time stream of twitter's public timeline.
#    does some fancy output formatting.
#-----------------------------------------------------------------------
import os
from twitter import *
import re
import sys
import csv
from datetime import datetime
#-----------------------------------------------------------------------
# Import the necessary package to process data in JSON format
#-----------------------------------------------------------------------
try:
    import json
except ImportError:
    import simplejson as json

csv_outfile = datetime.now().strftime("doc/%d%m%Y-%H%M%S_searchterm.csv")#"doc/euro2016wthoutTer.csv"
json_outfile = datetime.now().strftime("doc/%d%m%Y-%H%M%S_searchterm.json")#"doc/euro2016wthoutTer.json"

search_term = "searchtermA,searchtermB"

#-----------------------------------------------------------------------
# open a file to write (mode "w"), and create a CSV writer object
#-----------------------------------------------------------------------
csvfile = file(csv_outfile, "w")
csvwriter = csv.writer(csvfile)

#-----------------------------------------------------------------------
# add headings to our CSV file
#-----------------------------------------------------------------------
row = [ "user", "text", "location", "created_at" ]
csvwriter.writerow(row)


#-----------------------------------------------------------------------
# import a load of external features, for text display and date handling
# you will need the termcolor module:
#
# pip install termcolor
#-----------------------------------------------------------------------
from time import strftime
from textwrap import fill
from termcolor import colored
from email.utils import parsedate

#-----------------------------------------------------------------------
# load our API credentials 
#-----------------------------------------------------------------------
config = {}
execfile("config2.py", config)

#-----------------------------------------------------------------------
# create twitter API object
#-----------------------------------------------------------------------
auth = OAuth(config["access_key"], config["access_secret"], config["consumer_key"], config["consumer_secret"])
stream = TwitterStream(auth = auth, secure = True)

#-----------------------------------------------------------------------
# iterate over tweets matching this filter text
#-----------------------------------------------------------------------
tweet_iter = stream.statuses.filter(track = search_term, language="en")

pattern = re.compile("%s" % search_term, re.IGNORECASE)
#i=0
with open(json_outfile, 'w') as f:

	for tweet in tweet_iter:
		
		#-----------------------------------------------------------------------
		# Twitter Python Tool wraps the data returned by Twitter 
	    # as a TwitterDictResponse object.
	    # We convert it back to the JSON format to print/score and
	    # we writing JSON tweets feed on a JSON file
	    #-----------------------------------------------------------------------		
		json.dump(tweet, f)
		f.write('\n')
		#print json.dumps(tweet) 

		if "created_at" and "user" and "text" in tweet:
			# turn the date string into a date object that python can handle
			timestamp = parsedate(tweet["created_at"])

			# now format this nicely into HH:MM:SS format
			timetext = strftime("%H:%M:%S", timestamp)
			

			# colour our tweet's time, user and text
			time_colored = colored(timetext, color = "white", attrs = [ "bold" ])
			user_colored = colored(tweet["user"]["screen_name"], "green")
			text_colored = tweet["text"]
			location_colored = colored(tweet["user"]["location"], "red")
			
			# replace each instance of our search terms with a highlighted version
			text_colored = pattern.sub(colored(search_term.upper(), "yellow"), text_colored)

			# add some indenting to each line and wrap the text nicely
			indent = " " * 11
			text_colored = fill(text_colored, 80, initial_indent = indent, subsequent_indent = indent)

			# now output our tweet
			print "(%s) @%s from %s" % (time_colored, user_colored, location_colored)
			print "%s" % (text_colored)

			#-----------------------------------------------------------------------
			# using .encode('utf-8') to fix emoji and no ascii characters issue
			#-----------------------------------------------------------------------
			user = tweet["user"]["screen_name"].encode('utf-8')
			text = tweet["text"].encode('utf-8')
			location = tweet["user"]["location"]
			if(location != None):
				location = tweet["user"]["location"].encode('utf-8')
			if "created_at" in tweet:	
				created_at = tweet["created_at"]

			#-----------------------------------------------------------------------
			# now write on csv
			#-----------------------------------------------------------------------

			row = [ user, text, location, created_at ]
			csvwriter.writerow(row)
		else:
			print "Maybe Hangup. Check .json document"
		#i += 1
		#print i
		if datetime.now().strftime("%H%M%S") == '040000':
			f.close()
			csvfile.close()
			stream = "stop"
			break

import time
time.sleep(2)		
os.execv('tweetsGrabber.py', [''])
			
