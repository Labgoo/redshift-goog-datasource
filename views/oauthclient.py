# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, g, redirect, url_for
import logging
from oauth.provider import DataExplorerAuthorizationProvider
from user import require_login
from models import OAuthClient

mod = Blueprint('oauthclient', __name__, url_prefix='/oauthclient')

provider = DataExplorerAuthorizationProvider()

def save(name, description, domain, website, icon):
    logging.info('save application %s: %s', name)

    client, created = OAuthClient.objects.get_or_create(name=name)

    if created or not client.client_secret:
        client.client_secret = provider.generate_client_secret()

    client.owner = g.user
    client.name = name
    client.description = description
    client.domain = domain
    client.website = website
    client.icon = icon

    client.save()

@mod.route('/list', methods=['GET'])
@require_login
def list():
    return render_template('oauthclient/list.html', clients=OAuthClient.objects())

@mod.route('/new', methods=['GET'])
@require_login
def new():
    return render_template('oauthclient/new.html', client = None)

@mod.route('/', methods=['GET', 'POST'])
@mod.route('/<name>', methods=['GET', 'POST'])
@require_login
def edit(name=None):
    if request.method == 'GET':
        if not name:
            return redirect(url_for('.new'))

        client = OAuthClient.find(name)
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

    return render_template('oauthclient/new.html',
                           client = client)

