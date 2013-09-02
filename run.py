import logging
from app import app
from flask import redirect, url_for
import os

from sqlalchemy.dialects import registry

registry.register('postgresql.redshift', 'redshift' '', 'PGDialect_RedShift')


@app.before_request
def before_request():
    logging.getLogger().setLevel(logging.INFO)


from views import query
from views import transformer
from views import user
from views import connection_string
from views import oauth2
from views import oauthclient
from views import homepage

app.register_blueprint(query.mod)
app.register_blueprint(transformer.mod)
app.register_blueprint(user.mod)
app.register_blueprint(connection_string.mod)
app.register_blueprint(oauth2.mod)
app.register_blueprint(oauthclient.mod)
app.register_blueprint(homepage.mod)


@app.context_processor
def inject_meta():
    d = dict(favico=os.environ.get('favico'), logo=os.environ.get('logo'))

    for key, val in os.environ.iteritems():
        key = "env_" + key
        d[key] = val

    return d


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)