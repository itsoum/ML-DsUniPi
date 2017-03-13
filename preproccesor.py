#!/usr/bin/env python

import csv
import re
import operator
import itertools
from collections import Counter, defaultdict
from itertools import imap
from operator import  itemgetter
import sys
import string

outfile = "preproccesor_terms_28102016-132120_gr.csv"
outfile2 = "preproccesor_others_28102016-132120_gr.csv"

#-----------------------------------------------------------------------
# open a file to write (mode "w"), and create a CSV writer object
#-----------------------------------------------------------------------
csvfile = file(outfile, "w")
csvwriter = csv.writer(csvfile)

csvfile2 = file(outfile2, "w")
csvwriter2 = csv.writer(csvfile2)

#-----------------------------------------------------------------------
# formats tweets: @-mentios, liks, etc...
#-----------------------------------------------------------------------
regex_str = [
    r'<[^>]+>', # HTML tags
    r'(?:@[\w_]+)', # @-mentions
    r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)", # hash-tags
    r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', # URLs
 
    r'(?:(?:\d+,?)+(?:\.?\d+)?)', # numbers
    r"(?:[a-z][a-z'\-_]+[a-z])", # words with - and '
    r'(?:[\w_]+)', # other words
    r'(?:\S)' # anything else
]
    
tokens_re = re.compile(r'('+'|'.join(regex_str)+')', re.VERBOSE | re.IGNORECASE)


#-----------------------------------------------------------------------
# open the target file and stopwords file
#-----------------------------------------------------------------------
with open('doc/okeanos vm/28102016-132120_gr.csv') as f, open('stopwords.txt') as sw:
    
    # skip the header
    next(f)

    #-----------------------------------------------------------------------
    # take from column 'text' of .csv all tweets. 
    # also count them. key: tweet | value: the number of same tweet
    #-----------------------------------------------------------------------
    cn = Counter(imap(itemgetter(1), csv.reader(f))) 
        
    #-----------------------------------------------------------------------
    # take 'stop words' from .txt and do lowercase them
    #-----------------------------------------------------------------------
    stopwords = re.sub(ur"[^\w\d'\s]+", '',  sw.read()).split()
    low_stopwords = [word.lower() for word in stopwords]
    
    # initialize a new list
    words = []
    tweets_number = 0
    
    #-----------------------------------------------------------------------
    # a) count the number of tweets
    # b) breaks the tweet phrase in its own words in a list and 
    # c) append words list with a new list for every tweet
    #-----------------------------------------------------------------------
    for key, value in cn.iteritems():

        # the number of all tweets with same text, and with RT label
        tweets_number += value
        
        words.append(tokens_re.findall(key))
    
    # number of tweets it grabbed
    num_tweets1 = tweets_number
    print num_tweets1
    row = [ "raw_tweets_number:", num_tweets1, " " ]
    csvwriter2.writerow(row) 
    # the number of all tweets without same text but with RT label
    num_tweets2 = len(words)
    print num_tweets2
    row = [ "tweets_number_proc1:", num_tweets2, " " ]
    csvwriter2.writerow(row) 
    # the number of all tweets without same text and RT label
    words_without_rtweets = [word for word in words if ('RT' or 'rt') not in word]
    tweets_number_without_rtweets = len(words_without_rtweets)
    num_tweets3 = tweets_number_without_rtweets
    print num_tweets3
    row = [ "tweets_number_proc2:", num_tweets3, " " ]
    csvwriter2.writerow(row)

    # do lowercase all the words
    low_final_listofwords = [[word.lower() for word in tweet] for tweet in words_without_rtweets]

    # remove urls
    low_final_listofwords_nohttps = [[re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', word) for word in tweet] for tweet in low_final_listofwords]
    
    # remove tweets with the same text | confuse first try, because same text tweets includes different urls
    low_final_listofwords_nohttps = [list(x) for x in set(frozenset(i) for i in [set(i) for i in low_final_listofwords_nohttps])]
    num_tweets4 = len(low_final_listofwords_nohttps)
    print num_tweets4
    row = [ "tweets_number_proc3:", num_tweets4, " " ]
    csvwriter2.writerow(row)

    
    #-----------------------------------------------------------------------
    # UNIQUE TOKENS FROM TWITTER FEED WITHOUT DUPLICATE TWEETS AND URL
    #-----------------------------------------------------------------------

    # flatten the words list of lists in one final_listofwords0 list 
    final_listofwords0 = list(itertools.chain.from_iterable(low_final_listofwords_nohttps))
        
    #-----------------------------------------------------------------------
    # counts the number of a word appears in list and create a dictionary 
    # key: word | value: count
    #-----------------------------------------------------------------------
    word_counts0 = Counter(final_listofwords0)

    #-----------------------------------------------------------------------
    # calc frequency: word(i) appears n times/ m tweets
    # print pair key:value with value bigger 100
    #-----------------------------------------------------------------------
    uniquetokens0 = 0
    for key, value in word_counts0.iteritems():
        uniquetokens0 += 1
  
    # calc average frequency: sum of words/ m tweets
    print uniquetokens0
    row = [ "raw_uniquetokens:", uniquetokens0, " " ]
    csvwriter2.writerow(row)
 


    #-----------------------------------------------------------------------
    # remove emoji and stop-words
    #-----------------------------------------------------------------------
    remoji_low_final_listofwords = [[re.sub(r'[^\x00-\x7F]+','', word) for word in tweet] for tweet in low_final_listofwords_nohttps]
    repunc = re.compile('[%s]' % re.escape(string.punctuation))    
    repunc_low_final_listofwords = [[repunc.sub('', word) for word in tweet] for tweet in remoji_low_final_listofwords]

    filtered_low_final_listofwords = [[word for word in tweet if word not in low_stopwords] for tweet in repunc_low_final_listofwords]
    
    Final_filtered_low_final_listofwords = [filter(None, tweet) for tweet in filtered_low_final_listofwords]

    #-----------------------------------------------------------------------
    # load nltk's SnowballStemmer as variabled 'stemmer'
    #-----------------------------------------------------------------------
    from nltk.stem.snowball import SnowballStemmer
    stemmer = SnowballStemmer("english")
    stems = [[stemmer.stem(word) for word in tweet] for tweet in Final_filtered_low_final_listofwords]


    #-----------------------------------------------------------------------
    # find all cooccurancies
    #-----------------------------------------------------------------------
    from collections import defaultdict
 
    com = defaultdict(lambda : defaultdict(int))
     
    # f is the file pointer to the JSON data set
    for terms_only in stems: 
     
        # Build co-occurrence matrix
        for i in range(len(terms_only)-1):            
            for j in range(i+1, len(terms_only)):
                w1, w2 = sorted([terms_only[i], terms_only[j]])                
                if w1 != w2:
                    com[w1][w2] += 1

    com_max = []
    # For each term, look for the most common co-occurrent terms
    for t1 in com:
        t1_max_terms = sorted(com[t1].items(), key=operator.itemgetter(1), reverse=True)[:5]
        for t2, t2_count in t1_max_terms:
            com_max.append(((t1, t2), t2_count))
    # Get the most frequent co-occurrences
    terms_max = sorted(com_max, key=operator.itemgetter(1), reverse=True)
    print(terms_max[:50])
    for couple in terms_max[:1000]:
        for occur in couple:
            row = [ occur, " " ]
            csvwriter2.writerow(row) 
    
    # flatten the words list of lists in one final_listofwords list 
    final_listofwords = list(itertools.chain.from_iterable(stems))
    
    
    #-----------------------------------------------------------------------
    # counts the number of a word appears in list and create a dictionary 
    # key: word | value: count
    #-----------------------------------------------------------------------
    word_counts = Counter(final_listofwords)
    

    #-----------------------------------------------------------------------
    # add headings to our CSV file
    #-----------------------------------------------------------------------
    row = [ "word", "occurrences", "frequency" ]
    csvwriter.writerow(row)

    #-----------------------------------------------------------------------
    # calc frequency: word(i) appears n times/ m tweets
    # print pair key:value with value bigger 100
    #-----------------------------------------------------------------------
    sum_frq = 0
    uniquetokens = 0
    for key, value in word_counts.iteritems():
        frequency = (float(value)/float(num_tweets4))*100
        sum_frq += frequency
        uniquetokens += 1

        if(value > 5000):
            print "word %s appears %s times with frequency %f %%" % (key,value,frequency)

        #-----------------------------------------------------------------------
        # now write on csv
        #-----------------------------------------------------------------------
        
        row = [ key, value, frequency ]
        csvwriter.writerow(row) 
    
    # calc average frequency: sum of words/ m tweets
    avg_frq = sum_frq/num_tweets4
    print avg_frq
    print uniquetokens
    row = [ "uniquetokens:", uniquetokens, " " ]
    csvwriter2.writerow(row)
    row = [ "avg_frequency:", avg_frq, " " ]
    csvwriter2.writerow(row) 



