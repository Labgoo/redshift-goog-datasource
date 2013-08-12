from app import app
db = app.extensions['mongoengine']
from flask import session
import requests
import os


class ProjectConnection(db.Document):
    url = db.StringField(required=True)
    name = db.StringField(required=True)
    headers = db.StringField()

    @classmethod
    def api_root(cls):
        return os.environ.get('cooladata_api_root')

    @classmethod
    def all(cls):
        user = getattr(session, 'user', None)

        if not user:
            return []

        r = requests.get('%sprojects/' % cls.api_root(),
                         headers={'Authorization': 'Token %s' % user.oauth_token})

        r.raise_for_status()
        projects = r.json()

        connections = []

        for project in projects:
            connection = ProjectConnection()
            connection.url = '%sprojects/%s/cql?tq={query}' % (cls.api_root(), project["id"])
            connection.headers = '{"Authorization": "Token %s"}' % user.oauth_token
            connection.name = project["name"]
            connections.append(connection)

        return connections

    @classmethod
    def find(cls, name_or_oid, _=False):
        if not name_or_oid:
            return None

        projects = getattr(session, 'projects', None)

        if projects is None:
            projects = cls.all()

        for project in projects:
            if project.name == name_or_oid:
                return project

        return None

