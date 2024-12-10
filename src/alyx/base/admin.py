from reversion.admin import VersionAdmin
from django.contrib import admin
from django.forms import Textarea, TextInput
from django.db.models import Model, UUIDField, CharField, JSONField, TextField
from django.urls import reverse
from zoneinfo import ZoneInfo
from datetime import datetime
from django.conf import settings


from .widgets import JsonWidget
from .adminsite import get_showed_apps_list


class BaseAdmin(VersionAdmin):
    formfield_overrides = {
        TextField: {"widget": Textarea(attrs={"rows": 8, "cols": 60})},
        JSONField: {"widget": JsonWidget},
        UUIDField: {"widget": TextInput(attrs={"size": 32})},
    }
    list_per_page = 50
    save_on_top = True
    show_full_result_count = False

    def __init__(self, *args, **kwargs):
        if self.fields and "json" not in self.fields:
            self.fields += ("json",)  # type: ignore
        super(BaseAdmin, self).__init__(*args, **kwargs)

    def get_changeform_initial_data(self, request):
        # The default start time, in the admin interface, should be in the timezone of the user.
        if not request.user.lab:
            return {}
        from ..misc.models import Lab

        lab_tz = ZoneInfo(Lab.objects.get(name=request.user.lab[0]).timezone)

        server_tz = ZoneInfo(settings.TIME_ZONE)  # server timezone
        now = datetime.now(tz=server_tz)  # convert datetime from naive to server timezone
        now = now.astimezone(lab_tz)  # convert to the lab timezone
        return {"start_time": now, "created_at": now, "date_time": now}

    def changelist_view(self, request, extra_context=None):
        category_list = get_showed_apps_list(admin.site.get_app_list(request))
        extra_context = extra_context or {}
        extra_context["mininav"] = [("", "-- jump to --")]
        extra_context["mininav"] += [(model["admin_url"], model["name"]) for model in category_list[0].models]
        return super(BaseAdmin, self).changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request, *args, **kwargs):
        if request.user.is_public_user:
            return False
        else:
            return super(BaseAdmin, self).has_add_permission(request, *args, **kwargs)

    def has_change_permission(self, request, obj=None):
        if request.user.is_public_user:
            return False
        if not obj:
            return True
        if request.user.is_superuser:
            return True
        # Find subject associated to the object.
        if hasattr(obj, "responsible_user"):
            subj = obj
        elif getattr(obj, "session", None):
            subj = obj.session.subject
        elif getattr(obj, "subject", None):
            subj = obj.subject
        else:
            return False
        resp_user = getattr(subj, "responsible_user", None)
        # List of allowed users for the subject.
        allowed = getattr(resp_user, "allowed_users", None)
        allowed = set(allowed.all() if allowed else [])
        if resp_user:
            allowed.add(resp_user)
        # Add the responsible user or user(s) to the list of allowed users.
        if hasattr(obj, "responsible_user"):
            allowed.add(obj.responsible_user)
        if hasattr(obj, "user"):
            allowed.add(obj.user)
        if hasattr(obj, "users"):
            for user in obj.users.all():
                allowed.add(user)
        return request.user in allowed


class BaseInlineAdmin(admin.TabularInline):
    show_change_link = True
    formfield_overrides = {
        TextField: {"widget": Textarea(attrs={"rows": 3, "cols": 30})},
        JSONField: {"widget": Textarea(attrs={"rows": 3, "cols": 30})},
        CharField: {"widget": TextInput(attrs={"size": 16})},
    }


def get_admin_url(obj: Model):
    if not obj:
        return "#"
    info = (obj._meta.app_label, obj._meta.model_name)
    return reverse("admin:%s_%s_change" % info, args=(obj.pk,))
