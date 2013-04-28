# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, g, Response, redirect, url_for
import logging, json
from user import require_login
from models import Transformer, User

mod = Blueprint('transformer', __name__, url_prefix='/transformer')

def load(name):
    logging.info('load transformer %s', name)

    transformer = Transformer.find(name)

    if not transformer:
        return None

    return transformer

def save(name, code, editors):
    logging.info('save transformer %s: %s', name, code)

    Transformer.create_or_update(name, code, editors)


@mod.route('/list', methods=['GET'])
@require_login
def list():
    return render_template('transformer/list.html', transformeres=Transformer.all())


@mod.route('/new', methods=['GET'])
@require_login
def new():
    code = "#simple passthru transformer\nresult = []\n\nfor row in data:\n  result.append(row)"

    return render_template('transformer/create_or_edit.html',
                           code=code)


@mod.route('/', methods=['GET', 'POST'])
@mod.route('/<name>', methods=['GET', 'POST'])
@require_login
def edit(name=None):
    if request.method == 'GET':
        logging.info('loading transformer %s', name)
        if not name:
            return redirect(url_for('.new'))

        transformer = load(name)

        code = transformer.code
        editors = transformer.editors
    else:
        def get_editors():
            editors = request.form.get('editors', '').split(',')
            return User.get_by_username(editors)

        code = request.form['code']

        name = request.form.get('name')

        if name == 'new':
            name = None

        editors = get_editors()

        if name:
            save(name, code, editors)
            return redirect(url_for('.edit', name=name))

    return render_template('transformer/create_or_edit.html',
                           name=name,
                           code=code,
                           editors=editors)

