import unittest

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

        response = lambda_handler({'email': 'qwe@gmail.com'}, None)
        expected_response = success_response({'age': 13})
        self.assertEqual(response, expected_response)

        response = lambda_handler({}, None)
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
                return {'age': 'qwe'}

        lambda_handler = TestHandler.get_lambda_handler()

        response = lambda_handler({'email': 'qwe@gmail.com'}, None)
        self.assertEqual(response['status'], 'FAIL')
        self.assertEqual(response['status_code'], 500)
