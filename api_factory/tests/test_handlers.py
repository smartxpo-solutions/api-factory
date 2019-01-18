import unittest
import json

from ..forms import BaseInputForm, BaseOutputForm
from ..fields import StringField, IntegerField
from ..handlers import LambdaHandler, success_response


class TestLambdaHandler(unittest.TestCase):

    def test_basic_request(self):

        class TestInputForm(BaseInputForm):
            email = StringField(required=True)

        class TestOutputForm(BaseOutputForm):
            age = IntegerField()

        class TestHandler(LambdaHandler):
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
            input_form = TestInputForm
            output_form = TestOutputForm

            def handler(self):
                return {'age': 'bad value'}

        lambda_handler = TestHandler.get_lambda_handler()

        response = json.loads(lambda_handler({'queryStringParameters': {'email': 'qwe@gmail.com'}}, None)['body'])
        self.assertEqual(response['status'], 'FAIL')
        self.assertEqual(response['status_code'], 500)
