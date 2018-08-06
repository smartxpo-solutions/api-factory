class FieldValidationError(Exception):
    pass


class ClientError(Exception):
    pass


class ServerError(Exception):
    pass


class PermissionsError(ClientError):
    def __init__(self, user_id, action):
        self.user_id = user_id
        self.action = action

    def __str__(self):
        return 'permission denied for the user [%s] to perform the action [%s]' % (self.user_id, self.action)


class RequiredFieldError(ClientError):
    def __init__(self, field):
        self.field = field

    def __str__(self):
        return '%s is required' % self.field


class InvalidValueError(ClientError):
    def __init__(self, field, value, reason=''):
        self.field = field
        self.value = value
        self.reason = reason

    def __str__(self):
        return 'invalid value [%s=%s] %s' % (self.field, self.value, self.reason)


class AuthenticationError(ClientError):
    def __str__(self):
        return 'authentication error'
