from dateutil.parser import parse


class Bunch(dict):
    def __init__(self, *args, **kwargs):
        super(Bunch, self).__init__(*args, **kwargs)
        self.__dict__ = self


def flatten(list_like):
    return [item for sublist in list_like for item in sublist]


def _show_change(date_time, old, new):
    date_time = parse(date_time)
    return "%s: %s ⇨ %s" % (date_time.strftime("%d/%m/%Y at %H:%M"), str(old), str(new))


def iter_history_changes(obj, field):
    changes = obj.json.get("history", {}).get(field, [])
    for d1, d2 in zip(changes, changes[1:]):
        yield _show_change(d1["date_time"], d1["value"], d2["value"])
    # Last change to current value.
    if changes:
        d = changes[-1]
        current = getattr(obj, field, None)
        yield _show_change(d["date_time"], d["value"], current)
