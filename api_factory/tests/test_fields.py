import unittest

from api_factory.fields import StringField, FloatField, IntegerField, ListField, BooleanField, DictField
from api_factory.exceptions import FieldValidationError


class TestFields(unittest.TestCase):

    def assert_validation_error(self, field, value):
        with self.assertRaises(FieldValidationError):
            field.validate(value)

    def test_default_value(self):
        self.assertEqual(StringField(default='qwe').validate(None), 'qwe')
        self.assertEqual(FloatField(default=1.2).validate(None), 1.2)
        self.assertEqual(IntegerField(default=1).validate(None), 1)
        self.assertEqual(ListField(StringField, default=['1', '2']).validate(None), ['1', '2'])

        self.assertEqual(StringField(default='qwe', required=True).validate(None), None)
        self.assertEqual(FloatField(default=1.2, required=True).validate(None), None)
        self.assertEqual(IntegerField(default=1, required=True).validate(None), None)
        self.assertEqual(ListField(StringField, default=['1', '2'], required=True).validate(None), None)

    def test_empty_values(self):
        self.assertEqual(StringField().validate(None), None)
        self.assertEqual(FloatField().validate(None), None)
        self.assertEqual(IntegerField().validate(None), None)
        self.assertEqual(ListField(StringField).validate(None), None)

    def test_string_field(self):
        field = StringField(min_length=3, max_length=5)
        self.assert_validation_error(field, '12')
        self.assert_validation_error(field, '123456')
        self.assertEqual(field.validate('123'), '123')
        self.assertEqual(field.validate('12345'), '12345')

    def test_boolean_field(self):
        field = BooleanField()
        self.assertTrue(field.validate(True))
        self.assertFalse(field.validate(False))
        self.assertTrue(field.validate('qwe'))

    def test_float_field(self):
        field = FloatField(min_value=3, max_value=5)
        self.assert_validation_error(field, 'qwe')
        self.assert_validation_error(field, '12qwe')
        self.assert_validation_error(field, '12,2')
        self.assertEqual(field.validate('3'), 3)
        self.assertEqual(field.validate('3.5'), 3.5)
        self.assertEqual(field.validate(3), 3)
        self.assertEqual(field.validate(3.5), 3.5)

    def test_integer_field(self):
        field = IntegerField(min_value=3, max_value=5)
        self.assert_validation_error(field, 'qwe')
        self.assert_validation_error(field, '12qwe')
        self.assert_validation_error(field, '12.2')
        self.assertEqual(field.validate('3'), 3)
        self.assertEqual(field.validate(3), 3)
        self.assertEqual(field.validate(3.5), 3)

    def test_list_field(self):
        field = ListField(StringField)
        self.assert_validation_error(field, 123)
        self.assertEqual(field.validate(['qw', 123]), ['qw', '123'])

        field = ListField(IntegerField)
        self.assert_validation_error(field, 123)
        self.assert_validation_error(field, ['1q'])
        self.assert_validation_error(field, ['1.1'])
        self.assertEqual(field.validate(['1', 2, 3.3]), [1, 2, 3])

        field = ListField(FloatField)
        self.assert_validation_error(field, 123)
        self.assert_validation_error(field, ['1q'])
        self.assertEqual(field.validate(['1', '1.1', 2, 3.3]), [1, 1.1, 2, 3.3])

    def test_dict_field(self):
        field = DictField(StringField)
        self.assert_validation_error(field, 123)
        self.assert_validation_error(field, 'abc')
        self.assertEqual(field.validate({'a': 'b'}), {'a': 'b'})

    def test_blank_list_field(self):
        field = ListField(StringField, blank=True)
        self.assertEqual(field.validate([]), [])

        field = ListField(StringField, blank=False)
        self.assert_validation_error(field, [])

    def test_valid_values_list_field(self):
        field = ListField(StringField, valid_values={'a', 'b'})
        self.assert_validation_error(field, ['c'])
        self.assert_validation_error(field, ['a', 'c'])
        self.assertEqual(field.validate(['a', 'b']), ['a', 'b'])
