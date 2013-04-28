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
    owner = db.ReferenceField(User, required=True, dbref=True)
    editors = db.ListField(db.ReferenceField('User', dbref=True))

    @classmethod
    def all(cls):
        if not session.user:
            return None

        return cls.objects.filter(db.Q(owner=session.user) | db.Q(editors = session.user))

    @classmethod
    def create_or_update(cls, name, sql, meta_vars, connection, editors):
        user = session.user

        if not user:
            raise Exception('Missing user')

        query, created = cls.objects.get_or_create(auto_save = False, name = name)

        if not created and query.owner.pk != user.pk:
            raise Exception('Query already exists')

        if created:
            query.owner = user

        editors = list(editors)

        for i,editor in enumerate(editors):
            if editor.pk == user.pk:
                editors[i] = None

        editors = [editor for editor in editors if editor]

        if not created:
            modified = [editor.pk for editor in editors] != [editor.pk for editor in query.editors] or \
                       query.sql != sql or \
                       query.meta_vars != meta_vars or \
                       query.connection != connection

        if created or modified:
            query.editors = editors
            query.last_modified_by = session.user
            query.sql = sql
            query.connection = connection
            query.meta_vars = meta_vars
            query.updated = datetime.utcnow()
            query.save()

    @classmethod
    def find(cls, name_or_oid):
        logging.info('loading query %s', name_or_oid)

        user = session.user

        if not user:
            raise Exception('Missing user')

        if not name_or_oid:
            return None

        if ObjectId.is_valid(name_or_oid):
            filter = db.Q(pk = name_or_oid) | db.Q(name = name_or_oid)
        else:
            filter = db.Q(name = name_or_oid)

        query = cls.objects.get(filter & (db.Q(owner=user) | db.Q(editors = user)))

        return query
