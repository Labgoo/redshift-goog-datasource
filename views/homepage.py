from flask import render_template, request, Blueprint, Response, redirect, url_for, g
import logging, json
from models import Query
from datetime import datetime, timedelta
from models import Transformer, ConnectionString, User
from user import require_login

mod = Blueprint('homepage', __name__)

@mod.route('/', methods=['GET'])
def index():
    return render_template('homepage/index.html')