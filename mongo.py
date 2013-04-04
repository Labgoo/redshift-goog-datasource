import os

def get_mongo():	
	from pymongo import MongoClient, uri_parser

	mongolab_uri = os.environ['MONGOLAB_URI']
	url = uri_parser.parse_uri(mongolab_uri)
	MONGODB_USERNAME = url['username']
	MONGODB_PASSWORD = url['password']
	MONGODB_HOST, MONGODB_PORT = url['nodelist'][0]
	MONGODB_DB = url['database']

	connection = MongoClient(MONGODB_HOST, MONGODB_PORT)
	db = connection[MONGODB_DB]
	if MONGODB_USERNAME:
		db.authenticate(MONGODB_USERNAME, MONGODB_PASSWORD)

	return db