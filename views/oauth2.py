import flask
from flask import request, g, render_template
from user import require_login
from flask import Blueprint
from models import AccessKey, Application

# This class will be defined later in this post
from oauth.provider import DataExplorerAuthorizationProvider

mod = Blueprint('oauth', __name__, url_prefix='/oauth')

provider = DataExplorerAuthorizationProvider()

def code_request(get_response):
    response = get_response()

    location = response.headers.get('Location')

    if location.startswith('urn:ietf:wg:oauth:2.0:oob'):
        import urlparse

        query = location.split('?')[1]
        params = dict(urlparse.parse_qsl(query))
        code = params.get('code')
        return render_template('oauth/display_code.html',
                               code=code)
    else:
        return response

@mod.route("/submit", methods=["POST"])
@require_login
def submit_auth():
    if request.form.get('user_action', 'Reject') == 'Reject':
        return render_template('oauth/request_result.html',
                               title='Application Login Failure',
                               error='invalid_request',
                               description="user denied this authentication request")

    params = {}
    for key, val in request.form.iteritems():
        params[key] = val

    return code_request(lambda: provider.get_authorization_code_from_params(params))

# Authorization Code
# Returns a redirect header on success
@mod.route("/", methods=["GET"])
@require_login
def authorization_code():
    client_id = request.args.get('client_id')

    if not AccessKey.has_access(client_id, g.user.id):
        application = Application.find(client_id)
        scope = request.args.get('scope')
        response_type = request.args.get('response_type')
        redirect_uri = request.args.get('redirect_uri')
        return render_template('oauth/request.html',
                               application=application,
                               redirect_uri=redirect_uri,
                               scope=scope,
                               response_type=response_type)
    else:
        return code_request(lambda: provider.get_authorization_code_from_uri(request.url))

# Token exchange
# Returns JSON token information on success
@mod.route("/access_token", methods=["POST"])
def token():
    # Get a dict of POSTed form data
    data = {k: request.form[k] for k in request.form.iterkeys()}

    # This is the important line
    response = provider.get_token_from_post_data(data)

    # The same Response object is provided, and must be converted
    # to a type that your application framework can use and returned.
    flask_res = flask.make_response(response.text, response.status_code)
    for k, v in response.headers.iteritems():
        flask_res.headers[k] = v
    return flask_res