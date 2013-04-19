# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, g, Response, redirect, url_for
import logging, json
from user import require_login
from models import Application

mod = Blueprint('application', __name__, url_prefix='/application')

def save(name, description, domain, website, icon):
    logging.info('save application %s: %s', name)

    application, created = Application.objects.get_or_create(name=name)
    application.owner = g.user
    application.name = name
    application.description = description
    application.domain = domain
    application.website = website
    application.icon = icon

    application.save()

@mod.route('/list', methods=['GET'])
@require_login
def list():
    return render_template('application/list.html', application=Application.objects())

@mod.route('/new', methods=['GET'])
@require_login
def new():
    return render_template('application/new.html', application = None)

@mod.route('/', methods=['GET', 'POST'])
@mod.route('/<name>', methods=['GET', 'POST'])
@require_login
def edit(name=None):
    if request.method == 'GET':
        logging.info('loading application %s', name)
        if not name:
            return redirect(url_for('.new'))

        application = Application.find(name)
    else:
        name = request.form.get('name')
        description = request.form.get('description')
        domain = request.form.get('domain')
        website = request.form.get('website')
        icon = request.form.get('icon')

        if name == 'new':
            name = None

        if name:
            save(name, description, domain, website, icon)
            return redirect(url_for('.edit', name = name))

    return render_template('application/new.html',
                           application = application)

