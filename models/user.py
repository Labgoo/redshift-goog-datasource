import logging
from app import app

db = app.extensions['mongoengine']

class User(db.Document):
    meta = {'collection': 'users'}

    openid = db.StringField(required=False)
    username = db.StringField(required=False)
    email = db.StringField(required=False)
    oauth_token = db.StringField(required=False)

    @classmethod
    def create(cls, username, email, openid, oauth_token):
        user = User()
        user.username = username
        user.email = email
        user.openid = openid
        user.oauth_token = oauth_token
        user.save()

    @classmethod
    def get_by_username(cls, users):
        try:
            return cls.objects.filter(email__in=users)
        except: # TODO: better catch
            return None

    @classmethod
    def get_by_openid(cls, openid):
        try:
            return cls.objects.get(openid=openid)
        except:  # TODO: better catch
            return None