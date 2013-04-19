import logging
from app import app

db = app.extensions['mongoengine']

class Transformer(db.Document):
    meta = {'collection': 'transformerers',
            'indexes': [
                {'fields': ['name'], 'unique': True},
                ]
    }

    code = db.StringField(required=True)
    name = db.StringField(required=True)

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
