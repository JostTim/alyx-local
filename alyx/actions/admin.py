from django import forms
from django.contrib import admin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django.utils.html import format_html
from django.urls import reverse

from alyx.base import BaseAdmin, DefaultListFilter
from .models import *
from subjects.models import Subject
from subjects.admin import get_admin_url


class BaseActionAdmin(BaseAdmin):
    fields = ['subject', 'start_time', 'end_time', 'users',
              'location', 'procedures', 'narrative']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'subject':
            kwargs["queryset"] = Subject.objects.filter(responsible_user=request.user,
                                                        death_date=None,
                                                        ).order_by('nickname')
        return super(BaseActionAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ProcedureTypeAdmin(BaseActionAdmin):
    fields = ['name', 'description']


class WaterAdministrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(WaterAdministrationForm, self).__init__(*args, **kwargs)
        # Only show subjects that are on water restriction.
        self.fields['subject'].queryset = Subject.objects.filter(
            pk__in=[wr.subject.pk
                    for wr in WaterRestriction.objects.filter(start_time__isnull=False,
                                                              end_time__isnull=True)],
        )


class WaterAdministrationAdmin(BaseActionAdmin):
    fields = ['subject', 'date_time', 'water_administered', 'hydrogel', 'user']

    form = WaterAdministrationForm


class WeighingAdmin(BaseActionAdmin):
    list_display = ['subject_l', 'weight', 'date_time']
    fields = ['subject', 'date_time', 'weight', 'user', 'weighing_scale']
    ordering = ('-date_time',)
    list_display_links = ('weight',)
    readonly_fields = ['subject_l']

    def subject_l(self, obj):
        url = get_admin_url(obj.subject)
        return format_html('<a href="{url}">{subject}</a>', subject=obj.subject or '-', url=url)
    subject_l.short_description = 'subject'


# Filters
# ------------------------------------------------------------------------------------------------

class ResponsibleUserListFilter(DefaultListFilter):
    title = 'responsible user'
    parameter_name = 'responsible_user'

    def lookups(self, request, model_admin):
        return (
            (None, 'Me'),
            ('all', 'All'),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.filter(subject__responsible_user=request.user)
        elif self.value == 'all':
            return queryset.all()


class SubjectAliveListFilter(DefaultListFilter):
    title = 'alive'
    parameter_name = 'alive'

    def lookups(self, request, model_admin):
        return (
            (None, 'Yes'),
            ('n', 'No'),
            ('all', 'All'),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.filter(subject__death_date=None)
        if self.value() == 'n':
            return queryset.exclude(subject__death_date=None)
        elif self.value == 'all':
            return queryset.all()


class SurgeryAdmin(BaseActionAdmin):
    list_display = ['subject', 'date', 'users_l', 'procedures_l', 'narrative']
    fields = BaseActionAdmin.fields + ['brain_location', 'outcome_type']
    list_display_links = ['date']
    list_filter = [SubjectAliveListFilter,
                   ResponsibleUserListFilter,
                   ('subject__line', RelatedDropdownFilter),
                   ]

    def date(self, obj):
        return obj.start_time.date()
    date.admin_order_field = 'start_time'

    def users_l(self, obj):
        return ', '.join(map(str, obj.users.all()))
    users_l.short_description = 'users'

    def procedures_l(self, obj):
        return ', '.join(map(str, obj.procedures.all()))
    procedures_l.short_description = 'procedures'


admin.site.register(ProcedureType, ProcedureTypeAdmin)
admin.site.register(Weighing, WeighingAdmin)
admin.site.register(WaterAdministration, WaterAdministrationAdmin)

admin.site.register(Session, BaseActionAdmin)
admin.site.register(WaterRestriction, BaseActionAdmin)
admin.site.register(OtherAction, BaseActionAdmin)
admin.site.register(VirusInjection, BaseActionAdmin)

admin.site.register(Surgery, SurgeryAdmin)
