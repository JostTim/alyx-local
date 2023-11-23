import structlog
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.http import HttpResponse
import io
from operator import attrgetter
from .water_control import water_control

logger = structlog.get_logger(__name__)


def return_figure(f):
    buf = io.BytesIO()
    f.savefig(buf, format="png")
    buf.seek(0)
    return HttpResponse(buf.read(), content_type="image/png")


def date_to_datetime(d):
    return datetime(d.year, d.month, d.day, 12, 0, 0)


def date_range(start_date, end_date):
    assert isinstance(start_date, datetime)
    assert isinstance(end_date, datetime)
    for n in range(int((end_date.date() - start_date.date()).days) + 1):
        yield (start_date + timedelta(n))


def to_date(s):
    if isinstance(s, str):
        return datetime.strptime("%s 12:00:00" % s, "%Y-%m-%d %H:%M:%S")
    elif isinstance(s, datetime):
        return s
    elif s is None:
        return s
    raise ValueError("The date should be either a string or a datetime.")


class TrainingControl(object):
    _columns = (
        "date",
        "number",
        "n_trials",
        "n_correct_trials",
        "success_rate",
        "is_trained",
    )

    def __init__(
        self,
        nickname=None,
        subject_id=None,
        timezone=timezone.get_default_timezone(),
        water_control=None,
    ):
        assert nickname, "Subject nickname not provided"
        self.nickname = nickname

        self.subject_id = subject_id

        self.sessions = []
        self.timezone = timezone
        self.water_control = water_control

    def date(self, session):
        return session.start_time

    def number(self, session):
        return str(session.number).zfill(3)

    def n_trials(self, session):
        return session.n_trials

    def n_correct_trials(self, session):
        return session.n_correct_trials

    def is_trained(self, session):
        return self.water_control.is_water_restricted(date=session.start_time)

    def success_rate(self, session):
        return (session.n_correct_trials / session.n_trials) * 100

    def add_sessions(self, sessions):
        sessions = list(sessions)
        if not len(sessions):
            return
        self.sessions.extend(sessions)
        self.sessions = sorted(self.sessions, key=attrgetter("start_time"))

    def to_jsonable(self):
        out = []
        for session in self.sessions:
            obj = {}
            for col in self._columns:
                obj[col] = getattr(self, col)(session)

            out.append(obj)
        return out

    def plot(self):
        import matplotlib

        matplotlib.use("AGG")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mpld
        from matplotlib import dates as mdates

        f, ax = plt.subplots(1, 1, figsize=(8, 3))

        dates = [self.date(session) for session in self.sessions]
        pefs = [self.success_rate(session) for session in self.sessions]

        ax.plot(dates, pefs, "-o", color="black", lw=2, label="sessions")

        ax.set_title(f"Performances for subject {self.nickname}")

        ax.set_xlabel("Date")
        ax.set_ylabel("Performance (%)")
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.grid(True)
        ax.legend()
        ax.set_ylim(0, 100)
        f.autofmt_xdate()
        f.tight_layout()
        return return_figure(f)


def training_control(subject):
    assert subject is not None

    # Create the WaterControl instance.
    wc = water_control(subject)

    tc = TrainingControl(
        nickname=subject.nickname,
        subject_id=subject.id,
        timezone=subject.timezone(),
        water_control=wc,
    )

    sessions = subject.actions_sessions.all().exclude(
        n_trials__isnull=True, n_correct_trials__isnull=True
    )

    tc.add_sessions(list(sessions))

    return tc
