# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, g, Response, redirect, url_for
import logging, json
import mongo, os
from user import require_login
from models import ConnectionString

mod = Blueprint('connection_string', __name__, url_prefix='/connection')


def load(name):
    logging.info('load connection string %s', name)

    connection_string = ConnectionString.objects.get({"name": name})

    if not connection_string:
        return None

    return connection_string.get('url')

def save(name, url):
    logging.info('save connection_string %s: %s', name, url)

    ConnectionString.update(
        {'name': name},
        {"$set": {'url': url}},
        upsert = True);

@mod.route('/list', methods=['GET'])
def list():
    return render_template('connection_string/list.html', connection_strings=ConnectionString.objects())


@mod.route('/new', methods=['GET'])
@require_login
def new():
    url = 'mysql://scott:tiger@localhost/foo'
    return render_template('connection_string/new.html', url = url)

@mod.route('/', methods=['GET', 'POST'])
@mod.route('/<name>', methods=['GET', 'POST'])
@require_login
def edit(name=None):
    if request.method == 'GET':
        logging.info('loading connection string %s', name)
        if not name:
            return redirect(url_for('.new'))

        url = load(name)
    else:
        url = request.form['url']

        name = request.form.get('name')

        if name == 'new':
            name = None

        if name:
            save(name, url)
            return redirect(url_for('.edit', name = name))

    return render_template('connection_string/new.html',
                           name = name,
                           url = url)

