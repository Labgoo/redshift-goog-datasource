from app import app
from models import User
from bson import ObjectId
db = app.extensions['mongoengine']

class OAuthClient(db.Document):
    meta = {'collection': 'oauthclients',
            'indexes': [
                {'fields': ['name'], 'unique': True},
            ]
    }

    owner = db.ReferenceField(User, required=True, dbref=True)
    name = db.StringField(required=True)
    website = db.StringField(required=True)
    icon = db.StringField(required=False)
    domain = db.StringField(required=True)
    description = db.StringField(required=True)
    client_secret = db.StringField()

    @property
    def client_id(self):
        return str(self.pk)

    @classmethod
    def find(cls, client_id):
        if not client_id:
            return None

        if ObjectId.is_valid(client_id):
            client = cls.objects.get(db.Q(pk = client_id) | db.Q(name = client_id))
        else:
            client = cls.objects.get(db.Q(name = client_id))

        return client
