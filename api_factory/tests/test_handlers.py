import unittest
import json

from api_factory.exceptions import Http404
from api_factory.forms import BaseInputForm, BaseOutputForm
from api_factory.fields import StringField, IntegerField
from api_factory.handlers import LambdaHandler, success_response
from api_factory.responses import Response


class TestLambdaHandler(unittest.TestCase):

    def test_basic_request(self):

        class TestInputForm(BaseInputForm):
            email = StringField(required=True)

        class TestOutputForm(BaseOutputForm):
            age = IntegerField()

        class TestHandler(LambdaHandler):
            method = 'GET'
            input_form = TestInputForm
            output_form = TestOutputForm

            def handler(self):
                return {'age': len(self.input_data['email'])}

        lambda_handler = TestHandler.get_lambda_handler()

        response = json.loads(lambda_handler({'queryStringParameters': {'email': 'qwe@gmail.com'}}, None)['body'])
        expected_response = success_response({'age': 13})
        self.assertEqual(response, expected_response)

        response = json.loads(lambda_handler({'queryStringParameters': {}}, None)['body'])
        self.assertEqual(response['status'], 'FAIL')
        self.assertEqual(response['status_code'], 400)

    def test_response_errors(self):

        class TestInputForm(BaseInputForm):
            email = StringField(required=True)

        class TestOutputForm(BaseOutputForm):
            age = IntegerField()

        class TestHandler(LambdaHandler):
            method = 'GET'
            input_form = TestInputForm
            output_form = TestOutputForm

            def handler(self):
                return {'age': 'bad value'}

        lambda_handler = TestHandler.get_lambda_handler()

        response = json.loads(lambda_handler({'queryStringParameters': {'email': 'qwe@gmail.com'}}, None)['body'])
        self.assertEqual(response['status'], 'FAIL')
        self.assertEqual(response['status_code'], 500)

    def test_post_method(self):

        class TestInputForm(BaseInputForm):
            email = StringField(required=True)

        class TestHandler(LambdaHandler):
            method = 'POST'
            input_form = TestInputForm

            def handler(self):
                assert self.input_data['email'] == 'qwe@gmail.com'
                return {}

        lambda_handler = TestHandler.get_lambda_handler()

        response = json.loads(lambda_handler({'body': json.dumps({'email': 'qwe@gmail.com'})}, None)['body'])
        self.assertEqual(response['status'], 'OK')

    def test_http404_exception(self):
        class TestHandler(LambdaHandler):
            method = 'GET'

            def handler(self):
                raise Http404('Smth not found')

        lambda_handler = TestHandler.get_lambda_handler()

        response = lambda_handler({'queryStringParameters': {}}, None)

        self.assertFalse(response['isBase64Encoded'])
        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(json.loads(response['body']), {'message': 'Smth not found'})

    def test_return_response_object(self):
        class TestHandler(LambdaHandler):
            method = 'GET'

            def handler(self):
                return Response({'test': 'test'}, status_code=403)

        lambda_handler = TestHandler.get_lambda_handler()

        response = lambda_handler({'queryStringParameters': {}}, None)

        self.assertFalse(response['isBase64Encoded'])
        self.assertEqual(response['statusCode'], 403)
        self.assertEqual(json.loads(response['body']), {'test': 'test'})
