import abc

from typing import Optional, List, Type, Set

from .exceptions import FieldValidationError


class BaseField(metaclass=abc.ABCMeta):

    # is a field is required
    required: bool

    # default field value (incompatible with required fields)
    default: Optional

    # field doc string
    help: Optional[str]

    def __init__(self, *, required: bool=False, default=None, help: str=None):
        self.required = required
        self.default = default
        self.help = help

    def validate(self, value):
        if not self.required:
            value = value if value is not None else self.default

        if value is None:
            return None

        return self.custom_validation(value)

    @abc.abstractmethod
    def custom_validation(self, value):
        pass


class StringField(BaseField):

    # restrict the value to be larger than min_length
    min_length: Optional[int]

    # restrict the value to be shorter than max_length
    max_length: Optional[int]

    def __init__(self, *, min_length: int=None, max_length: int=None, **kwargs):
        super(StringField, self).__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length

    def custom_validation(self, value):
        value = str(value)

        if self.min_length is not None and self.min_length > len(value):
            raise FieldValidationError('the value is shorter than min allowed length [%s]' % self.min_length)

        if self.max_length is not None and self.max_length < len(value):
            raise FieldValidationError('the value is larger than max allowed length [%s]' % self.max_length)

        return value


class BooleanField(BaseField):

    def custom_validation(self, value):
        value = bool(value)
        return value


class NumericField(BaseField):

    # abstract property to set the expected data type
    dtype = None

    # restrict the value to be higher than min_value
    min_value: Optional[float]

    # restrict the value to be lower than max_value
    max_value: Optional[float]

    def __init__(self, *, min_value: float=None, max_value: float=None, **kwargs):
        super(NumericField, self).__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def custom_validation(self, value):
        try:
            value = self.dtype(value)
        except ValueError:
            raise FieldValidationError('wrong data type')

        if self.min_value is not None and self.min_value > value:
            raise FieldValidationError('the value is lower than min allowed value [%s]' % self.min_value)

        if self.max_value is not None and self.max_value < value:
            raise FieldValidationError('the value is bigger than max allowed value [%s]' % self.max_value)

        return value


class FloatField(NumericField):
    dtype = float


class IntegerField(NumericField):
    dtype = int


class ListField(BaseField):

    # type of the list elements
    field_type: Type[BaseField]

    # is list may be empty
    blank: bool

    # restrict the list elements to a set of values
    valid_values: Optional[Set]

    def __init__(self, field_type: Type[BaseField], *, blank: bool=True, valid_values: Optional[Set]=None, **kwargs):
        super(ListField, self).__init__(**kwargs)
        self.field_type = field_type
        self.blank = blank
        self.valid_values = valid_values

    def custom_validation(self, values) -> List:
        try:
            field_type_obj = self.field_type()
            values = [field_type_obj.validate(val) for val in values]
        except TypeError:
            raise FieldValidationError('wrong data type')

        if not self.blank and not values:
            raise FieldValidationError('the value is blank')

        if self.valid_values is not None:
            unexpected_values = set(values) - set(self.valid_values)
            if unexpected_values:
                raise FieldValidationError("not allowed values: %s" % unexpected_values)

        return values
