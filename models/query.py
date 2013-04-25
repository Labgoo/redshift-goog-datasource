from app import app
from bson import ObjectId
from flask import session
import logging
from datetime import datetime
from models import User, ConnectionString

db = app.extensions['mongoengine']

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

    @classmethod
    def create_or_update(cls, name, sql, meta_vars, connection):
        query, created = cls.objects.get_or_create(auto_save = False, name = name)

        query.last_modified_by = session.user

        query.sql = sql
        query.connection = connection
        query.meta_vars = meta_vars
        query.updated = datetime.utcnow()
        query.save()

    @classmethod
    def all(cls):
        if not session.user:
            return None

        return cls.objects(owner=session.user)

    @classmethod
    def find(cls, name_or_oid):
        logging.info('loading query %s', name_or_oid)

        if not name_or_oid:
            return None

        if ObjectId.is_valid(name_or_oid):
            app = cls.objects.get(db.Q(pk = name_or_oid) | db.Q(name = name_or_oid))
        else:
            app = cls.objects.get(db.Q(name = name_or_oid))

        return app
