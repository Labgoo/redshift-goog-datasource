# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, g, Response, redirect, url_for
import logging, json
import mongo, os

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
def queries():
	data_explorer = mongo.get_mongo()
	if data_explorer:
		transformers = data_explorer.transformers.find()
	else:
		transformers = []

	return render_template('transformer/list.html', transformers=transformers)


@mod.route('/new', methods=['GET'])
def new_transformer():
	code = "def process(data):\n  return data"

	return render_template('transformer/new.html', 
		code = code)

@mod.route('/', methods=['GET'])
@mod.route('/<transformer_name>', methods=['GET'])
def transformer_home(transformer_name=None):
	logging.info('loading transformer %s', transformer_name)
	if not transformer_name:
		return redirect(url_for('.new_transformer'))

	code = load_transformer(transformer_name)

	return render_template('transformer/new.html', 
		transformer_name = transformer_name, 
		code = code)

@mod.route('/new', methods=['POST'])
@mod.route('/<transformer_name>', methods=['POST'])
def create_transformer(transformer_name=None):
	code = request.form['code']

	transformer_name = request.form.get('transformer-name')

	if transformer_name == 'new':
		transformer_name = None

	if transformer_name:
		save_transformer(transformer_name, code)
		return redirect(url_for('.transformer_home', transformer_name = transformer_name))

	return render_template('transformer/new.html', 
		transformer_name = transformer_name, 
		code = code)

