from app import app
db = app.extensions['mongoengine']
from flask import session
from models import User
from bson import ObjectId

class ConnectionString(db.Document):
    meta = {'collection': 'connection_strings',
            'indexes': [
                {'fields': ['name'], 'unique': True},
            ]
    }

    owner = db.ReferenceField(User, required=True, dbref=True)
    url = db.StringField(required=True)
    name = db.StringField(required=True)
    headers = db.StringField()

    @classmethod
    def all(cls):
        if not session.user:
            return None

        return cls.objects.filter(owner=session.user)

    @classmethod
    def create_or_update(cls, name, url, headers):
        owner = session.user
        connection, created = cls.objects.get_or_create(auto_save = False, name = name)

        if not created and connection.owner.pk != owner.pk:
            raise Exception('Connection point already exists')

        connection.owner = owner
        connection.url = url
        connection.headers = headers
        connection.save()

    @classmethod
    def find(cls, name_or_oid):
        if not name_or_oid:
            return None

        if ObjectId.is_valid(name_or_oid):
            connection_string = cls.objects.get(db.Q(pk = name_or_oid) | db.Q(name = name_or_oid))
        else:
            connection_string = cls.objects.get(db.Q(name = name_or_oid))

        return connection_string
