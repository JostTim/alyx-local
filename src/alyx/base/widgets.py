import json
from django.forms import Textarea


class JsonWidget(Textarea):
    def __init__(self, *args, **kwargs):
        kwargs["attrs"] = {"rows": 20, "cols": 60, "style": "font-family: monospace;"}
        super(JsonWidget, self).__init__(*args, **kwargs)

    def format_value(self, value):
        out = super(JsonWidget, self).format_value(value)
        if out is not None and out and not isinstance(out, dict):
            out = json.loads(out)
        out = json.dumps(out, indent=1)
        return out
