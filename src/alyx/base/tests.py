from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from collections import OrderedDict


class BaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        settings.DISABLE_MAIL = True
        call_command("loaddata", settings.DATA_DIR / "all_dumped_anon.json.gz", verbosity=1)

    def ar(self, r, code=200):
        """
        Asserts that HTTP status code matches expected value and parse data with or without
         pagination
        :param r: response object
        :param code: expected HTTP response code (default 200)
        :return: data: the data structure without pagination info if paginate activated
        """
        self.assertTrue(r.status_code == code, r.data)
        pkeys = {"count", "next", "previous", "results"}
        if isinstance(r.data, OrderedDict) and set(r.data.keys()) == pkeys:
            return r.data["results"]
        else:
            return r.data

    def post(self, *args, **kwargs):
        return self.client.post(*args, **kwargs, content_type="application/json")

    def patch(self, *args, **kwargs):
        return self.client.patch(*args, **kwargs, content_type="application/json")
