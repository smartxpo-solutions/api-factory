import json


class Response:
    def __init__(self, data_json, *, status_code=200, is_binary=False, headers=None, encoder_class=None):
        self.headers = headers or {}
        self.data_json = data_json
        self.status_code = status_code
        self.is_binary = is_binary
        self.encoder_class = encoder_class

    @property
    def data(self):
        return json.dumps(self.data_json, cls=self.encoder_class)

    def to_aws_response(self):
        return {
            'isBase64Encoded': self.is_binary,
            'statusCode': self.status_code,
            'headers': self.headers,
            'body': self.data,
        }


class Http200Response(Response):
    status_code = 200

    def __init__(self, data_json, *, is_binary=False, headers=None, encoder_class=None):
        super(Http200Response, self).__init__(data_json, status_code=self.status_code, is_binary=is_binary,
                                              headers=headers, encoder_class=encoder_class)


class Http404Response(Response):
    status_code = 404

    def __init__(self, error_message, *, headers=None, encoder_class=None):
        data_json = {
            'message': error_message,
        }
        super(Http404Response, self).__init__(data_json, status_code=self.status_code, is_binary=False,
                                              headers=headers, encoder_class=encoder_class)
