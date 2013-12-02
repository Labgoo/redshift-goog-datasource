from flask import Flask
import mongo


def install_newrelic_if_needed():
    import os
    config_file = os.environ.get('NEW_RELIC_CONFIG_FILE', None)

    if config_file is not None:
        environment = os.environ.get('NEW_RELIC_ENVIRONMENT', 'production')

        import newrelic.agent
        newrelic.agent.initialize(config_file, environment)

app = Flask(__name__)

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

from flask.ext.mongoengine import MongoEngine

install_newrelic_if_needed()

mongodb = MongoEngine()
mongodb.init_app(app)

#toolbar = DebugToolbarExtension(app)

