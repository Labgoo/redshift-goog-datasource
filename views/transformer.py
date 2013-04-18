# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, g, Response, redirect, url_for
import logging, json
import mongo, os
from user import require_login

mod = Blueprint('transformer', __name__, url_prefix='/transformer')

def load_transformer(transformer_name):
	logging.info('load transformer %s', transformer_name)

	data_explorer = mongo.get_mongo()
	if data_explorer:
		transformer = data_explorer.transformers.find_one({"name": transformer_name})

	if not transformer:
		return None

	code = transformer.get('code')

	return code

def save_transformer(transformer_name, code):
	logging.info('save transformer %s: %s', transformer_name, code)

	data_explorer = mongo.get_mongo()
	data_explorer.transformers.update(
		{'name': transformer_name}, 
		{"$set": {'code': code}},
		upsert = True);

@mod.route('/list', methods=['GET'])
@require_login
def list():
	data_explorer = mongo.get_mongo()
	if data_explorer:
		transformers = data_explorer.transformers.find()
	else:
		transformers = []

	return render_template('transformer/list.html', transformers=transformers)


@mod.route('/new', methods=['GET'])
@require_login
def new():
	code = "def process(data):\n  return data"

	return render_template('transformer/new.html', 
		code = code)

@mod.route('/', methods=['GET', 'POST'])
@mod.route('/<name>', methods=['GET', 'POST'])
@require_login
def edit(name=None):
	if request.method == 'GET':
		logging.info('loading transformer %s', name)
		if not name:
			return redirect(url_for('.new'))

		code = load_transformer(name)
	else:
		code = request.form['code']

		name = request.form.get('name')

		if name == 'new':
			name = None

		if name:
			save_transformer(name, code)
			return redirect(url_for('.edit', name = name))

	return render_template('transformer/new.html', 
		name = name, 
		code = code)

