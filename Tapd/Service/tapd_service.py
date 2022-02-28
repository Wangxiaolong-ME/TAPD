import sys

from Tapd.Config import config

sys.path.append('')

from Tapd.Service.api_service import Api


# TAPD接口配置
class TapdApiConfig(Api):
    def __init__(self, **kwargs):
        self.work_id = {
            "workspace_id": XXXXXX,
        }
        self.url = config.url
        super(TapdApiConfig, self).__init__(auth=config.auth, **kwargs)

    def tapd_get(self, path, **kwargs):
        # v_status 分割符
        if kwargs.__contains__("v_status"):
            if type(kwargs["v_status"]) is str:
                pass
            elif kwargs.get("v_status"):
                kwargs["v_status"] = "|".join(kwargs["v_status"])

        params = {
            **self.work_id,
            **kwargs
        }
        response = self.get(url=self.url + path, params=params)
        return response

    def tapd_post(self, path, **kwargs):
        data = {
            **self.work_id,
            **kwargs
        }
        response = self.post(url=self.url + path, data=data)
        return response


# TAPD接口调用
class TapdApi(TapdApiConfig):
    def __init__(self, **kwargs):
        super(TapdApi, self).__init__(**kwargs)

    def get_bugs(self, **kwargs):
        path = config.getbug
        response = self.tapd_get(path, **kwargs)
        return response

    def get_comments(self, **kwargs):
        path = config.comment
        response = self.tapd_get(path, **kwargs)
        return response

    def add_comments(self, **kwargs):
        path = config.comment
        data = {
            "author": "xxxxxx",
            "entry_type": "bug",
            **kwargs
        }
        response = self.tapd_post(path, **data)
        return response

    def upload(self, **kwargs):
        path = config.upload
        data = {
            "type": "bug",
            "owner": "xxxxxx",
            **kwargs
        }
        response = self.tapd_post(path, **data)
        return response

    def change_owner(self, **kwargs):
        path = config.getbug
        response = self.tapd_post(path, **kwargs)
        return response
