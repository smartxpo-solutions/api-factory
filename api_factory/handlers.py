import os
import jwt
import json
import boto3
import base64
import logging

from typing import Type, Dict, Optional
from collections import namedtuple
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

from .forms import BaseInputForm, BaseOutputForm
from .exceptions import PermissionsError, ClientError, ServerError, AuthenticationError
from .logger import log_handler


logger = logging.getLogger('api-factory')
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)


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

    # event data
    event: Optional[Dict] = None

    # method description
    help: str = None

    # processed input data
    input_data: Dict

    # defined input form
    input_form: Type[BaseInputForm] = None

    # defined output form
    output_form: Type[BaseOutputForm] = None

    # HTTP method name: GET, POST, etc
    method = None

    @classmethod
    def get_lambda_handler(cls):
        """ Creates an entry point for AWS Lambda function """

        def _handler(event, context):
            response = cls().handle_request(event)

            headers = event.get('headers') or {}
            headers['Access-Control-Allow-Origin'] = '*'
            headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubdomains; preload'
            headers['Content-Security-Policy'] = "default-src 'none'; img-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'"
            headers['X-Content-Type-Options'] = 'nosniff'
            headers['X-Frame-Options'] = 'DENY'
            headers['X-XSS-Protection'] = '1; mode=block'
            headers['Referrer-Policy'] = 'same-origin'

            return {
                'isBase64Encoded': False,
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response)
            }

        return _handler

    def process_method(self, data: Dict):
        """ Process the input data according to the custom method """

        if self.method == 'GET':
            self.input_data = data.get('queryStringParameters') or {}
        else:
            self.input_data = json.loads(data.get('body')) if data.get('body') else {}

        # process the request data if input form added
        if self.input_form is not None:
            self.input_data = self.input_form.process(self.input_data)

        # run custom method handler
        response_data = self.handler()

        # process the response data if output form added
        if self.output_form is not None:
            response_data = self.output_form.process(response_data)

        return response_data

    def handle_request(self, event):
        """ Process the request and handle the response errors """

        self.event = event

        try:
            response_data = self.process_method(event)
            return success_response(response_data)

        except PermissionsError as e:
            logger.warning({'message': 'permissions is not valid', 'reason': e})
            return error_response(403, str(e))

        except AuthenticationError as e:
            logger.error({'message': 'auth error', 'reason': e})
            return error_response(401, str(e))

        except ClientError as e:
            logger.debug({'message': 'client error', 'reason': e})
            return error_response(400, str(e))

        # if any unexpected error raised, treat it as a server error
        # all expected errors should be processed accordingly to their nature
        except (ServerError, Exception) as e:
            logger.exception({'message': 'server error', 'reason': e}, exc_info=True)
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

    def process_method(self, data: Dict):
        # process the authentication if the method requires it
        if self.authentication:
            self.setup_requesting_user(data.get('headers') or {})

        return super(Auth0Authenticator, self).process_method(data)

    def setup_requesting_user(self, headers: Dict):
        """ Setup requesting user using JWT from the headers.
        Verify JWT and decode payload. Logs suspicious JWT troubles.
        """

        # check if user authenticated
        token = headers.get('Authorization')
        if not token:
            logger.warning({'message': 'JWT is missing', 'reason': 'missing "Authorization" header'})
            raise AuthenticationError()

        # XXX: temporary
        token = token.replace('Bearer ', '')

        # TODO: add more meaningful logging to catch suspicious requests
        try:
            # get a public key out from certificate key
            public_key = load_pem_x509_certificate(self.JWT_CERT_KEY, default_backend()).public_key()

            # verify jwt and decode payload
            token_payload = jwt.decode(token, public_key, verify=True, algorithms=['RS256'], audience=self.JWT_AUDIENCE)

        except jwt.InvalidSignatureError:
            logger.warning({'message': 'attempt to decode the wrong JWT'})
            raise AuthenticationError()

        except jwt.PyJWTError as e:
            logger.warning({'message': 'error while decoding the JWT', 'reason': e})
            raise AuthenticationError()

        user_email = token_payload.get('email')
        if not user_email:
            logger.warning({'message': 'user email is not found in the JWT payload'})
            raise AuthenticationError()

        email_verified = token_payload.get('email_verified')
        if not email_verified:
            logger.warning({'message': 'user email is not verified'})
            raise AuthenticationError()

        # TODO: validate jwt expiration
        # TODO: validate jwt issuer

        self.requesting_user = RequestingUser(user_email)


# helper class, combines common functional
BaseHandler = type('BaseHandler', (Auth0Authenticator, LambdaHandler), {})


class AuthHandler(BaseHandler):

    # client to call lambda directly
    lambda_client = boto3.client('lambda')

    def authorize(self, **payload):
        log_msg = dict(payload)
        response = self.call_lambda(name=os.environ['AUTHORIZER_FUNC'], payload=payload)
        if response['status'] == 'FAIL' or not response['body']['access_is_allowed']:
            log_msg.update({'message': 'permissions is not valid', 'user_email': self.requesting_user.email})
            logger.warning(log_msg)
            raise PermissionsError()

        log_msg.update({'message': 'permissions is valid', 'user_email': self.requesting_user.email})
        logger.info(log_msg)

    def call_lambda(self, name: str, payload: Dict=None):
        event = {
            'queryStringParameters': payload or {},
            'headers': self.event.get('headers') or {}
        }

        response = self.lambda_client.invoke(
            FunctionName=name, InvocationType='RequestResponse', Payload=json.dumps(event))
        response = json.loads(response['Payload'].read())
        return json.loads(response['body'])
