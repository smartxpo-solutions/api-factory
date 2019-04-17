from typing import List, Dict

from .handlers import BaseHandler
from .fields import (BaseField, SubformField, ListSubformField, DictSubformField, StringField,
                     BooleanField, NumericField, FloatField, IntegerField, ListField, DictField, JSONField)


def get_field_type(field) -> str:
    if isinstance(field, StringField):
        return 'str'
    if isinstance(field, BooleanField):
        return 'bool'
    if isinstance(field, FloatField):
        return 'float'
    if isinstance(field, IntegerField):
        return 'int'
    if isinstance(field, JSONField):
        return 'json'
    if isinstance(field, ListField):
        return 'list[%s]' % get_field_type(field.field_type)
    if isinstance(field, DictField):
        return 'dict[%s]' % get_field_type(field.field_type)
    if isinstance(field, ListSubformField):
        return 'list subform'
    if isinstance(field, DictSubformField):
        return 'dict subform'
    if isinstance(field, SubformField):
        return 'subform'


def get_field_info(field: BaseField) -> Dict:
    docs = {
        'description': field.help,
        'required': field.required,
    }

    details = {'type': get_field_type(field)}
    if isinstance(field, SubformField):
        details['subform'] = collect_forms_documentation(field.subform)
    else:
        details['default'] = field.default
        # details['description'] = field.help
        # details['required'] = field.required

        if isinstance(field, StringField):
            details = {'min_length': field.min_length, 'max_length': field.max_length}
        elif isinstance(field, NumericField):
            details = {'min_value': field.min_value, 'max_value': field.max_value}
        elif isinstance(field, ListField):
            details = {'blank': field.blank, 'valid_values': field.valid_values}
        elif isinstance(field, DictField):
            details = {'blank': field.blank}

    docs['details'] = details
    return docs


def collect_forms_documentation(form) -> Dict:
    if form is not None:
        return {key: get_field_info(field) for key, field in form.fields}


def collect_documentation(handlers: List[BaseHandler]) -> List[Dict]:
    return [
        {
            'http_method': handler.method,
            'description': handler.help,
            'input': collect_forms_documentation(handler.input_form),
            'output': collect_forms_documentation(handler.output_form)
        } for handler in handlers
    ]
