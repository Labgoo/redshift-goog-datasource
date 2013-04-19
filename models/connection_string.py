import logging
from app import app
from models import Transformer

db = app.extensions['mongoengine']

class ConnectionString(db.Document):
    meta = {'collection': 'connection_strings',
            'indexes': [
                {'fields': ['name'], 'unique': True},
                ]
    }

    url = db.StringField(required=True)
    name = db.StringField(required=True)
    headers = db.StringField()

