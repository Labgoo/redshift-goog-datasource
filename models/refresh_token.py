from app import app
from mongoengine.queryset import DoesNotExist
db = app.extensions['mongoengine']

class RefreshToken(db.Document):
    meta = {'collection': 'applications',
            'indexes': [
                {'fields': ['client_id', 'refresh_token'], 'unique': True},
            ]
    }

    client_id = db.StringField(required=True)
    refresh_token = db.StringField(required=True)
    data = db.StringField(required=True)

    @classmethod
    def delete(cls, client_id, refresh_token):
        cls.objects(db.Q(client_id = client_id) & db.Q(refresh_token = refresh_token)).remove()

    @classmethod
    def find(cls, client_id, refresh_token):
        return RefreshToken.objects.get(db.Q(client_id=client_id) & db.Q(refresh_token=refresh_token))

    @classmethod
    def save(cls, client_id, refresh_token, data):
        token, created = RefreshToken.objects.get_or_create(client_id=client_id, refresh_token=refresh_token)
        token.data = data

        token.save()

class AccessKey(db.Document):
    meta = {'collection': 'applications',
            'indexes': [
                {'fields': ['client_id', 'user_id'], 'unique': False},
            ]
    }

    client_id = db.StringField(required=True)
    user_id = db.StringField(required=True)
    access_key = db.StringField(required=True)
    token = db.ReferenceField(RefreshToken, required=True)

    @classmethod
    def has_access(cls, client_id, user_id):
        try:
            return cls.objects.get(db.Q(client_id = client_id) & db.Q(user_id = user_id)) != None
        except DoesNotExist:
            return None

    @classmethod
    def delete(cls, client_id, user_id):
        cls.objects(db.Q(client_id = client_id) & db.Q(user_id = user_id)).remove()

    @classmethod
    def save(cls, client_id, user_id, access_key, token):
        access, created = AccessKey.objects.get_or_create(client_id=client_id, user_id=user_id)
        access.access_key = access_key
        access.token = token

        access.save()