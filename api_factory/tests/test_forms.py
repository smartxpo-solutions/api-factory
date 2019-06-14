import unittest

from api_factory.forms import BaseInputForm, BaseOutputForm
from api_factory.fields import StringField, IntegerField, SubformField, DictSubformField, ListSubformField
from api_factory.exceptions import RequiredFieldError, InvalidValueError, ServerError


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

    def test_key_map(self):
        class TestForm(BaseOutputForm):
            email = StringField(key_map='user_email')
            age = IntegerField()

        output_data = TestForm.process({'age': 2, 'user_email': 'qwe@gmail.com'})
        expected_data = {'age': 2, 'email': 'qwe@gmail.com'}
        self.assertDictEqual(output_data, expected_data)

    def test_output_formats(self):

        class TestForm(BaseOutputForm):
            email = StringField()

        output_data = TestForm.process({'email': 'qwe@gmail.com'})
        expected_data = {'email': 'qwe@gmail.com'}
        self.assertEqual(output_data, expected_data)

        output_data = TestForm.process([{'email': 'qwe@gmail.com'}, {'email': 'asd@gmail.com'}])
        expected_data = [{'email': 'qwe@gmail.com'}, {'email': 'asd@gmail.com'}]
        self.assertEqual(output_data, expected_data)

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

    def test_subform_field(self):

        class TestSuborm(BaseOutputForm):
            email = StringField()

        class TestForm(BaseOutputForm):
            user = SubformField(TestSuborm)

        output_data = TestForm.process({'user': {'email': 'qwe@gmail.com'}})
        expected_data = {'user': {'email': 'qwe@gmail.com'}}
        self.assertDictEqual(output_data, expected_data)

        output_data = TestForm.process({'user': {}})
        expected_data = {'user': {'email': None}}
        self.assertDictEqual(output_data, expected_data)

        output_data = TestForm.process({'user': None})
        expected_data = {'user': None}
        self.assertDictEqual(output_data, expected_data)

    def test_dict_subform_field(self):

        class TestSuborm(BaseOutputForm):
            email = StringField()

        class TestForm(BaseOutputForm):
            users = DictSubformField(TestSuborm)

        output_data = TestForm.process({'users': {'Mike': {'email': 'qwe@gmail.com'}}})
        expected_data = {'users': {'Mike': {'email': 'qwe@gmail.com'}}}
        self.assertDictEqual(output_data, expected_data)

        output_data = TestForm.process({'users': {}})
        expected_data = {'users': {}}
        self.assertDictEqual(output_data, expected_data)

        output_data = TestForm.process({'users': None})
        expected_data = {'users': None}
        self.assertDictEqual(output_data, expected_data)

    def test_list_subform_field(self):

        class TestSuborm(BaseOutputForm):
            email = StringField()

        class TestForm(BaseOutputForm):
            users = ListSubformField(TestSuborm)

        output_data = TestForm.process({'users': [{'email': 'qwe@gmail.com'}]})
        expected_data = {'users': [{'email': 'qwe@gmail.com'}]}
        self.assertDictEqual(output_data, expected_data)

        output_data = TestForm.process({'users': []})
        expected_data = {'users': []}
        self.assertDictEqual(output_data, expected_data)

        output_data = TestForm.process({'users': None})
        expected_data = {'users': []}
        self.assertDictEqual(output_data, expected_data)
