# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, g, Response, redirect, url_for
import logging, json
import pymongo, os

mod = Blueprint('query', __name__, url_prefix='/query')

def query_db(query, args):
	sql = query.format(**args)
	cur = g.db.execute(sql)
	data = [dict((column, value) for column, value in row.items()) for row in cur.fetchall()]

	type_convert = {"unicode": "string", "string": "string", "long": "number"}
	description = dict([(name, (type_convert[type(value).__name__], name)) for name, value in data[0].iteritems()])
	columns_order = [name for name, value in data[0].items()]

	return description, data, columns_order

def get_mongo():	
	from pymongo import MongoClient, uri_parser

	mongolab_uri = os.environ['MONGOLAB_URI']
	url = uri_parser.parse_uri(mongolab_uri)
	MONGODB_USERNAME = url['username']
	MONGODB_PASSWORD = url['password']
	MONGODB_HOST, MONGODB_PORT = url['nodelist'][0]
	MONGODB_DB = url['database']

	connection = MongoClient(MONGODB_HOST, MONGODB_PORT)
	db = connection[MONGODB_DB]
	if MONGODB_USERNAME:
		db.authenticate(MONGODB_USERNAME, MONGODB_PASSWORD)

	return db

def vars_from_meta_vars(meta_vars):
	def convert_value(val, type):
		if not val:
			return None

		if type == 'string':
			return val
		elif type == 'integer':
			return int(val)
		elif type == 'float':
			return float(val)

	vars = []
	for name, options in meta_vars:
		value = request.form.get(name, options.get('default'))
		value = convert_value(value, options.get('type'))
		vars.append((name, value))
	
	return vars

@mod.route('/', methods=['GET'])
@mod.route('/<query_name>', methods=['GET'])
def query_home(query_name=None):
	if not query_name:
		return redirect(url_for('.new_query'))

	data_explorer = get_mongo()
	if data_explorer:
		query = data_explorer.queries.find_one({"name": query_name})

	meta_vars = query.get('meta_vars')
	vars = vars_from_meta_vars(meta_vars)

	return render_template('query/new.html', 
		query_name=query_name, 
		sql=query.get('sql'), 
		meta_vars=meta_vars, 
		vars=vars)

@mod.route('/new', methods=['GET'])
def new_query():
	sql = "select str_targetcountry as country,count(*) as calls,sum(int_duration) as total_duration, sum(int_billsec) as total_billsec " + "from socialism_online.cdrs_raw " + "where int_year=2013 and int_month=3 and int_day=18 " + "group by str_targetcountry " + "order by str_targetcountry asc;"

	return render_template('query/new.html', sql=sql)

@mod.route('/', methods=['POST'])
def create_query():
	def extract_meta_var_fields():
		index = 0

		meta = []
		while True:
			name = request.form.get('var-name%d' % index)
			if not name:
				return meta

			type = request.form.get('var-type%d' % index, 'string')
			default = request.form.get('var-default%d' % index, 'string')

			meta.append((name, {'default': default, 'type': type}))

			index += 1

	meta_vars = extract_meta_var_fields()

	vars = vars_from_meta_vars(meta_vars)

	sql = request.form['sql']

	import gviz_api
	description, data, columns_order = query_db(sql, dict(vars))
	
	data_table = gviz_api.DataTable(description)
	data_table.LoadData(data)

	json_data = data_table.ToJSon(columns_order=columns_order)

	query_name = request.form.get('query-name')

	if query_name:
		data_explorer = get_mongo()
		if data_explorer:
			data_explorer.queries.update(
				{'name': query_name}, 
				{"$set": {'sql': sql, 'meta_vars': meta_vars}},
				upsert = True);

			return redirect(url_for('.query_home', query_name=query_name))

	return render_template('query/new.html', query_name=query_name, json=json_data, sql=sql, meta_vars=meta_vars, vars=vars)