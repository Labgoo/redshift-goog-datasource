from app import app
from bson import ObjectId
from flask import session
import logging, random, string
from datetime import datetime
from mongoengine.queryset import DoesNotExist
from models import User, ConnectionString

db = app.extensions['mongoengine']

UNICODE_ASCII_CHARACTERS = (string.ascii_letters.decode('ascii') +
    string.digits.decode('ascii'))

def random_ascii_string(length):
    return ''.join([random.choice(UNICODE_ASCII_CHARACTERS) for x in xrange(length)])

def create_query_access_token():
    return random_ascii_string(16)

class Query(db.Document):
    meta = {'collection': 'queries',
            'indexes': [
                {'fields': ['name'], 'unique': True},
            ]
    }

    meta_vars = db.ListField(required=False)
    sql = db.StringField(required=True)
    name = db.StringField(required=True)
    connection = db.ReferenceField(ConnectionString, required=False, dbref=True)
    last_modified_by = db.ReferenceField(User, required=True, dbref=True)
    updated = db.DateTimeField(required=True)
    owner = db.ReferenceField(User, required=True, dbref=True)
    editors = db.ListField(db.ReferenceField('User', dbref=True))
    access_token = db.StringField(required=True)

    @classmethod
    def all(cls):
        user = getattr(session, 'user', None)

        if not user:
            return []

        return cls.objects.filter(db.Q(owner=user) | db.Q(editors = user))

    def is_user_editor(self, user):
        return self.owner == user or user in self.editors

    @classmethod
    def remove_duplicate_editors(cls, query, editors):
        user = getattr(session, 'user', None)

        for i,editor in enumerate(editors):
            if editor == user and user == query.owner:
                editors[i] = None

        return list(set([editor for editor in editors if editor]))

    @classmethod
    def create_or_update(cls, name, sql, meta_vars, connection, editors):
        user = getattr(session, 'user', None)

        if not user:
            raise Exception('Missing user')

        query, created = cls.objects.get_or_create(auto_save = False, name = name)

        if not created and not query.is_user_editor(user):
            raise Exception('Query already exists')

        if created:
            query.owner = user

        editors = cls.remove_duplicate_editors(query, editors)

        if not created:
            modified = [editor.pk for editor in editors] != [editor.pk for editor in query.editors] or \
                       query.sql != sql or \
                       query.meta_vars != meta_vars or \
                       query.connection != connection

        if created or not query.access_token:
            query.access_token = create_query_access_token()
            modified = True

        if created or modified:
            query.editors = editors
            query.last_modified_by = user
            query.sql = sql
            query.connection = connection
            query.meta_vars = meta_vars
            query.updated = datetime.utcnow()
            query.save()

        return query, created

    @classmethod
    def find(cls, name_or_oid, access_token=None):
        logging.info('loading query %s', name_or_oid)

        user = getattr(session, 'user', None)

        if not user and not access_token:
            raise Exception('Missing user')

        if not name_or_oid:
            return None

        if ObjectId.is_valid(name_or_oid):
            filter = db.Q(pk = name_or_oid) | db.Q(name = name_or_oid)
        else:
            filter = db.Q(name = name_or_oid)

        if not access_token:
            filter = filter & (db.Q(owner=user) | db.Q(editors = user))

        try:
            query = cls.objects.get(filter)
        except DoesNotExist:
            query = None

        if query and access_token and access_token != query.access_token:
            return None

        return query
