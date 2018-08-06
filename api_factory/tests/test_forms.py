import unittest

from ..forms import BaseInputForm, BaseOutputForm
from ..fields import StringField, IntegerField
from ..exceptions import RequiredFieldError, InvalidValueError, ServerError


class TestInputForms(unittest.TestCase):

    def test_required_fields(self):

        class TestForm(BaseInputForm):
            email = StringField(required=True)
            age = IntegerField()

        with self.assertRaises(RequiredFieldError):
            TestForm.process({'age': 2})

        with self.assertRaises(RequiredFieldError):
                TestForm.process({})

        input_data = TestForm.process({'email': 'test@gmail.com'})
        expected_data = {'email': 'test@gmail.com', 'age': None}
        self.assertDictEqual(input_data, expected_data)

        input_data = TestForm.process({'email': 'test@gmail.com', 'age': -1})
        expected_data = {'email': 'test@gmail.com', 'age': -1}
        self.assertDictEqual(input_data, expected_data)

    def test_input_errors(self):

        class TestForm(BaseInputForm):
            email = StringField(min_length=5)
            age = IntegerField(min_value=2)

        with self.assertRaisesRegex(InvalidValueError, 'email=1234'):
            TestForm.process({'email': '1234'})

        with self.assertRaisesRegex(InvalidValueError, 'age=1'):
            TestForm.process({'email': '12345', 'age': 1})

        with self.assertRaisesRegex(InvalidValueError, 'age=qwe'):
            TestForm.process({'email': '12345', 'age': 'qwe'})

        TestForm.process({'email': '12345', 'age': 2})
        TestForm.process({'age': 2})
        TestForm.process({'email': '12345'})

    def test_forms_inheritance(self):
        pass


class TestOutputForms(unittest.TestCase):

    def test_output_formats(self):

        class TestForm(BaseOutputForm):
            email = StringField()

        input_data = TestForm.process({'email': 'qwe@gmail.com'})
        expected_data = {'email': 'qwe@gmail.com'}
        self.assertEqual(input_data, expected_data)

        input_data = TestForm.process([{'email': 'qwe@gmail.com'}, {'email': 'asd@gmail.com'}])
        expected_data = [{'email': 'qwe@gmail.com'}, {'email': 'asd@gmail.com'}]
        self.assertEqual(input_data, expected_data)

    def test_output_errors(self):

        class TestForm(BaseOutputForm):
            email = StringField(min_length=5)
            age = IntegerField(min_value=2)

        with self.assertRaises(ServerError):
            TestForm.process({'email': '1234'})

        with self.assertRaises(ServerError):
            TestForm.process({'email': '12345', 'age': 1})

        with self.assertRaises(ServerError):
            TestForm.process({'email': '12345', 'age': 'qwe'})

        TestForm.process({'email': '12345', 'age': 2})
        TestForm.process({'age': 2})
        TestForm.process({'email': '12345'})
