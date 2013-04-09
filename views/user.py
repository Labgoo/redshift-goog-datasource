# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, g, Response, redirect, url_for, flash, session
import logging, json
import os
from flask_openid import OpenID
from app import app

from models import User

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
			User.create(name, email, session['openid'])
			return redirect(oid.get_next_url())

	return render_template('users/create_profile.html', next_url=oid.get_next_url())

@mod.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
	if g.user is not None:
		return redirect(url_for('query.query_home'))

	if request.method == 'POST':
		openid = request.form.get('openid')
		if openid:
			return oid.try_login(openid, ask_for=['email', 'fullname',
												  'nickname'])
	return render_template(
		'users/login.html',
		next = oid.get_next_url(),
		error = oid.fetch_error())

@oid.after_login
def create_or_login(resp):
	session['openid'] = resp.identity_url
	user = User.get_by_openid(resp.identity_url)
	if user is not None:
		flash(u'Successfully signed in')
		g.user = user
		return redirect(oid.get_next_url())

	return redirect(url_for(
		'.create_profile', 
		next = oid.get_next_url(),
		name = resp.fullname or resp.nickname,
		email = resp.email))

@app.before_request
def lookup_current_user():
	g.user = None
	if 'openid' in session:
		g.user = User.get_by_openid(session['openid'])