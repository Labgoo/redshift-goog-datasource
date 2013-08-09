# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, g, session, redirect, url_for, Response
import logging
from user import require_login
from models import ConnectionString, User

mod = Blueprint('connection_string', __name__, url_prefix='/connection')

@mod.route('/list', methods=['GET'])
def list():
    return render_template('connection_string/list.html', connections=ConnectionString.all())

@mod.route('/new', methods=['GET'])
@require_login
def new():
    return render_template('connection_string/create_or_edit.html')

@mod.route('/<name>', methods=['DELETE'])
def delete(name):
    connection = ConnectionString.find(name)
    if connection:
        connection.delete()

    json_data = ConnectionString.dumps({'status': 'ok'})
    return Response(json_data,  mimetype='application/json')

@mod.route('/', methods=['GET', 'POST'])
@mod.route('/<name>', methods=['GET', 'POST'])
@require_login
def edit(name=None):
    users = []
    error_message = None

    if request.method == 'GET':
        logging.info('loading connection string %s', name)
        if not name:
            return redirect(url_for('.new'))

        connection = ConnectionString.find(name)

        url = connection.url
        name = connection.name
        headers = connection.headers
        users.append(connection.owner)
        editors = connection.editors
    else:
        def get_editors():
            editors = request.form.getlist('editors')
            if editors:
                users = User.get_by_username(editors)
                return users

            return []

        url = request.form['url']
        name = request.form.get('name')
        headers = request.form.get('headers')
        users.append(session.user)
        editors = get_editors()

        if name == 'new':
            name = None

        if name:
            try:
                ConnectionString.create_or_update(
                    name=name,
                    url=url,
                    headers=headers,
                    editors=editors)
                return redirect(url_for('.list'))
            except ValueError, ex:
                error_message = ex.message

    return render_template('connection_string/create_or_edit.html',
                           name=name,
                           headers=headers,
                           users=users,
                           url=url,
                           editors=editors,
                           error=error_message)

