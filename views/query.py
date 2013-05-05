# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, Response, redirect, url_for
import logging, json
from models import Query
from datetime import datetime, timedelta
from models import Transformer, ConnectionString, User
from user import require_login

mod = Blueprint('query', __name__, url_prefix='/query')

def query_google_data_source(connection, sql, meta_vars, vars):
    import requests

    url = connection.url
    if url.startswith('google://'):
        url = connection.url[len('google://'):]

    query = build_sql_query(sql, meta_vars, vars)

    url = url.replace('{query}', query)

    headers = json.loads(connection.headers)

    r = requests.get(url, headers=headers)
    r.raise_for_status()

    return datatable_to_data(r.json())

def build_sql_query(query, meta_vars, vars):
    meta_vars = dict(meta_vars)
    vars = dict(vars)

    vars = vars_with_default_value(meta_vars, vars)

    logging.info('execute query %s %s %s', query, vars, meta_vars)

    return query.format(**vars)

def query_db(connection, query,  meta_vars, vars):
    if not connection:
        raise ValueError('Missing Connection String')

    from sqlalchemy import create_engine

    db = create_engine(connection.url)
    sql = build_sql_query(query, meta_vars, vars)
    cur = db.execute(sql)
    rows = cur.fetchall()

    if len(rows) > 0:
        columns_order = [column for column, value in rows[0].items()]
    else:
        columns_order = []

    data = [dict((column, value) for column, value in row.items()) for row in rows]

    type_convert = {"NoneType": "string",
                    "unicode": "string",
                    "string": "string",
                    "long": "number",
                    "int": "number",
                    "datetime": "datetime",
                    "bool": "boolean",
                    "float": "number"}
        
    if len(data) > 0:
        description = dict([(name, (type_convert[type(value).__name__], name)) for name, value in data[0].iteritems()])
    else:
        description = {}

    return description, data, columns_order

def save(name, sql, meta_vars, connection, editors):
    Query.create_or_update(name = name,
                           sql = sql,
                           meta_vars = meta_vars,
                           connection = connection,
                           editors = editors)

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

def data_to_datatable(description, data, columns_order):
    import gviz_api

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)

    return data_table, columns_order

def datatable_to_data(data_table):
    table = data_table.get('table', data_table)
    description = table["cols"]

    def enum_rows():
        for row in table["rows"]:
            r = []
            for i,v in enumerate(row["c"]):
                r.append((description[i]["id"], v["v"]))

            yield dict(r)

    data = [item for item in enum_rows()]

    def convert_description():
        for col in description:
            yield col["id"], (col["type"], col["label"])

    description = [item for item in convert_description()]

    return dict(description), data, None

def query_execute_sql(connection, sql, meta_vars, vars):
    description, data, columns_order = query_db(connection, sql, meta_vars, vars)

    return description, data, columns_order

@mod.route('/list', methods=['GET'])
@require_login
def list():
    queries = Query.all()

    return render_template('query/list.html', queries=queries)

def handle_datetime(obj):
    return obj.isoformat() if isinstance(obj, datetime) else None

@mod.route('/new', methods=['GET'])
@require_login
def new():
    sql = "select * from socialism_online.cdrs_raw \n" + \
          "where\n\textract(year from dt_timestamp)={Year} and \n" + \
          "\textract(month from dt_timestamp)={Month} and \n" + \
          "\textract(day from dt_timestamp)={Day}"

    yesterday = datetime.today() - timedelta(days=1)
    meta_vars=[
        ("Year", {"type": "integer", "default": yesterday.year}),
        ("Month", {"type": "integer", "default": yesterday.month}),
        ("Day", {"type": "integer", "default": yesterday.day})]

    vars = [('Year', None), ('Month', None), ('Day', None)]

    return render_template('query/create_or_edit.html',
        sql = sql,
        vars = vars,
        connection = None,
        connections = ConnectionString.all(),
        editors = [],
        meta_vars = meta_vars)

@mod.route('/', methods=['POST', 'GET'])
@mod.route('/<name>', methods=['POST', 'GET'])
@require_login
def edit(name=None):
    if request.method == 'POST':
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

        def get_editors():
            editors = request.form.get('editors', '').split(',')
            return User.get_by_username(editors)

        meta_vars = extract_meta_var_fields()

        sql = request.form['sql']

        name = request.form.get('query-name')

        if name == 'new':
            name = None

        connection = ConnectionString.find(request.form.get('connection-string'))

        editors = get_editors()

        if name and request.form.get('user-action') == 'Save + Execute':
            save(name, sql, meta_vars, connection, editors)
            full_vars = vars_from_request(meta_vars, False)
            return redirect(url_for('.edit', name = name, **dict(full_vars)))

        vars = vars_from_request(meta_vars, True)
    else:
        if not name:
            return redirect(url_for('.new'))

        vars = []
        for key, value in request.args.iteritems():
            if not value:
                continue

            vars.append((key, value))

        query = Query.find(name)

        if not query:
            return redirect(url_for('.new'))

        sql = query.sql
        meta_vars = query.meta_vars
        connection = query.connection
        editors = query.editors

    transform = request.args.get('transform', None)

    raw_data = not request.args.get('json', None) is None

    try:
        json_data = None

        if connection:
            if connection.url.startswith('google://') or connection.url.startswith('http://') or connection.url.startswith('https://'):
                description, data, columns_order = query_google_data_source(connection, sql, meta_vars, vars)
            else:
                description, data, columns_order = query_execute_sql(connection, sql, meta_vars, vars)

            if transform:
                data = Transformer.execute(transform, data)

            if raw_data:
                json_data = json.dumps(data, default=handle_datetime)
            elif len(data) > 0:
                data_table, columns_order = data_to_datatable(description, data, columns_order)
                json_data = data_table.ToJSon(columns_order=columns_order)

        if not json_data:
            json_data = json.dumps([])
            data_table = None

        error = ''
    except Exception, ex:
        logging.error("Failed to execute query %s", ex)
        error = str(ex)
        data_table = None

    if not request.args.get('gwiz', None) is None:
        return Response(data_table.ToJSonResponse(columns_order=columns_order),  mimetype='application/json')
    if not request.args.get('json', None) is None:
        if error:
            return Response(error)

        return Response(json_data,  mimetype='application/json')
    elif not request.args.get('html', None) is None:
        return Response(data_table.ToHtml(columns_order=columns_order))
    elif not request.args.get('csv', None) is None:
        return Response(data_table.ToCsv(columns_order=columns_order), mimetype='text/csv')
    else:
        full_vars = []
        vars = dict(vars)
        for key, options in meta_vars:
            val = vars.get(key)
            if val:
                full_vars.append((key, val))
            else:
                full_vars.append((key, None))

    return render_template('query/create_or_edit.html',
        name = name,
        sql = sql,
        error = error,
        json = json_data,
        connection = connection,
        connections = ConnectionString.all(),
        meta_vars = meta_vars,
        editors = editors,
        vars = full_vars)