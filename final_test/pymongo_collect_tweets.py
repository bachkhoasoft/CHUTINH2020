import sys
import pymongo
import time
import tweepy
import nltk
from nltk.corpus import stopwords
from tweepy.streaming import StreamListener, json
from tweepy import OAuthHandler
from tweepy import Stream

# Locations collection has the form:
#        'location': 'London',
#        'isTaken': 0
#
# words collection has the form:
#        'word': realy
#        'location' : london,
#        'count': 0

### database parameters
dbuser = 'test'
dbpassword = '*******'
dbname = 'python_twitter'
host = '******.mlab.com'
port = 21861
#-----------------------------------------------------------------------
# util functions
def list_db(mydb, n=0):

    i = 0

    for doc in mydb.find():
        if (n > 0 and i>n): break
        i += 1
        print(doc)
		
def insert_word(word):
        
    global db
    words = db['words']
    doc = words.find_one_and_update(
        { 'word' : word },
        { '$inc': { "count": 1 } },
        upsert=True)
		
def connect_to_db():
    
    # Connect to data base
    global db, connection
    connection = pymongo.MongoClient(host, port)
    db = connection[dbname]
    
    db.authenticate(dbuser, dbpassword)
    print('db', db)
    return db, connection
	
def get_notTaken_location_and_keys(db):
    
    # First we'll add a few songs. Nothing is required to create the songs 
    # collection; it is created automatically when we insert.

    locations = db['locations']
    print('locations', locations)
    
    # Get location from locations collection and mark that its taken	
    #
    #        'location': 'London',
    #        'isTaken': 0	

    cursor = db.locations.find({"isTaken": 0}) 
    my_doc = None

    for doc in cursor:
        print ('location %s is it taken ?  %d ' %
               (doc['location'], doc['isTaken']))
        my_doc = doc
        break
    if (my_doc is None):
        print('No more locations')
        return None
    
    print('----------------------------------------------')
    print('Using location: 	',my_doc['location'])
    my_location = my_doc['location']
    global consumer_key, consumer_secret, access_token, access_token_secret

    consumer_key = my_doc['consumer_key']
    consumer_secret=my_doc['consumer_secret']
    access_token=my_doc['access_token']
    access_token_secret=my_doc['access_token_secret']
    query = {'location': my_location}
    print('query', query)

    locations.update_one(query, {'$set': {'isTaken': 1}})

    list_db(locations)
    
    return my_location
#----------------------------------------------------------------
'''
TWITTER_VAR = {
    "consumer_key": ****',
    "consumer_secret": ****',
    "access_token": ****',
    "access_token_secret": ****'}
'''	
nltk.download('stopwords')
STOP_WORDS = ['ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 'about',
              'once', 'during', 'out', 'very', 'having', 'with', 'they', 'own', 'an', 'be',
              'some', 'for', 'do', 'its', 'yours', 'de', 'vs', 'such', 'into', 'of', 'most', 'itself',
              'other', 'off', 'is', 's', 'am', 'or', 'who', 'as', 'from', 'him', 'each',
              'the', 'themselves', 'until', 'below', 'are', 'we', 'these', 'your', 'his',
              'through', 'don', '\'\'', 'nor', 'me', 'were', 'her', 'more', 'himself',
              'this', 'down', 'should', 'our', 'their', 'while', 'above', 'both',
              'up', 'to', 'ours', 'had', 'she', 'all', 'no', 'when', 'at', 'any',
              'before', 'them', 'same', 'and', 'been', 'have', 'in', 'will', 'on',
              'does', 'yourselves', 'then', 'that', 'because', 'what', 'over', 'why',
              'so', 'can', 'did', 'not', 'now', 'under', 'he', 'you', 'herself', 'has',
              'just', 'where', 'too', 'only', 'myself', 'which', 'those', 'i', 'after',
              'few', 'whom', 't', 'being', 'if', 'theirs', 'my', 'against', 'a', 'by',
              'doing', 'it', 'how', 'further', 'was', 'here', 'than', 'The',
              'rt', '&amp', ' ', '', '``', 'http', 'via', 'https', 'amp', '\'s', 'co', 'th']
STOP_WORDS = set(stopwords.words('english') + STOP_WORDS)


WORD_TOKENIZER = nltk.RegexpTokenizer('[a-zA-Z]\w+')
def tokenize_tweet_text(tweet_text):
    word_tokens = WORD_TOKENIZER.tokenize(tweet_text)
    filtered_sentence = []
    for w in word_tokens:
            
        if len(w) > 1 and w.lower() not in STOP_WORDS:
            w = nltk.re.sub('[!@#$]', '', w)
            
            filtered_sentence.append(w.lower())
    return filtered_sentence
#----------------------------------------------------------------
# gloval variables
db = None
connection = None
track_words = []
words = None
consumer_key = ''
consumer_secret=''
access_token=''
access_token_secret=''
	
class StdOutListener(tweepy.StreamListener):

    def __init__(self):
        super().__init__()
		
    def on_status(self, status):
        if status.retweeted:
            return
                
    def on_data(self, data):
        global track_words
        global words
        tweet = json.loads(data)
        if tweet['text']:
            text = tweet['text']
            print(text)
        else:
            return True
			
        tokens = tokenize_tweet_text(text)
        for token in tokens:
            if ((token not in track_words)):
                print('inserting word ', token)
                insert_word(token)
        return True
    
    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_data disconnects the stream
            return False

	
###############################################################################
# main
###############################################################################
consumer_key=u'****'
consumer_secret= u'****'
access_token= u'****'
access_token_secret=u'****'
track_words=['worldcup']

def main(args):
	
	db, connection = connect_to_db()

	global track_words


	print('=======================================')
	print('track words:', track_words)

	
	words = db['words']

	global consumer_key, consumer_secret, access_token, access_token_secret
	
	while True:
		try:

			auth = OAuthHandler(consumer_key, consumer_secret)
			auth.set_access_token(access_token, access_token_secret)
			api = tweepy.API(auth)
			stream_listener = StdOutListener()
			stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
			stream.filter(track=track_words)
			
		except:
		
			print("restarting")
			time.sleep(3)
			


	print("exit process")	
	
	connection.close()


if __name__ == '__main__':
    main(sys.argv[1:])
