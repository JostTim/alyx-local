# Generated by Django 2.1.1 on 2018-10-15 09:14

from alyx.actions import models as action_models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("misc", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("subjects", "0001_initial"),
        ("actions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="weighing",
            name="subject",
            field=models.ForeignKey(
                help_text="The subject which was weighed",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="weighings",
                to="subjects.Subject",
            ),
        ),
        migrations.AddField(
            model_name="weighing",
            name="user",
            field=models.ForeignKey(
                blank=True,
                help_text="The user who weighed the subject",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="waterrestriction",
            name="adlib_drink",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="actions.WaterType"
            ),
        ),
        migrations.AddField(
            model_name="waterrestriction",
            name="lab",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="misc.Lab"),
        ),
        migrations.AddField(
            model_name="waterrestriction",
            name="location",
            field=models.ForeignKey(
                blank=True,
                help_text="The physical location at which the action was performed",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="misc.LabLocation",
            ),
        ),
        migrations.AddField(
            model_name="waterrestriction",
            name="procedures",
            field=models.ManyToManyField(
                blank=True, help_text="The procedure(s) performed", to="actions.ProcedureType"
            ),
        ),
        migrations.AddField(
            model_name="waterrestriction",
            name="subject",
            field=models.ForeignKey(
                help_text="The subject on which this action was performed",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="actions_waterrestrictions",
                to="subjects.Subject",
            ),
        ),
        migrations.AddField(
            model_name="waterrestriction",
            name="users",
            field=models.ManyToManyField(
                blank=True, help_text="The user(s) involved in this action", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="wateradministration",
            name="session",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="actions.Session"
            ),
        ),
        migrations.AddField(
            model_name="wateradministration",
            name="subject",
            field=models.ForeignKey(
                help_text="The subject to which water was administered",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="water_administrations",
                to="subjects.Subject",
            ),
        ),
        migrations.AddField(
            model_name="wateradministration",
            name="user",
            field=models.ForeignKey(
                blank=True,
                help_text="The user who administered water",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="wateradministration",
            name="water_type",
            field=models.ForeignKey(
                default=action_models._default_water_type,
                on_delete=django.db.models.deletion.SET_DEFAULT,
                to="actions.WaterType",
            ),
        ),
        migrations.AddField(
            model_name="virusinjection",
            name="lab",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="misc.Lab"),
        ),
        migrations.AddField(
            model_name="virusinjection",
            name="location",
            field=models.ForeignKey(
                blank=True,
                help_text="The physical location at which the action was performed",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="misc.LabLocation",
            ),
        ),
        migrations.AddField(
            model_name="virusinjection",
            name="procedures",
            field=models.ManyToManyField(
                blank=True, help_text="The procedure(s) performed", to="actions.ProcedureType"
            ),
        ),
        migrations.AddField(
            model_name="virusinjection",
            name="subject",
            field=models.ForeignKey(
                help_text="The subject on which this action was performed",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="actions_virusinjections",
                to="subjects.Subject",
            ),
        ),
        migrations.AddField(
            model_name="virusinjection",
            name="users",
            field=models.ManyToManyField(
                blank=True, help_text="The user(s) involved in this action", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="taskprotocol",
            name="lab",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="misc.Lab"),
        ),
        migrations.AddField(
            model_name="taskprotocol",
            name="location",
            field=models.ForeignKey(
                blank=True,
                help_text="The physical location at which the action was performed",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="misc.LabLocation",
            ),
        ),
        migrations.AddField(
            model_name="taskprotocol",
            name="procedures",
            field=models.ManyToManyField(
                blank=True, help_text="The procedure(s) performed", to="actions.ProcedureType"
            ),
        ),
        migrations.AddField(
            model_name="taskprotocol",
            name="subject",
            field=models.ForeignKey(
                help_text="The subject on which this action was performed",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="actions_taskprotocols",
                to="subjects.Subject",
            ),
        ),
        migrations.AddField(
            model_name="taskprotocol",
            name="users",
            field=models.ManyToManyField(
                blank=True, help_text="The user(s) involved in this action", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="surgery",
            name="lab",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="misc.Lab"),
        ),
        migrations.AddField(
            model_name="surgery",
            name="location",
            field=models.ForeignKey(
                blank=True,
                default=action_models._default_surgery_location,
                help_text="The physical location at which the surgery was performed",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="misc.LabLocation",
            ),
        ),
        migrations.AddField(
            model_name="surgery",
            name="procedures",
            field=models.ManyToManyField(
                blank=True, help_text="The procedure(s) performed", to="actions.ProcedureType"
            ),
        ),
        migrations.AddField(
            model_name="surgery",
            name="subject",
            field=models.ForeignKey(
                help_text="The subject on which this action was performed",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="actions_surgerys",
                to="subjects.Subject",
            ),
        ),
        migrations.AddField(
            model_name="surgery",
            name="users",
            field=models.ManyToManyField(
                blank=True, help_text="The user(s) involved in this action", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="lab",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="misc.Lab"),
        ),
        migrations.AddField(
            model_name="session",
            name="location",
            field=models.ForeignKey(
                blank=True,
                help_text="The physical location at which the action was performed",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="misc.LabLocation",
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="parent_session",
            field=models.ForeignKey(
                blank=True,
                help_text="Hierarchical parent to this session",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="actions.Session",
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="procedures",
            field=models.ManyToManyField(
                blank=True, help_text="The procedure(s) performed", to="actions.ProcedureType"
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="project",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="subjects.Project"
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="subject",
            field=models.ForeignKey(
                help_text="The subject on which this action was performed",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="actions_sessions",
                to="subjects.Subject",
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="task_protocol",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="actions.TaskProtocol"
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="users",
            field=models.ManyToManyField(
                blank=True, help_text="The user(s) involved in this action", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="otheraction",
            name="lab",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="misc.Lab"),
        ),
        migrations.AddField(
            model_name="otheraction",
            name="location",
            field=models.ForeignKey(
                blank=True,
                help_text="The physical location at which the action was performed",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="misc.LabLocation",
            ),
        ),
        migrations.AddField(
            model_name="otheraction",
            name="procedures",
            field=models.ManyToManyField(
                blank=True, help_text="The procedure(s) performed", to="actions.ProcedureType"
            ),
        ),
        migrations.AddField(
            model_name="otheraction",
            name="subject",
            field=models.ForeignKey(
                help_text="The subject on which this action was performed",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="actions_otheractions",
                to="subjects.Subject",
            ),
        ),
        migrations.AddField(
            model_name="otheraction",
            name="users",
            field=models.ManyToManyField(
                blank=True, help_text="The user(s) involved in this action", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
