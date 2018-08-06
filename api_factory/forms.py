from typing import Dict, List, Tuple

from .exceptions import InvalidValueError, RequiredFieldError, ServerError, FieldValidationError
from .fields import BaseField


class FormsMeta(type):

    def __init__(cls, name, bases, attrs):
        super(FormsMeta, cls).__init__(name, bases, attrs)

        # collects all the defined form fields
        cls.fields = [(key, field) for key, field in attrs.items() if not key.startswith('__')]


class BaseInputForm(metaclass=FormsMeta):

    # aggregated all the defined fields
    fields: List[Tuple[str, BaseField]] = None

    @classmethod
    def process(cls, input_data: Dict) -> Dict:
        processed_data = {}

        for key, field in cls.fields:
            value = input_data.get(key)

            # validate required fields
            if field.required and not value:
                raise RequiredFieldError(key)

            # validate field value
            try:
                processed_data[key] = field.validate(value)
            except FieldValidationError as e:
                raise InvalidValueError(key, value, str(e))

        return processed_data


class BaseOutputForm(metaclass=FormsMeta):

    # aggregated all the defined fields
    fields: List[Tuple[str, BaseField]] = None

    @classmethod
    def process(cls, output_data):
        """ Processing different types of response: dict response and list of dicts """

        if isinstance(output_data, dict):
            return cls.process_form(output_data)
        elif isinstance(output_data, (list, tuple)):
            return [cls.process_form(data) for data in output_data]

    @classmethod
    def process_form(cls, output_data: Dict) -> Dict:
        processed_data = {}

        for key, field in cls.fields:
            value = output_data.get(key)

            # validate field value
            try:
                processed_data[key] = field.validate(value)
            except FieldValidationError as e:
                raise ServerError('invalid value [%s=%s] %s' % (key, value, str(e)))

        return processed_data
