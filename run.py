from flask import g
import logging
from app import app, db
import os

from sqlalchemy.dialects import registry
registry.register('postgresql.redshift', 'redshift' '', 'PGDialect_RedShift')

@app.before_request
def before_request():
	logging.getLogger().setLevel(logging.INFO)
	g.db = db.engine

from views import query
from views import transformer
from views import user
from views import connection_string
from views import oauth2
from views import application

app.register_blueprint(query.mod)
app.register_blueprint(transformer.mod)
app.register_blueprint(user.mod)
app.register_blueprint(connection_string.mod)
app.register_blueprint(oauth2.mod)
app.register_blueprint(application.mod)

if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)