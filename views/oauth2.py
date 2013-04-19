import flask
from flask import request, g, render_template
from user import require_login
from flask import Blueprint
from models import AccessKey, Application

# This class will be defined later in this post
from oauth.provider import DataExplorerAuthorizationProvider

mod = Blueprint('oauth2', __name__, url_prefix='/oauth2')

# Authorization Code
# Returns a redirect header on success
@mod.route("/auth", methods=["GET"])
@require_login
def authorization_code():

    client_id = request.args.get('client_id')

    if not AccessKey.has_access(client_id, g.user.id):
        application = Application.find(client_id)
        return render_template('oauth/request.html', application=application)
    else:
        # You can cache this instance for efficiency
        provider = DataExplorerAuthorizationProvider()

        # This is the important line
        response = provider.get_authorization_code_from_uri(request.url)

        # For maximum compatibility, a standard Response object is provided
        # Response has the following properties:
        #
        #     response.status_code        int
        #     response.text               response body
        #     response.headers            iterable dict-like object with keys and values
        #
        # This response must be converted to a type that your application
        # framework can use and returned.
        flask_res = flask.make_response(response.text, response.status_code)
        for k, v in response.headers.iteritems():
            flask_res.headers[k] = v

        return flask_res

# Token exchange
# Returns JSON token information on success
@mod.route("/token", methods=["POST"])
def token():

    # You can cache this instance for efficiency
    provider = DataExplorerAuthorizationProvider()

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