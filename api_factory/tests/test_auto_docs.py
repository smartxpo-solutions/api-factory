from unittest import TestCase

from ..handlers import BaseHandler
from ..forms import BaseInputForm, BaseOutputForm
from ..fields import StringField, BooleanField, ListField, SubformField
from ..auto_docs import collect_documentation


class TestAutoDocs(TestCase):
    maxDiff = None

    def test_simple_docs(self):
        class ReceiversSubform(BaseOutputForm):
            name = StringField(help='Receiver name')
            email = StringField(help='Receiver email')

        class TestOutputForm(BaseOutputForm):
            is_sent = BooleanField(help='Was the letter sent?')
            receivers = SubformField(ReceiversSubform, help='Receivers info')

        class SendEventReviewEmailInput(BaseInputForm):
            event_id = StringField(required=True, help='Event ID')
            edition_id = StringField(required=True, help='Edition ID')
            emails = ListField(StringField, required=True, blank=False, help='Receivers')
            body = StringField(required=True, min_length=5, help='Message body')

        class SendEventReviewEmailHandler(BaseHandler):
            help = 'Send a event review message to the event users'
            input_form = SendEventReviewEmailInput
            output_form = TestOutputForm
            method = 'POST'

            def handler(self):
                pass

        docs = collect_documentation([SendEventReviewEmailHandler])
        self.assertEqual(len(docs), 1)

        expected_docs = {'description': 'Send a event review message to the event users',
                         'http_method': 'POST',
                         'input': {'body': {'description': 'Message body',
                                            'details': {'max_length': None, 'min_length': 5},
                                            'required': True},
                                   'edition_id': {'description': 'Edition ID',
                                                  'details': {'max_length': None, 'min_length': None},
                                                  'required': True},
                                   'emails': {'description': 'Receivers',
                                              'details': {'blank': False, 'valid_values': None},
                                              'required': True},
                                   'event_id': {'description': 'Event ID',
                                                'details': {'max_length': None, 'min_length': None},
                                                'required': True}},
                         'output': {'is_sent': {'description': 'Was the letter sent?',
                                                'details': {'default': None, 'type': 'bool'},
                                                'required': False},
                                    'receivers': {'description': 'Receivers info',
                                                  'details': {'subform': {'email': {'description': 'Receiver '
                                                                                                   'email',
                                                                                    'details': {'max_length': None,
                                                                                                'min_length': None},
                                                                                    'required': False},
                                                                          'name': {'description': 'Receiver '
                                                                                                  'name',
                                                                                   'details': {'max_length': None,
                                                                                               'min_length': None},
                                                                                   'required': False}},
                                                              'type': 'subform'},
                                                  'required': False}}}
        self.assertDictEqual(docs[0], expected_docs)
