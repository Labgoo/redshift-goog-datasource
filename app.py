import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import *

app = Flask(__name__)

app.config.update(
	DEBUG = True,
	SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

db = SQLAlchemy(app)