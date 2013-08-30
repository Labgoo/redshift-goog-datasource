from app import app
db = app.extensions['mongoengine']
from flask import session
import requests
import os
import logging


class ProjectConnection(db.Document):
    url = db.StringField(required=True)
    name = db.StringField(required=True)
    headers = db.StringField()

    @classmethod
    def api_root(cls):
        from urlparse import urlparse
        oid_url = os.environ.get('oid_url')
        o = urlparse(oid_url)
        return "%s://%s/api" % (o.scheme, o.netloc)

    @classmethod
    def projects_root(cls):
        return os.path.join(cls.api_root(), 'projects')

    @classmethod
    def all(cls):
        user = getattr(session, 'user', None)

        if not user:
            logging.info('connections.all() no user')
            return []

        logging.info('connections.all() user token (four first chars): %s', user.oauth_token[1:4])

        r = requests.get(cls.projects_root(),
                         headers={'Authorization': 'Token %s' % user.oauth_token})

        r.raise_for_status()
        projects = r.json()

        connections = []

        for project in projects:
            connection = ProjectConnection()
            connection.url = os.path.join(cls.projects_root(), str(project["id"]), 'cql?tq={query}')
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

