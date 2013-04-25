import logging
from app import app
from models import User
from flask import session
from datetime import datetime
from bson import ObjectId

db = app.extensions['mongoengine']

class Transformer(db.Document):
    meta = {'collection': 'transformerers',
            'indexes': [
                {'fields': ['name'], 'unique': True},
                ]
    }

    owner = db.ReferenceField(User, required=True, dbref=True)
    code = db.StringField(required=True)
    name = db.StringField(required=True)
    last_modified_by = db.ReferenceField(User, required=True, dbref=True)
    updated = db.DateTimeField(required=True)

    @classmethod
    def all(cls):
        if not session.user:
            return None

        return cls.objects.filter(owner=session.user)

    @classmethod
    def create_or_update(cls, name, code):
        owner = session.user
        query, created = cls.objects.get_or_create(auto_save = False, name = name)

        if not created and query.owner.pk != owner.pk:
            raise Exception('Query already exists')

        query.last_modified_by = session.user
        query.owner = owner
        query.code = code
        query.updated = datetime.utcnow()
        query.save()

    @classmethod
    def execute(cls, name, data):
        logging.info('executing transformer %s', name)
        transformer = cls.objects.get({"name": name})

        if not transformer:
            return None

        code = transformer.code

        code_globals = {}
        code_locals = {'data': data}
        code_object = compile(code, '<string>', 'exec')
        exec code_object in code_globals, code_locals

        return code_locals['result']
