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
    editors = db.ListField(db.ReferenceField('User', dbref=True))

    @classmethod
    def all(cls):
        user = getattr(session, 'user', None)

        if not user:
            return []

        return cls.objects.filter(db.Q(owner=user) | db.Q(editors = user))

    def is_user_editor(self, user):
        return self.owner == user or user in self.editors

    @classmethod
    def remove_duplicate_editors(cls, connection, editors):
        user = getattr(session, 'user', None)

        for i,editor in enumerate(editors):
            if editor == user and user == connection.owner:
                editors[i] = None

        return list(set([editor for editor in editors if editor]))

    @classmethod
    def create_or_update(cls, name, url, headers, editors):
        user = getattr(session, 'user', None)

        if not user:
            raise Exception('Missing user')

        connection, created = cls.objects.get_or_create(auto_save = False, name = name)

        if not created and not connection.is_user_editor(user):
            raise ValueError('Connection already exists')

        if created:
            connection.owner = user

        editors = cls.remove_duplicate_editors(connection, editors)

        connection.editors = editors
        connection.url = url
        connection.headers = headers
        connection.save()

    @classmethod
    def find(cls, name_or_oid, allow_global_search=False):
        if not name_or_oid:
            return None

        user = getattr(session, 'user', None)

        if not user and not allow_global_search:
            raise Exception('Missing user')

        if ObjectId.is_valid(name_or_oid):
            filter = db.Q(pk = name_or_oid) | db.Q(name = name_or_oid)
        else:
            filter = db.Q(name = name_or_oid)

        if not allow_global_search:
            filter = filter & (db.Q(owner=user) | db.Q(editors = user))

        connection = cls.objects.get(filter)

        return connection

