import json
from django.test import Client


class JsonClient(Client):

    def __init__(self):
        super().__init__()
        self.token = None

    def post(self, *args, **kwargs):
        if self.token:
            kwargs['Authorization'] = 'Token %s' % self.token
        return super().post(*args, **kwargs)


    def json_post(self, url, json_data):
        headers = {'content_type': 'application/json'}
        return self.post(url, json.dumps(json_data), **headers)

    def get(self, *args, **kwargs):
        if self.token:
            kwargs['Authorization'] = 'Token %s' % self.token
        return super().get(*args, **kwargs)
