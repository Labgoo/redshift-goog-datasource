import os

def get_mongo_params():
    from pymongo import uri_parser

    mongolab_uri = os.environ['MONGOLAB_URI']

    url = uri_parser.parse_uri(mongolab_uri)
    MONGODB_USERNAME = url['username']
    MONGODB_PASSWORD = url['password']
    MONGODB_HOST, MONGODB_PORT = url['nodelist'][0]
    MONGODB_DB = url['database']

    return {'username': MONGODB_USERNAME,
            'password': MONGODB_PASSWORD,
            'host': MONGODB_HOST,
            'port': MONGODB_PORT,
            'db': MONGODB_DB
    }