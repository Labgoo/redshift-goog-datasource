# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, Response, redirect, url_for, g
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
    result = r.json()

    if result.get("status") == "error":
        http_error_msgs = []
        for error in result.get("errors", []):
            http_error_msgs.append(error.get("detailed_message"))

        raise requests.HTTPError("\n".join(http_error_msgs), response=r)

    r.raise_for_status()

    return datatable_to_data(result)

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
    return Query.create_or_update(name = name,
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

def data_to_datatable(description, data):
    import gviz_api

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)

    return data_table

def datatable_to_data(data_table):
    table = data_table.get('table', data_table)
    description = table["cols"]

    def enum_rows():
        for row in table["rows"]:
            r = []
            for i,v in enumerate(row["c"]):
                val = v["v"] if v else None
                r.append((description[i]["id"], val))

            yield dict(r)

    data = [item for item in enum_rows()]

    def convert_description():
        for col in description:
            yield col["id"], (col["type"], col["label"])

    columns_order = [col["id"] for col in description]

    description = [item for item in convert_description()]

    return dict(description), data, columns_order

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
    return render_template('query/create_or_edit.html',
        sql = "",
        vars = [],
        connection = None,
        connections = ConnectionString.all(),
        editors = [])

@mod.route('/<name>', methods=['DELETE'])
def delete(name):
    query = Query.find(name)
    if query:
        query.delete()

    json_data = json.dumps({'status': 'ok'})
    return Response(json_data,  mimetype='application/json')

@mod.route('/', methods=['POST', 'GET'])
@mod.route('/<name>', methods=['POST', 'GET'])
def edit(name=None):

    user_access_token = request.args.get('access_token', request.form.get('access_token'))

    if not user_access_token and g.user is None:
        return redirect(url_for('user.login', next=request.path))

    execute_sql = request.method == 'POST'

    query = None

    redirect_to = None

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

        if not name and g.user is None:
            return redirect(url_for('user.login', next=request.path))

        connection_string = request.form.get('connection-string')
        connection = ConnectionString.find(connection_string, True)

        editors = get_editors()

        if name and request.form.get('user-action') == 'Save':
            if g.user is None:
                return redirect(url_for('user.login', next=request.path))

            query, created = save(name, sql, meta_vars, connection, editors)

            if created:
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

        query = Query.find(name, access_token=user_access_token)

        if not query:
            return redirect(url_for('.new'))

        sql = query.sql
        meta_vars = query.meta_vars
        connection = query.connection
        editors = query.editors

    data_table = None
    error = None
    json_data = None
    access_token = None
    if execute_sql:
        transform = request.args.get('transform', None)

        if not transform:
            transform = request.args.get('transformer', None)

        raw_data = not request.args.get('json', None) is None

        try:
            json_data = None

            if connection:
                if connection.url.startswith('google://') or connection.url.startswith('http://') or connection.url.startswith('https://'):
                    description, data, columns_order = query_google_data_source(connection, sql, meta_vars, vars)
                else:
                    description, data, columns_order = query_execute_sql(connection, sql, meta_vars, vars)

                if transform:
                    data = Transformer.execute(transform, data, True)

                if raw_data:
                    json_data = json.dumps(data, default=handle_datetime)
                elif len(data) > 0:
                    data_table = data_to_datatable(description, data)
                    json_data = data_table.ToJSon(columns_order=columns_order)

            if not json_data:
                json_data = json.dumps([])
                data_table = None

        except Exception, ex:
            logging.exception("Failed to execute query %s", ex)
            error = str(ex)

        if not request.args.get('gwiz', None) is None:
            if error:
                return Response(json.dumps({"error": error}), mimetype='application/json')

            return Response(data_table.ToJSonResponse(columns_order=columns_order),  mimetype='application/json')
        if not request.args.get('gwiz_json', None) is None:
            if error:
                return Response(json.dumps({"error": error}), mimetype='application/json')

            if data_table:
                return Response(data_table.ToJSon(columns_order=columns_order), mimetype='application/json')
            else:
                return Response('',  mimetype='application/json')

        if not request.args.get('json', None) is None:
            if error:
                return Response(json.dumps({"error": error}), mimetype='application/json')

            return Response(json_data,  mimetype='application/json')
        elif not request.args.get('html', None) is None:
            return Response(data_table.ToHtml(columns_order=columns_order))
        elif not request.args.get('csv', None) is None:
            return Response(data_table.ToCsv(columns_order=columns_order), mimetype='text/csv')

    full_vars = []
    vars = dict(vars)
    for key, options in meta_vars:
        val = vars.get(key)
        if val:
            full_vars.append((key, val))
        else:
            full_vars.append((key, None))

    if name:
        if query is None:
            query = Query.find(name, access_token=user_access_token)

        if query:
            access_token = query.access_token

    return render_template('query/create_or_edit.html',
        name = name,
        sql = sql,
        error = error,
        connection = connection,
        connections = ConnectionString.all() or [connection],
        meta_vars = meta_vars,
        editors = editors,
        access_token=access_token,
        vars = full_vars)