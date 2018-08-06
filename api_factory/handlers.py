import os
import jwt
import base64
import logging

from typing import Type, Dict, Optional
from collections import namedtuple
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

from .forms import BaseInputForm, BaseOutputForm
from .exceptions import PermissionsError, ClientError, ServerError, AuthenticationError


logger = logging.getLogger('lambda.auth')


def error_response(status_code, reason):
    """ Defines an error response structure """

    return {
        'status': 'FAIL',
        'status_code': status_code,
        'reason': reason
    }


def success_response(body):
    """ Defines a success response structure """

    return {
        'status': 'OK',
        'body': body
    }


RequestingUser = namedtuple('RequestingUser', ['email'])


class LambdaHandler:
    """ Describes the common pattern of an API methods. Designed specifically for AWS Lambda. """

    # method description
    help: str = None

    # processed input data
    input_data: Dict

    # defined input form
    input_form: Type[BaseInputForm] = None

    # defined output form
    output_form: Type[BaseOutputForm] = None

    @classmethod
    def get_lambda_handler(cls):
        """ Creates an entry point for AWS Lambda function """

        def _handler(event, context):
            return cls().handle_request(event)

        return _handler

    def process_method(self, data: Dict):
        """ Process the input data according to the custom method """

        # process the request data if input form added
        if self.input_form is not None:
            self.input_data = self.input_form.process(data)

        # run custom method handler
        response_data = self.handler()

        # process the response data if output form added
        if self.output_form is not None:
            response_data = self.output_form.process(response_data)

        return response_data

    def handle_request(self, data):
        """ Process the request and handle the response errors """

        try:
            response_data = self.process_method(data)
            return success_response(response_data)

        except PermissionsError as e:
            logger.warning(e)
            return error_response(403, str(e))

        except AuthenticationError as e:
            logger.warning(e)
            return error_response(401, str(e))

        except ClientError as e:
            logger.debug(e)
            return error_response(400, str(e))

        # if any unexpected error raised, treat it as a server error
        # all expected errors should be processed accordingly to their nature
        except (ServerError, Exception) as e:
            logger.exception('unexpected error: %s' % e, exc_info=True)
            return error_response(500, 'server error')

    def handler(self) -> Dict:
        raise NotImplementedError()


class Auth0Authenticator:
    """ Mixin class for LambdaHandler based classes. Adds an Auth0 authentication. """

    # does authentication is required
    authentication: bool = True

    # requesting user info if user is authenticated
    requesting_user: Optional[RequestingUser] = None

    def __init__(self, *args, **kwargs):
        super(Auth0Authenticator, self).__init__(*args, **kwargs)

        # certification key encoded into base64 (used to verify the JWT)
        self.JWT_CERT_KEY = base64.b64decode(os.environ['JWT_CERT_KEY'].encode())

        # Auth0 audience (used to verify the JWT)
        self.JWT_AUDIENCE = os.environ['AUDIENCE']

    def process_request(self, data: Dict):
        # process the authentication if the method requires it
        if self.authentication:
            self.setup_requesting_user(data.get('header', {}))

        return super(Auth0Authenticator, self).process_request(data)

    def setup_requesting_user(self, headers: Dict):
        """ Setup requesting user using JWT from the headers.
        Verify JWT and decode payload. Logs suspicious JWT troubles.
        """

        # check if user authenticated
        token = headers.get('Authenticate')
        if not token:
            logger.warning('JWT is missing')
            raise AuthenticationError()

        # TODO: add more meaningful logging to catch suspicious requests
        try:
            # get a public key out from certificate key
            public_key = load_pem_x509_certificate(self.JWT_CERT_KEY, default_backend()).public_key()

            # verify jwt and decode payload
            token_payload = jwt.decode(token, public_key, verify=True, algorithms=['RS256'], audience=self.JWT_AUDIENCE)

        except jwt.InvalidSignatureError:
            logger.warning('attempt to decode the wrong JWT')
            raise AuthenticationError()

        except jwt.PyJWTError as e:
            logger.warning('error while decoding the JWT: %s', e)
            raise AuthenticationError()

        email_verified = token_payload.get('email_verified')
        if not email_verified:
            logger.warning('user email is not verified')
            raise AuthenticationError()

        user_email = token_payload.get('email')
        if not user_email:
            logger.warning('user email is not found in the token payload')
            raise AuthenticationError()

        # TODO: validate jwt expiration
        # TODO: validate jwt issuer

        self.requesting_user = RequestingUser(user_email)


# helper class, combines common functional
BaseHandler = type('BaseHandler', (Auth0Authenticator, LambdaHandler), {})
