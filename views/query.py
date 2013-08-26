# -*- coding: utf-8 -*-

from flask import render_template, request, Blueprint, Response, redirect, url_for, g
import logging
import json
import os
from models import Query
from datetime import datetime
from models import Transformer, User
from user import require_login

mod = Blueprint('query', __name__, url_prefix='/query')


def query_google_data_source(connection, sql, meta_vars, query_vars):
    import requests

    url = connection.url
    if url.startswith('google://'):
        url = connection.url[len('google://'):]

    query = build_sql_query(sql, meta_vars, query_vars)

    url = url.replace('{query}', query)

    headers = {}

    if connection.headers:
        headers.update(json.loads(connection.headers))

    if g.user and g.user.oauth_token and headers.get('Authorization', None) is None:
        headers['Authorization'] = 'Token %s' % g.user.oauth_token

    r = requests.get(url, headers=headers)
    result = r.json()

    if result.get("status") == "error":
        http_error_msgs = []
        for error in result.get("errors", []):
            reason = error.get('reason')
            detailed_message = error.get("detailed_message")
            message = error.get("message")

            msg = []
            if reason:
                msg.append('%s:' % reason)

            if message:
                msg.append(message)

            if detailed_message:
                msg.append(detailed_message)

            http_error_msgs.append("\n".join(msg))

        raise requests.HTTPError("\n".join(http_error_msgs), response=r)

    r.raise_for_status()

    return datatable_to_data(result)


def build_sql_query(query, meta_vars, query_vars):
    meta_vars = dict(meta_vars)
    query_vars = dict(query_vars)

    query_vars = vars_with_default_value(meta_vars, query_vars)

    logging.info('execute query %s %s %s', query, query_vars, meta_vars)

    return query.format(**query_vars)


def query_db(connection, query,  meta_vars, query_vars):
    if not connection:
        raise ValueError('Missing Connection String')

    from sqlalchemy import create_engine

    db = create_engine(connection.url)
    sql = build_sql_query(query, meta_vars, query_vars)
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
    return Query.create_or_update(
        name=name,
        sql=sql,
        meta_vars=meta_vars,
        connection=connection,
        editors=editors)


def convert_value(val, val_type):
    if not val:
        return None

    if val_type == 'string':
        return val
    elif val_type == 'integer':
        return int(val)
    elif val_type == 'float':
        return float(val)


def vars_with_default_value(meta_vars, query_vars):
    result = {}
    for key, options in meta_vars.iteritems():
        val = query_vars.get(key)

        if not val:
            val = options.get('default')

        result[key] = convert_value(val, options['type'])

    return result


def data_to_datatable(description, data):
    import gviz_api

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)

    return data_table


def parse_date_string(val):
    parts = [int(v) for v in val[len("Date("):-1].split(',')]

    if len(parts) == 3:
        return datetime(parts[0], parts[1]+1, parts[2])

    if len(parts) == 6:
        return datetime(parts[0], parts[1]+1, parts[2],
                        parts[3], parts[4], parts[5])

    if len(parts) == 7:
        return datetime(parts[0], parts[1]+1, parts[2],
                        parts[3], parts[4], parts[5],
                        parts[6])


def datatable_to_data(data_table):
    table = data_table.get('table', data_table)
    description = table["cols"]

    def enum_rows():
        for row in table["rows"]:
            r = []
            for i, v in enumerate(row["c"]):
                val = v["v"] if v else None

                if isinstance(val, basestring) and val.startswith('Date('):
                    val = parse_date_string(val)

                r.append((description[i]["id"], val))

            yield dict(r)

    data = [item for item in enum_rows()]

    def convert_description():
        for col in description:
            yield col["id"], (col["type"], col["label"])

    columns_order = [col["id"] for col in description]

    description = [item for item in convert_description()]

    return dict(description), data, columns_order


def query_execute_sql(connection, sql, meta_vars, query_vars):
    description, data, columns_order = query_db(connection, sql, meta_vars, query_vars)

    return description, data, columns_order


@mod.route('/list', methods=['GET'])
@require_login
def list_items():
    queries = Query.all()

    return render_template('query/list.html', queries=queries)


def handle_datetime(obj):
    return obj.isoformat() if isinstance(obj, datetime) else None


def get_connections_factory():
    factory_class_name = os.environ.get('connections_class', 'models.ConnectionString')
    import importlib

    parts = factory_class_name.split(".")

    module_name = ".".join(parts[0:-1])
    class_name = parts[-1]
    module = importlib.import_module(module_name)

    return getattr(module, class_name)


def is_format_request(formats):
    if isinstance(formats, basestring):
        return request.args.get(formats, None) is not None

    for fmt in formats:
        if is_format_request(fmt):
            return True

    return False


def is_data_request():
    return is_format_request(['gwiz', 'json', 'csv', 'html', 'gwiz_json'])

@mod.route('/new', methods=['GET'])
@require_login
def new():
    return render_template(
        'query/create_or_edit.html',
        sql="",
        vars=[],
        connection=None,
        connections=get_connections_factory().all(),
        editors=[])


@mod.route('/<name>', methods=['DELETE'])
def delete(name):
    query = Query.find(name)
    if query:
        query.delete()

    json_data = json.dumps({'status': 'ok'})
    return Response(json_data,  mimetype='application/json')


def ajax_redirect(url):
    json_data = json.dumps({'redirect': url})
    return Response(json_data,  mimetype='application/json')


def ajax_redirect_on_post(url):
    is_post = request.method == 'POST'

    if is_post:
        return ajax_redirect(url)

    return redirect(url)


@mod.route('/', methods=['POST', 'GET'])
@mod.route('/<name>', methods=['POST', 'GET'])
def edit(name=None):
    user_access_token = request.args.get('access_token', request.form.get('access_token'))

    if not user_access_token and g.user is None:
        return redirect(url_for('user.login', next=request.path))

    execute_sql = request.method == 'POST' or is_data_request()

    query = None

    if request.method == 'POST':
        def extract_meta_var_fields():
            index = 0

            meta = []
            while True:
                name = request.form.get('var-name%d' % index)
                if not name:
                    return meta

                var_type = request.form.get('var-type%d' % index, 'string')
                default = request.form.get('var-default%d' % index, 'string')

                meta.append((name, {'default': default, 'type': var_type}))

                index += 1

        def vars_from_request(meta_vars, empty_vars):
            query_vars = []
            for name, options in meta_vars:
                value = request.form.get(name)

                if value:
                    value = convert_value(value, options.get('type'))
                elif not empty_vars:
                    continue

                query_vars.append((name, value))

            return query_vars

        def get_editors():
            editors = request.form.getlist('editors')
            if editors:
                users = User.get_by_username(editors)
                return users

            return []

        meta_vars = extract_meta_var_fields()

        sql = request.form['sql']

        name = request.form.get('query-name')

        if name == 'new':
            name = None

        if not name and g.user is None:
            return redirect(url_for('user.login', next=request.path))

        connection_string = request.form.get('connection-string')
        connection = get_connections_factory().find(connection_string, True)

        editors = get_editors()

        if name and request.form.get('user-action') == 'Save':
            if g.user is None:
                return ajax_redirect_on_post(url_for('user.login', next=request.path))

            query, created = save(name, sql, meta_vars, connection, editors)

            if created:
                full_vars = vars_from_request(meta_vars, False)
                return ajax_redirect(url_for('.edit', name=name, **dict(full_vars)))

        query_vars = vars_from_request(meta_vars, True)

    else:
        if not name:
            return redirect(url_for('.new'))

        query_vars = []
        for key, value in request.args.iteritems():
            if not value:
                continue

            query_vars.append((key, value))

        query = Query.find(name, access_token=user_access_token)

        if not query:
            return redirect(url_for('.new'))

        sql = query.sql
        meta_vars = query.meta_vars
        connection = query.connection
        editors = query.editors

    data_table = None
    error = None
    columns_order = None
    json_data = None
    access_token = None
    if execute_sql:
        transform = request.args.get('transform', None)

        if not transform:
            transform = request.args.get('transformer', None)

        try:
            json_data = None

            if connection:
                if connection.url.startswith('google://') or \
                        connection.url.startswith('http://') or \
                        connection.url.startswith('https://'):
                    description, data, columns_order = query_google_data_source(connection, sql, meta_vars, query_vars)
                else:
                    description, data, columns_order = query_execute_sql(connection, sql, meta_vars, query_vars)

                if transform:
                    data = Transformer.execute(transform, data, True)

                if is_format_request('json'):
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

        if is_format_request('gwiz'):
            if error:
                return Response(json.dumps({"error": error}), mimetype='application/json')

            return Response(data_table.ToJSonResponse(columns_order=columns_order),  mimetype='application/json')
        if is_format_request('gwiz_json'):
            if error:
                return Response(json.dumps({"error": error}), mimetype='application/json')

            if data_table:
                return Response(data_table.ToJSon(columns_order=columns_order), mimetype='application/json')
            else:
                return Response(json.dumps({"info": 'No results returned'}), mimetype='application/json')

        if is_format_request('json'):
            if error:
                return Response(json.dumps({"error": error}), mimetype='application/json')

            return Response(json_data,  mimetype='application/json')
        elif is_format_request('html'):
            return Response(data_table.ToHtml(columns_order=columns_order))
        elif is_format_request('csv'):
            return Response(data_table.ToCsv(columns_order=columns_order), mimetype='text/csv')

    full_vars = []
    query_vars = dict(query_vars)
    for key, options in meta_vars:
        val = query_vars.get(key)
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
        connections = get_connections_factory().all() or [connection],
        meta_vars = meta_vars,
        editors = editors,
        access_token=access_token,
        vars = full_vars)