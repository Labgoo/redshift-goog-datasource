from app import app

db = app.extensions['mongoengine']

class Query(db.Document):
    meta = {'collection': 'queries',
            'indexes': [
                {'fields': ['name'], 'unique': True},
            ]
    }

    meta_vars = db.StringField(required=False)
    sql = db.StringField(required=True)
    name = db.StringField(required=True)
