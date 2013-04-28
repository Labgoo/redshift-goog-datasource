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
        if not session.user:
            return None

        return cls.objects.filter(db.Q(owner=session.user) | db.Q(editors = session.user))

    @classmethod
    def create_or_update(cls, name, url, headers, editors):
        user = session.user

        if not user:
            raise Exception('Missing user')

        connection, created = cls.objects.get_or_create(auto_save = False, name = name)

        if not created and connection.owner.pk != owner.pk:
            raise Exception('Connection already exists')

        if created:
            connection.owner = user

        editors = list(editors)

        for i,editor in enumerate(editors):
            if editor.pk == user.pk:
                editors[i] = None

        editors = [editor for editor in editors if editor]

        connection.editors = editors
        connection.url = url
        connection.headers = headers
        connection.save()

    @classmethod
    def find(cls, name_or_oid):
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

