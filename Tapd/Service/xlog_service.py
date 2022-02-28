from Tapd.Config import config
from Tapd.Service.api_service import Api


class XlogApiConfig(Api):
    def __init__(self):
        super(XlogApiConfig, self).__init__()
        self.xlog_url = config.xlog_url
        self.params = {
            "qt": "query",
            "srvType": 1,
            "page": 0,
            "limit": 20
        }

    # xlog查询
    def search(self, qimei, begin_stamp, end_stamp):
        params = {
            **self.params,
            "qimei": qimei,
            "beginTime": begin_stamp,
            "endTime": end_stamp
        }
        response = self.get(self.xlog_url, params)
        return response

    def download(self, file_url):
        params = {
            "qt": "getpresignedurl",
            "srvType": 1,
            "fileURL": file_url
        }
        response = self.get(self.xlog_url, params)
        return response


class XlogApi(XlogApiConfig):

    def search_xlog(self, qimei, begin_stamp, end_stamp):
        response = self.search(qimei, begin_stamp, end_stamp)
        return response

    def download_xlog(self, file_url):
        response = self.download(file_url)
        return response
