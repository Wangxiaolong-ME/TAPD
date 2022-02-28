import logging
import sys

import requests

sys.path.append('')


# API基于requests
class Api:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def get(self, url, params):
        response = requests.get(url, params=params, **self.kwargs)
        if response.status_code == 200:
            return response
        else:
            logging.warning(f"Api_get,url:{response.request.url},status_code:{response.status_code}")
            return False

    def post(self, url, data):
        response = requests.post(url, data=data, **self.kwargs)
        if response.status_code == 200:
            return response
        else:
            logging.warning(f"Api_get,body:{response.request.body},status_code:{response.status_code}")
            return False
