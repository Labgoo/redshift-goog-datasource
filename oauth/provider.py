import json
import re
from flask import request, session
from models import OAuthClient
from pyoauth2.provider import AuthorizationProvider
import redis, os
from models import RefreshToken, AccessKey

class DataExplorerAuthorizationProvider(AuthorizationProvider):
    def __init__(self):
        super(DataExplorerAuthorizationProvider, self).__init__()

        redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')

        self.redis = redis.StrictRedis.from_url(redis_url)

    def validate_client_id(self, client_id):
        """Check that the client_id represents a valid application.

        :param client_id: Client id.
        :type client_id: str
        """
        return OAuthClient.find(client_id) is not None

    def validate_client_secret(self, client_id, client_secret):
        """Check that the client secret matches the application secret.

        :param client_id: Client Id.
        :type client_id: str
        :param client_secret: Client secret.
        :type client_secret: str
        """
        app = OAuthClient.find(client_id)
        if app is not None and app.secret == client_secret:
            return True

        return False

    def validate_redirect_uri(self, client_id, redirect_uri):
        """Validate that the redirect_uri requested is available for the app.

        :param redirect_uri: Redirect URI.
        :type redirect_uri: str
        """

        if redirect_uri == 'urn:ietf:wg:oauth:2.0:oob':
            return True

        app = OAuthClient.find(client_id)

        # When matching against a redirect_uri, it is very important to
        # ignore the query parameters, or else this step will fail as the
        # parameters change with every request
        if app is not None and app.domain == redirect_uri.split('?')[0]:
            return True

        return False

    def validate_access(self):
        """Validate that an OAuth token can be generated from the
        current session."""
        return session.user is not None

    def validate_scope(self, client_id, scope):
        """Validate that the scope requested is available for the app.

        :param client_id: Client id.
        :type client_id: str
        :param scope: Requested scope.
        :type scope: str
        """

        #TODO: validate scope

        return True

    def persist_authorization_code(self, client_id, code, scope):
        """Store important session information (user_id) along with the
        authorization code to later allow an access token to be created.

        :param client_id: Client Id.
        :type client_id: str
        :param code: Authorization code.
        :type code: str
        :param scope: Scope.
        :type scope: str
        """
        key = 'oauth2.authorization_code.%s:%s' % (client_id, code)

        # Store any information about the current session that is needed
        # to later authenticate the user.
        data = {'client_id': client_id,
                'scope': scope,
                'user_id': str(session.user.id)}

        # Authorization codes expire in 1 minute
        self.redis.setex(key, 60, json.dumps(data))

    def persist_token_information(self, client_id, scope, access_token,
                                  token_type, expires_in, refresh_token,
                                  data):
        """Save OAuth access and refresh token information.

        :param client_id: Client Id.
        :type client_id: str
        :param scope: Scope.
        :type scope: str
        :param access_token: Access token.
        :type access_token: str
        :param token_type: Token type (currently only Bearer)
        :type token_type: str
        :param expires_in: Access token expiration seconds.
        :type expires_in: int
        :param refresh_token: Refresh token.
        :type refresh_token: str
        :param data: Data from authorization code grant.
        :type data: mixed
        """

        # Set access token with proper expiration
        access_key = 'oauth2.access_token:%s' % access_token
        self.redis.setex(access_key, expires_in, json.dumps(data))

        # Set refresh token with no expiration
        token = RefreshToken.save(client_id, refresh_token, json.dumps(data))

        # Associate tokens to user for easy token revocation per app user
        AccessKey.save(client_id, data.get('user_id'), access_key, token)

    def from_authorization_code(self, client_id, code, scope):
        """Get session data from authorization code.

        :param client_id: Client ID.
        :type client_id: str
        :param code: Authorization code.
        :type code: str
        :param scope: Scope to validate.
        :type scope: str
        :rtype: dict if valid else None
        """
        key = 'oauth2.authorization_code.%s:%s' % (client_id, code)
        data = self.redis.get(key)
        if data is not None:
            data = json.loads(data)

            # Validate scope and client_id
            if (scope == '' or scope == data.get('scope')) and \
                            data.get('client_id') == client_id:
                return data

        return None  # The OAuth authorization will fail at this point

    def from_refresh_token(self, client_id, refresh_token, scope):
        """Get session data from refresh token.

        :param client_id: Client Id.
        :type client_id: str
        :param refresh_token: Refresh token.
        :type refresh_token: str
        :param scope: Scope to validate.
        :type scope: str
        :rtype: dict if valid else None
        """

        token = RefreshToken.find(client_id, refresh_token)
        if token is not None:
            data = json.loads(token.data)

            # Validate scope and client_id
            if (scope == '' or scope == data.get('scope')) and \
                            data.get('client_id') == client_id:
                return data

        return None  # The OAuth token refresh will fail at this point

    def discard_authorization_code(self, client_id, code):
        """Delete authorization code from the store.

        :param client_id: Client Id.
        :type client_id: str
        :param code: Authorization code.
        :type code: str
        """
        key = 'oauth2.authorization_code.%s:%s' % (client_id, code)
        self.redis.delete(key)

    def discard_refresh_token(self, client_id, refresh_token):
        """Delete refresh token from the store.

        :param client_id: Client Id.
        :type client_id: str
        :param refresh_token: Refresh token.
        :type refresh_token: str

        """
        RefreshToken.delete(client_id, refresh_token)

    def discard_client_user_tokens(self, client_id, user_id):
        """Delete access and refresh tokens from the store.

        :param client_id: Client Id.
        :type client_id: str
        :param user_id: User Id.
        :type user_id: str

        """

        AccessKey.delete(client_id, user_id)
