import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import *
from flask import g
import logging

app = Flask(__name__)

app.config.update(
	DEBUG = True,
	SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
)

db = SQLAlchemy(app)

from sqlalchemy.dialects import registry
registry.register('postgresql.redshift', 'redshift' '', 'PGDialect_RedShift')

@app.before_request
def before_request():
	g.db = db.engine

from views import query
app.register_blueprint(query.mod)

if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)