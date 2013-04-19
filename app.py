import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
import mongo

app = Flask(__name__)

app.config.update(
	DEBUG = True,
	SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
)

app.config['DEBUG_TB_PANELS'] = (
    'flask.ext.debugtoolbar.panels.versions.VersionDebugPanel',
    'flask.ext.debugtoolbar.panels.timer.TimerDebugPanel',
    'flask.ext.debugtoolbar.panels.headers.HeaderDebugPanel',
    'flask.ext.debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    'flask.ext.debugtoolbar.panels.template.TemplateDebugPanel',
    'flask.ext.debugtoolbar.panels.logger.LoggingPanel',
    'flask.ext.mongoengine.panels.MongoDebugPanel'
)

app.debug = True

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

app.config['MONGODB_SETTINGS'] = mongo.get_mongo_params()

db = SQLAlchemy(app)

from flask.ext.mongoengine import MongoEngine

mongodb = MongoEngine()
mongodb.init_app(app)

#toolbar = DebugToolbarExtension(app)

