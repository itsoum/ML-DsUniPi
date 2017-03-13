import time
start_time = time.time()

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score


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

with open('doc/28102016-132120_gr.csv') as f, open('stopwords.txt') as sw:
    
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
    
    print tweets_number
    # the number of all tweets without same text but with RT label
    print len(words)

    words_without_rtweets = [word for word in words if ('RT' or 'rt') not in word]
    
    # the number of all tweets without same text and RT label
    tweets_number_without_rtweets = len(words_without_rtweets)
    print tweets_number_without_rtweets


    # do lowercase all the words
    low_final_listofwords = [[word.lower() for word in tweet] for tweet in words_without_rtweets]

    # remove urls
    low_final_listofwords_nohttps = [[re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', word) for word in tweet] for tweet in low_final_listofwords]

    # remove tweets with the same text | confuse first try, because same text tweets includes different urls
    low_final_listofwords_nohttps = [list(x) for x in set(frozenset(i) for i in [set(i) for i in low_final_listofwords_nohttps])]

    print len(low_final_listofwords_nohttps)


    #-----------------------------------------------------------------------
    # remove emoji and stop-words
    #-----------------------------------------------------------------------
    remoji_low_final_listofwords = [[re.sub(r'[^\x00-\x7F]+','', word) for word in tweet] for tweet in low_final_listofwords_nohttps]
    repunc = re.compile('[%s]' % re.escape(string.punctuation))    
    repunc_low_final_listofwords = [[repunc.sub('', word) for word in tweet] for tweet in remoji_low_final_listofwords]

    filtered_low_final_listofwords = [[word for word in tweet if word not in low_stopwords] for tweet in repunc_low_final_listofwords]
    
    Final_filtered_low_final_listofwords = [filter(None, tweet) for tweet in filtered_low_final_listofwords]

    
    # load nltk's SnowballStemmer as variabled 'stemmer'
    from nltk.stem.snowball import SnowballStemmer
    stemmer = SnowballStemmer("english")

    stems = [[stemmer.stem(word) for word in tweet] for tweet in Final_filtered_low_final_listofwords]

    

    tweets = [' '.join(x) for x in stems]

    


#-----------------------------------------------------------------------
# START MACHINE LEARNING METHODS
#-----------------------------------------------------------------------


#-----------------------------------------------------------------------
# vectorize the text i.e. convert the strings to numeric features
#-----------------------------------------------------------------------
vectorizer = TfidfVectorizer(max_df=0.3, min_df=2, stop_words='english', use_idf=True, ngram_range=(1,2))
tfidf_matrix = vectorizer.fit_transform(tweets)
print tfidf_matrix.shape



#-----------------------------------------------------------------------
# cluster documents k-means
#-----------------------------------------------------------------------
true_k = 6
model = KMeans(n_clusters=true_k, init='k-means++', max_iter=300, n_init=10)
model.fit(tfidf_matrix)
#print top terms per cluster clusters

print("Top terms per cluster:")
order_centroids = model.cluster_centers_.argsort()[:, ::-1]
terms = vectorizer.get_feature_names()
for i in range(true_k):
    print "Cluster %d:" % i,
    for ind in order_centroids[i, :10]:
        print ' %s' % terms[ind],
    print

from sklearn import metrics
from sklearn.metrics import pairwise_distances


klabels = model.labels_
#print labels
silh_coef = metrics.silhouette_score(tfidf_matrix, klabels, metric='euclidean')
print silh_coef
X = tfidf_matrix.toarray()
calhar = metrics.calinski_harabaz_score(X, klabels)
print calhar

nums = Counter(klabels)
print nums



#-----------------------------------------------------------------------
# NMF
#-----------------------------------------------------------------------
from sklearn.decomposition import NMF
nmf = NMF(n_components=6, random_state=1).fit(tfidf_matrix)

feature_names = vectorizer.get_feature_names()

for topic_idx, topic in enumerate(nmf.components_):
    print("Topic #%d:" % topic_idx)
    print("  ".join([feature_names[i]
        for i in topic.argsort()[:-20-1:-1]]))
    print



#--------------------------------------------------------
# AgglomerativeClustering Ward
#--------------------------------------------------------
from sklearn.cluster import AgglomerativeClustering
X = tfidf_matrix.toarray()
print("Compute unstructured hierarchical clustering...")
#st = time.time()
ward = AgglomerativeClustering(n_clusters=6, linkage='ward', connectivity=None, affinity="eucledean", compute_full_tree="auto")
print 0
ward.fit(X)
print 1
wlabels = ward.labels_
print("Number of points: %i" % wlabels.size)

# problem
print("Top terms per ward cluster:")
order_centroids = ward.children_.argsort()[:, ::-1]
terms = vectorizer.get_feature_names()
for i in range(true_k):
    print terms[i]
    print "Cluster %d:" % i,
    for ind in order_centroids[i, :10]:
        print ' %s' % terms[ind],
    print

#clusters = model.labels_.tolist()

#print clusters.value_counts()
from sklearn import metrics
from sklearn.metrics import pairwise_distances


print wlabels
silh_coef = metrics.silhouette_score(tfidf_matrix, wlabels, metric='cityblock')
print silh_coef
calhar = metrics.calinski_harabaz_score(X, wlabels)



#-----------------------------------------------------------------------
# Ward and Dendogram
#-----------------------------------------------------------------------
import matplotlib.pyplot as plt

from scipy.cluster.hierarchy import ward, dendrogram

linkage_matrix = ward(dist) #define the linkage_matrix using ward clustering pre-computed distances
# calculate full dendrogram
plt.figure(figsize=(25, 10))
plt.title('Hierarchical Clustering Dendrogram (truncated)')
plt.xlabel('sample index or (cluster size)')
plt.ylabel('distance')
dendrogram(
    linkage_matrix,
    truncate_mode='lastp',  # show only the last p merged clusters
    p=6,  # show only the last p merged clusters
    leaf_rotation=90.,
    leaf_font_size=12.,
    show_contracted=True,  # to get a distribution impression in truncated branches
)
plt.savefig('ward_clusters_gr1.png', dpi=200) #save figure as ward_clusters
plt.show()

print("--- %s seconds ---" % (time.time() - start_time))
