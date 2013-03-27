# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, g, Response, redirect, url_for
import logging, json
import pymongo, os

mod = Blueprint('query', __name__, url_prefix='/query')

def query_db(query, args):
	sql = query.format(**args)
	cur = g.db.execute(sql)
	rows = cur.fetchall()

	columns_order = [column for column, value in rows[0].items()]
	data = [dict((column, value) for column, value in row.items()) for row in rows]

	type_convert = {"unicode": "string", "string": "string", "long": "number"}
	description = dict([(name, (type_convert[type(value).__name__], name)) for name, value in data[0].iteritems()])	

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

def save_query(query_name, sql, meta_vars):
	data_explorer = get_mongo()
	data_explorer.queries.update(
		{'name': query_name}, 
		{"$set": {'sql': sql, 'meta_vars': meta_vars}},
		upsert = True);

def convert_value(val, type):
	if not val:
		return None

	if type == 'string':
		return val
	elif type == 'integer':
		return int(val)
	elif type == 'float':
		return float(val)

def vars_with_default_value(meta_vars, vars):
	result = {}
	for key, options in meta_vars.iteritems():
		val = vars.get(key)

		if not val:
			val = options.get('default')

		result[key] = convert_value(val, options['type'])

	return result

def query_execute_sql(sql, meta_vars, vars):
	meta_vars = dict(meta_vars)
	vars = dict(vars)

	vars = vars_with_default_value(meta_vars, vars)

	description, data, columns_order = query_db(sql, vars)

	import gviz_api

	data_table = gviz_api.DataTable(description)
	data_table.LoadData(data)

	return data_table, columns_order	

def load_sql(query_name):
	data_explorer = get_mongo()
	if data_explorer:
		query = data_explorer.queries.find_one({"name": query_name})

	meta_vars = query.get('meta_vars')

	sql = query.get('sql')

	return sql, meta_vars

@mod.route('/new', methods=['GET'])
def new_query():
	sql = "select str_targetcountry as country,count(*) as calls,sum(int_duration) as total_duration, sum(int_billsec) as total_billsec " + \
	"from socialism_online.cdrs_raw " + \
	"where int_year={Year} and int_month={Month} and int_day={Day} " + \
	"group by str_targetcountry " + \
	"order by str_targetcountry asc;"

	meta_vars=[
		("Year", {"type": "integer", "default": 2013}), 
		("Month", {"type": "integer", "default": 3}), 
		("Day", {"type": "integer", "default": 18})]

	vars = [('Year', None), ('Month', None), ('Day', None)]

	return render_template('query/new.html', 
		sql = sql,
		vars = vars,
		meta_vars = meta_vars)

@mod.route('/new', methods=['POST'])
@mod.route('/<query_name>', methods=['POST'])
def create_query(query_name=None):
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

	def vars_from_request(meta_vars, empty_vars):
		vars = []
		for name, options in meta_vars:
			value = request.form.get(name)

			if value:
				value = convert_value(value, options.get('type'))
			elif not empty_vars:
				continue

			vars.append((name, value))
		
		return vars

	meta_vars = extract_meta_var_fields()

	sql = request.form['sql']

	query_name = request.form.get('query-name')

	if query_name == 'new':
		query_name = None

	if query_name:
		save_query(query_name, sql, meta_vars)
		vars = vars_from_request(meta_vars, False)
		return redirect(url_for('.query_home', query_name = query_name, **dict(vars)))

	vars = vars_from_request(meta_vars, True)

	try:
		data_table, columns_order = query_execute_sql(sql, meta_vars, vars)
		json = data_table.ToJSon(columns_order=columns_order)
	except Exception, ex:
		logging.exception("Failed to execute query %s", ex)
		json = {}

	return render_template('query/new.html', 
		query_name = query_name, 
		json = json, 
		sql = sql, 
		meta_vars = meta_vars, 
		vars = vars)

@mod.route('/', methods=['GET'])
@mod.route('/<query_name>', methods=['GET'])
def query_home(query_name=None):
	if not query_name:
		return redirect(url_for('.new_query'))

	vars = []
	for key, value in request.args.iteritems():
		if not value:
			continue

		vars.append((key, value))

	sql, meta_vars = load_sql(query_name)

	try:
		data_table, columns_order = query_execute_sql(sql, meta_vars, vars)
		json = data_table.ToJSon(columns_order=columns_order)
	except Exception, ex:
		logging.exception("Failed to execute query %s", ex)
		return

	if not request.args.get('json', None) is None:
		return Response(data_table.ToJSonResponse(columns_order=columns_order),  mimetype='application/json')
	elif not request.args.get('html', None) is None:
		return Response(data_table.ToHtml(columns_order=columns_order))
	elif not request.args.get('csv', None) is None:
		return Response(data_table.ToCsv(columns_order=columns_order), mimetype='text/csv')
	else:
		json = data_table.ToJSon(columns_order=columns_order)
		
		full_vars = []
		vars = dict(vars)
		for key, options in meta_vars:
			val = vars.get(key)
			if val:
				full_vars.append((key, val))
			else:
				full_vars.append((key, None))

		return render_template('query/new.html', 
			query_name = query_name, 
			sql = sql, 
			json = json,
			meta_vars = meta_vars, 
			vars = full_vars)
		
