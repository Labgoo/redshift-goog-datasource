import logging
from app import app
from models import User
from flask import session
from datetime import datetime
from bson import ObjectId

db = app.extensions['mongoengine']

class Transformer(db.Document):
    meta = {'collection': 'transformers',
            'indexes': [
                {'fields': ['name'], 'unique': True},
                ]
    }

    owner = db.ReferenceField(User, required=True, dbref=True)
    code = db.StringField(required=True)
    name = db.StringField(required=True)
    last_modified_by = db.ReferenceField(User, required=True, dbref=True)
    updated = db.DateTimeField(required=True)
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
    def remove_duplicate_editors(cls, transformer, editors):
        user = getattr(session, 'user', None)

        for i,editor in enumerate(editors):
            if editor == user and user == transformer.owner:
                editors[i] = None

        return list(set([editor for editor in editors if editor]))

    @classmethod
    def create_or_update(cls, name, code, editors):
        user = getattr(session, 'user', None)

        if not user:
            raise Exception('Missing user')

        transformer, created = cls.objects.get_or_create(auto_save = False, name = name)

        if not created and not transformer.is_user_editor(user):
            raise Exception('Transformer already exists')

        if created:
            transformer.owner = user

        editors = cls.remove_duplicate_editors(transformer, editors)

        if not created:
            modified = [editor.pk for editor in editors] != [editor.pk for editor in transformer.editors] or \
                       transformer.code != code

        if created or modified:
            transformer.editors = editors
            transformer.last_modified_by = user
            transformer.code = code
            transformer.updated = datetime.utcnow()
            transformer.save()

    @classmethod
    def execute(cls, name, data, allow_global_search=False):
        logging.info('executing transformer %s', name)
        transformer = cls.find(name, allow_global_search)

        if not transformer:
            return None

        code = transformer.code

        code_globals = {}
        code_locals = {'data': data}
        code_object = compile(code, '<string>', 'exec')
        exec code_object in code_globals, code_locals

        return code_locals['result']

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

        transformer = cls.objects.get(filter)

        return transformer
