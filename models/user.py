import logging
from app import app

db = app.extensions['mongoengine']

class User(db.Document):
    meta = {'collection': 'users'}

    openid = db.StringField(required=False)
    username = db.StringField(required=False)
    email = db.StringField(required=False)

    @classmethod
    def create(cls, username, email, openid):
        user = User()
        user.username = username
        user.email = email
        user.openid = openid
        user.save()

    @classmethod
    def get_by_openid(cls, openid):
        try:
            return cls.objects.get(openid = openid)
        except:
            return None