# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, g, redirect, url_for, flash, session
import logging, json
import os
from flask_openid import OpenID, AX_MAPPING, ALL_KEYS
from app import app

from models import User
from openid.extensions.sreg import data_fields

mod = Blueprint('user', __name__, url_prefix='/user')

oid = OpenID(app)

@mod.route('/logout')
def logout():
    session.pop('openid', None)
    flash(u'You were signed out')
    return redirect(oid.get_next_url())

@mod.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    if g.user is not None or 'openid' not in session:
        return redirect(oid.get_next_url())

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if not name:
            flash(u'Error: you have to provide a name')
        elif '@' not in email:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            User.create(name, email, session['openid'], session.get('oauth_token'))
            return redirect(oid.get_next_url())

    return render_template('users/create_profile.html', next_url=oid.get_next_url())

@mod.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    AX_MAPPING['oauth-token'] = ['http://axschema.org/oauth-token']
    ALL_KEYS.add('oauth-token')
    data_fields['oauth-token'] = 'OAuth Token'

    if g.user is not None:
        return redirect(url_for('homepage.index'))

    if request.method == 'POST':
        openid = request.form.get('openid')
        if openid:
            return oid.try_login(openid,
                                 ask_for=['email', 'fullname', 'nickname'], nice_to_have=['oauth-token'])
    else:
        oid_url = os.environ.get('oid_url')
        if oid_url:
            return oid.try_login(oid_url,
                                 ask_for=['email', 'fullname', 'nickname'], nice_to_have=['oauth-token'])

    return render_template(
        'users/login.html',
        next=oid.get_next_url(),
        error=oid.fetch_error())

@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url

    args = request.args.to_dict()
    oauth_token = args.get('openid.sreg.oauth-token')

    if oauth_token:
        session['oauth_token'] = oauth_token

    user = User.get_by_openid(resp.identity_url)
    if user is not None:
        flash(u'Successfully signed in')

        if user.oauth_token != oauth_token:
            user.oauth_token = oauth_token
            user.save()

        g.user = user
        return redirect(oid.get_next_url())

    return redirect(url_for(
        '.create_profile',
        next=oid.get_next_url(),
        name=resp.fullname or resp.nickname,
        email=resp.email))

@app.before_request
def lookup_current_user():
    g.user = None
    if 'openid' in session:
        g.user = User.get_by_openid(session['openid'])
        session.user = g.user


from functools import wraps


def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('user.login', next=request.path))

        return f(*args, **kwargs)

    return decorated


from openid.fetchers import HTTPFetcher, setDefaultFetcher, HTTPResponse
from requests.adapters import HTTPAdapter, DEFAULT_POOLBLOCK
from requests.packages.urllib3.poolmanager import PoolManager
import requests
import ssl


class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK):
        super(MyAdapter, self).init_poolmanager(connections, maxsize, block)

        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_TLSv1)


class Urllib3Fetcher(HTTPFetcher):
    def fetch(self, url, body=None, headers=None):
        if headers is None:
            headers = {}

        s = requests.Session()
        s.mount('https://', MyAdapter())

        if body:
            r = s.request('post', url, data=body, headers=headers, verify=False)
        else:
            r = s.request('get', url, headers=headers, verify=False)

        return self._makeResponse(r)

    def _makeResponse(self, requests_response):
        resp = HTTPResponse()
        resp.body = requests_response.text
        resp.final_url = requests_response.url
        resp.headers = requests_response.headers
        resp.status = requests_response.status_code

        return resp

setDefaultFetcher(Urllib3Fetcher(), False)