from django import forms
from django.utils.safestring import mark_safe
from django.contrib.postgres.forms import SimpleArrayField
from django.db.models import Q, Count, Max
from rest_framework import generics
from django_filters.rest_framework import CharFilter
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin
from django.views.generic.base import TemplateView, View
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
import numpy as np

from alyx.base import BaseFilterSet, rest_permission_classes
import django_filters
import structlog
from misc.models import Lab
from jobs.models import Task
from jobs.serializers import TaskListSerializer, TaskDetailsSeriaizer
from actions.models import Session
from pathlib import Path
import os

from pypelines.celery_tasks import create_celery_app

logger = structlog.get_logger(__name__)


class TasksStatusView(ListView):
    template_name = "tasks.html"
    paginate_by = 50

    def get_context_data(self, **kwargs):
        """Return context data for TasksStatusView.

        This method retrieves context data for the TasksStatusView class.
        It includes information about tasks, labs, space availability, and other relevant details.

        Returns:
            dict: A dictionary containing context data for the view.
        """
        graph = self.kwargs.get("graph", None)
        context = super(TasksStatusView, self).get_context_data(**kwargs)
        context["tableFilter"] = self.f
        context["graphs"] = list(Task.objects.all().values_list("graph", flat=True).distinct())
        # annotate the labs for template display
        cw = Count("session__tasks", filter=Q(session__tasks__status=20))
        ls = Max("session__start_time", filter=Q(session__tasks__isnull=False))
        lj = Max("session__tasks__datetime")
        context["labs"] = Lab.objects.annotate(count_waiting=cw, last_session=ls, last_job=lj).order_by("name")
        space = np.array(context["labs"].values_list("json__raid_available", flat=True), dtype=np.float)
        context["space_left"] = np.round(space / 1000, decimals=1)
        context["ibllib_version"] = list(context["labs"].values_list("json__ibllib_version", flat=True))
        if graph:
            # here the empty order_by is to fix a low level SQL bug with distinct when called
            # on value lists and unique together constraints. bof.
            # https://code.djangoproject.com/ticket/16058
            context["task_names"] = list(
                Task.objects.filter(graph=graph)
                .exclude(session__qc=50)
                .order_by("-priority")
                .order_by("level")
                .order_by()
                .values_list("name", flat=True)
                .distinct()
            )
        else:
            context["task_names"] = []
        context["title"] = "Tasks Recap"
        context["site_header"] = "Alyx"
        return context

    def get_queryset(self):
        """Return a filtered queryset based on the provided graph and lab parameters.

        This method retrieves the graph and lab parameters from the view's kwargs.
        It then filters the Session objects based on these parameters.
        If both lab and graph are None, an empty queryset is returned.
        Otherwise, the queryset is filtered based on the lab and graph values.
        The final queryset is passed through a ProjectFilter instance and returned after applying distinct()
        and order_by() operations.

        Returns:
            QuerySet: A filtered and ordered queryset of Session objects.
        """
        graph = self.kwargs.get("graph", None)
        lab = self.kwargs.get("lab", None)
        qs = Session.objects.exclude(qc=50)
        if lab is None and graph is None:
            qs = Session.objects.none()
        else:
            if lab:
                qs = qs.filter(lab__name=lab)
            if graph:
                qs = qs.filter(tasks__graph=self.kwargs["graph"])

        self.f = ProjectFilter(self.request.GET, queryset=qs)

        return self.f.qs.distinct().order_by("-start_time")


class ProjectFilter(django_filters.FilterSet):
    """
    Filter used in combobox of task admin page
    """

    class Meta:
        model = Session
        fields = ["projects"]
        exclude = ["json"]

    def __init__(self, *args, **kwargs):
        super(ProjectFilter, self).__init__(*args, **kwargs)


class TaskFilter(BaseFilterSet):
    lab = CharFilter("session__lab__name")
    status = CharFilter(method="enum_field_filter")

    class Meta:
        model = Task
        exclude = ["json"]


class TaskListView(generics.ListCreateAPIView):
    """
    get: **FILTERS**
    -   **task**: task name `/jobs?task=EphysSyncPulses`
    -   **session**: uuid `/jobs?session=aad23144-0e52-4eac-80c5-c4ee2decb198`
    -   **lab**: lab name from session table `/jobs?lab=churchlandlab`
    -   **pipeline**: pipeline field from task `/jobs?pipeline=ephys`

    [===> task model reference](/admin/doc/models/jobs.task)
    """

    queryset = Task.objects.all()
    # queryset = TaskListSerializer.setup_eager_loading(queryset)
    permission_classes = rest_permission_classes()
    filter_class = TaskFilter

    def get_serializer_class(self):
        if not self.request:
            return TaskListSerializer
        if self.request.method == "GET":
            return TaskListSerializer
        if self.request.method == "POST":
            return TaskDetailsSeriaizer


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    # queryset = TaskDetailsSeriaizer.setup_eager_loading(queryset)
    serializer_class = TaskDetailsSeriaizer
    permission_classes = rest_permission_classes()


def convert_mount(path, reverse=False) -> str:
    import platform

    available_mounts = {
        "//cajal/cajal_data2/ONE": "/mnt/one/cajal2",
        "//Mountcastle/lab/data/ONE": "/mnt/one/mountcastle1",
    }
    if "ubuntu" in platform.version().lower():
        path = path.replace("\\", "/")
        if reverse:
            for original_path, mounted_path in available_mounts.items():
                if mounted_path in path:
                    path = path.replace(mounted_path, original_path)
                    return os.path.normpath(
                        path
                    )  # we found one mount in the root. breaking and skipping the for - else clause
            # None of the mounts were in the root. Maybe data is in an unmounted location ?
            raise IOError("Could not reverse find a mounted location for this path")
        else:
            for original_path, mounted_path in available_mounts.items():
                if original_path in path:
                    path = path.replace(original_path, mounted_path)
                    return os.path.normpath(
                        path
                    )  # we found one mount in the root. breaking and skipping the for - else clause
            # None of the mounts were in the root. Maybe data is in an unmounted location ?
            raise IOError("Could not find a mounted location for this path")
    else:
        return os.path.normpath(path)


class TaskLogs(DetailView):
    template_name = "task_logs.html"
    # model = Task

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        task_id = self.kwargs.get("task_id", None)
        task_object = self.get_object()

        log_file = os.path.join(convert_mount(task_object.session_path), "logs", task_object.log)  # type: ignore
        logger.warning(f"Showing logs from file : {log_file}")
        ansi_logging_content = open(log_file, "r").read()

        context["title"] = f"Logs of task {task_id}"
        context["site_header"] = "Alyx"
        context["task_id"] = task_id
        context["task_change_url"] = reverse("admin:jobs_task_change", args=[task_id])
        context["ansi_logging_content"] = ansi_logging_content
        return context

    def get_object(self):
        return get_object_or_404(Task, pk=self.kwargs["task_id"])


class ArgumentsForm(forms.Form):
    whatever_argument = forms.IntegerField()
    named_argument = forms.CharField()
    boolean_argument = forms.BooleanField()
    array_field = SimpleArrayField(forms.CharField(max_length=100))

    def __init__(self, *args, session_pk, step_name, **kwargs):
        session_pk = str(session_pk)
        self.session_pk = session_pk
        self.step_name = step_name
        super().__init__(*args, **kwargs)

    def save(self):
        logger.warning(f"attempting to save {self=}")


class SessionTasksView(FormMixin, TemplateView):
    template_name = "session_tasks.html"
    form_class = ArgumentsForm

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form.

        Returns:
            dict: A dictionary containing the keyword arguments for instantiating the form,
                including session_pk and step_name.
        """
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {"session_pk": self.kwargs.get("session_pk", None), "step_name": self.kwargs.get("step_name", None)}
        )
        return kwargs

    # def get_object(self):
    #    return get_object_or_404(Session, pk=self.kwargs["session_pk"])

    def post(self, request, *args, **kwargs):
        """Handles POST requests for the view.

        Args:
            request: HttpRequest object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response based on form validation.
        """
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """Save the form data and call the parent class's form_valid method.

        Args:
            form: The form instance to be saved.

        Returns:
            The result of calling the parent class's form_valid method.
        """
        form.save()
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        """Return the success URL based on the session ID and step name.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            str: The success URL.

        Example:
            get_success_url(session_pk=1, step_name='step1')
        """
        session_id = self.kwargs.get("session_pk", None)
        step_name = self.kwargs.get("step_name", None)
        if session_id is not None and step_name is not None:
            return reverse("session-task", kwargs={"session_pk": str(session_id), "step_name": step_name})
        else:
            return reverse("home")

    def get_session_step_url(self, session_id, step_name):
        """Return the URL for a specific session step.

        Args:
            session_id (int): The ID of the session.
            step_name (str): The name of the step.

        Returns:
            str: The URL for the session step.
        """
        return reverse("session-task", kwargs={"session_pk": session_id, "step_name": step_name})

    def get_context_data(self, **kwargs):
        """Get context data for processing task view.

        Returns:
            dict: A dictionary containing context data for the processing task view.
        """

        context = super().get_context_data(**kwargs)
        session_id = str(self.kwargs.get("session_pk", None))
        session_object = Session.objects.get(pk=session_id)

        # celery_app = get_celery_app("pypelines", refresh=False)
        celery_app = create_celery_app(__file__, "pypelines")
        tasks_data = celery_app.get_celery_app_tasks("pypelines")

        available_pipelines = list(set([task_name.split(".")[0] for task_name in tasks_data.keys()]))

        default_project = session_object.projects.first()
        if default_project is None:
            default_pipeline = available_pipelines[0]
        else:
            project_name = str(default_project.name).lower()
            if project_name not in available_pipelines:
                default_pipeline = available_pipelines[0]
            else:
                default_pipeline = project_name

        selected_pipeline = self.kwargs.get("pipeline", default_pipeline)

        # reorder the pipelines so that the selected one is on top
        available_pipelines.pop(available_pipelines.index(selected_pipeline))
        available_pipelines = [
            selected_pipeline,
        ] + available_pipelines

        formated_data = self.format_app_tasks_data(tasks_data, selected_pipeline)

        step_name = self.kwargs.get("step_name", None)
        for i, pipe in enumerate(formated_data):
            for j, step in enumerate(pipe["steps"]):
                if step["is_empty"]:
                    continue
                if step["complete_name"] == step_name:
                    formated_data[i]["steps"][j]["is_selected"] = True
                formated_data[i]["steps"][j]["url"] = self.get_session_step_url(session_id, step["complete_name"])

        context["site_header"] = "Alyx"

        session_change_url = reverse("admin:actions_session_change", args=[session_id])

        title = f'Processing task view for session <a href="{session_change_url}">{session_object}</a>'
        if step_name is not None:
            this_url = self.get_session_step_url(session_id, step_name)
            title += f' - With task step <a href="{this_url}">{step_name}</a>'

        available_pipelines_dict = {}
        for pipeline_name in available_pipelines:

            if step_name is not None:
                value = reverse(
                    "session-task-with-pipeline",
                    kwargs={"session_pk": session_id, "step_name": step_name, "pipeline": pipeline_name},
                )
            else:
                value = reverse(
                    "session-tasks-with-pipeline", kwargs={"session_pk": session_id, "pipeline": pipeline_name}
                )

            available_pipelines_dict[pipeline_name] = value

        context["title"] = mark_safe(title)
        context["run_url"] = (
            reverse("create-session-task", kwargs={"session_pk": session_id, "step_name": step_name})
            if step_name is not None
            else ""
        )
        context["pipe_list"] = formated_data
        context["origin_url"] = self.get_session_step_url(session_id, step_name)
        context["selected_task_name"] = step_name
        context["form"] = self.get_form().as_div()
        context["available_pipelines"] = available_pipelines_dict
        return context

    def format_app_tasks_data(self, app_task_data, selected_pipeline):
        """_summary_

        Args:
            app_task_data (_type_): _description_
            selected_pipeline (_type_): _description_

        Returns:
            list: see below for an example :

            ```python
            formated_data = [
                {
                    "name": "neuropil_mask",
                    "steps": [
                        {
                            "name": "initial_calculation",
                            "complete_name": "neuropil_mask.initial_calculation",
                            "is_empty": False,
                            "is_selected": False,
                            "url": self.get_session_step_url(session_id, "neuropil_mask.initial_calculation"),
                            "requirement_stack": [],
                        },
                        {
                            "is_empty": True,
                        },
                        {
                            "name": "secondstep",
                            "complete_name": "neuropil_mask.secondstep",
                            "is_empty": False,
                            "is_selected": False,
                            "url": self.get_session_step_url(session_id, "neuropil_mask.secondstep"),
                            "requirement_stack": ["neuropil_mask.initial_calculation", "trials_df.initial_calculation"],
                        },
                    ],
                },
                {
                    "name": "trials_df",
                    "steps": [
                        {
                            "name": "initial_calculation",
                            "complete_name": "trials_df.initial_calculation",
                            "is_empty": False,
                            "is_selected": False,
                            "url": self.get_session_step_url(session_id, "trials_df.initial_calculation"),
                            "requirement_stack": [],
                        },
                        {
                            "name": "secondstep",
                            "complete_name": "trials_df.secondstep",
                            "is_empty": False,
                            "is_selected": False,
                            "url": self.get_session_step_url(session_id, "trials_df.secondstep"),
                            "requirement_stack": ["trials_df.initial_calculation"],
                        },
                    ],
                },
            ]
            ```
        """
        formated_data = {}
        max_level = 0

        # first organize steps bu pipe groups, and format the required data
        for task_name, task_data in app_task_data.items():
            pipeline = task_name.split(".")[0]
            if pipeline != selected_pipeline:
                continue
            pipe_name = task_data["pipe_name"]
            step_data = {
                "name": task_data["step_name"],
                "complete_name": task_name,
                "is_empty": False,
                "is_selected": False,
                "url": "temp//temp",  # self.get_session_step_url(session_id, "neuropil_mask.initial_calculation"),
                "requirement_stack": [
                    item if pipeline in item else f"{pipeline}.{item}" for item in task_data["requires"]
                ],
                "level": task_data["step_level_in_pipe"],
            }
            max_level = max_level if max_level > task_data["step_level_in_pipe"] else task_data["step_level_in_pipe"]
            pipe_data = formated_data.get(pipe_name, {"name": pipe_name, "steps": []})

            pipe_data["steps"].append(step_data)

            formated_data[pipe_name] = pipe_data

        formated_data = list(formated_data.values())

        # then fill the empty steps with is_empty: True placeholders to facilitate the later assortment
        # of steps by html and javascript in a visually readable way with empty divs
        for pipe in formated_data:
            pipe_levels = [step["level"] for step in pipe["steps"]]
            new_steps_data = []
            for step_level in range(max_level + 1):
                try:
                    level_index = pipe_levels.index(step_level)
                    new_steps_data.append(pipe["steps"][level_index])
                except ValueError:  # level not in list
                    new_steps_data.append({"is_empty": True, "level": step_level})
            pipe.update({"steps": new_steps_data})

        return formated_data


class CreateAndViewTask(View):

    def get(self, request, *args, **kwargs):
        step_name = self.kwargs.get("step_name")
        session_id = str(self.kwargs.get("session_pk"))
        session_object = Session.objects.get(pk=session_id)

        new_obj = Task.objects.create(name=step_name, session=session_object)
        new_task_pk = new_obj.pk
        # new_task_pk = f"run the pipeline mechanism here and get the new task using {step_name}"

        return redirect("task-logs", task_id=new_task_pk)


# class TasksOverview(View):
#     pass

# APP_STORAGE = {}


# def get_celery_app(app_name="pypelines", refresh=False):

#     if app_name in APP_STORAGE.keys() and not refresh:

#         return APP_STORAGE[app_name]

#     from celery import Celery
#     from types import MethodType

#     from configparser import ConfigParser

#     config = ConfigParser()

#     config_file_path = Path(__file__).parent / ".celery_secrets.ini"

#     config.read(config_file_path)
#     username = config.get("connexion", "username")
#     password = config.get("connexion", "password")
#     address = config.get("connexion", "address")
#     port = config.get("connexion", "port")
#     broker_type = config.get("connexion", "broker_type")

#     app = Celery(app_name, broker=f"{broker_type}://{username}:{password}@{address}:{port}//", backend="rpc://")
#     app.conf.accept_content = ["pickle", "json", "msgpack", "yaml"]
#     app.conf.worker_send_task_events = True
#     app.conf.timezone = "Europe/Paris"

#     @app.task(name=f"{app_name}.tasks_infos")
#     def tasks_infos(task_name) -> dict:
#         return {}

#     @app.task(name=f"{app_name}.handshake")
#     def handshake() -> str:
#         return ""

#     def get_remote_tasks(self):
#         registered_tasks = app.control.inspect().registered_tasks()
#         if registered_tasks is None:
#             logger.warning("Cannot get names of remotely registered tasks")
#             return {"task_names": [], "workers": []}
#         workers = []
#         task_names = []
#         for worker, tasks in registered_tasks.items():
#             workers.append(worker)
#             for task in tasks:
#                 task_names.append(task)

#         return {"task_names": task_names, "workers": workers}

#     app.get_remote_tasks = MethodType(get_remote_tasks, app)  # type: ignore

#     APP_STORAGE[app_name] = app

#     return app


# def get_celery_app_tasks(app, refresh=False):

#     app_task_data = getattr(app, "task_data", None)

#     if app_task_data is None or refresh:
#         try:
#             app_task_data = app.tasks[f"{app.main}.tasks_infos"].delay(app.main).get(timeout=2)
#             setattr(app, "task_data", app_task_data)
#         except Exception as e:
#             logger.warning(f"Could not get tasks from app. {e}")
#             logger.warning(f"Remote tasks are : {app.get_remote_tasks()}")
#             logger.warning(f"Local tasks are : {app.tasks}")
#             return {}

#     return app_task_data


# # In your Django view

# from django.http import HttpResponse
# from PIL import Image
# import io

# def display_image(request):
#     # Assuming `image_data` is a variable containing image bytes
#     # For example, let's create an image with PIL and convert it to bytes
#     image = Image.new('RGB', (100, 100), color = 'blue')
#     buffer = io.BytesIO()
#     image.save(buffer, format='JPEG')
#     image_data = buffer.getvalue()

#     # Create an HttpResponse with the image data and the correct MIME type
#     return HttpResponse(image_data, content_type="image/jpeg")

# # In your urls.py, map the view to a URL
# from django.urls import path
# from .views import display_image

# urlpatterns = [
#     path('display_image/', display_image, name='display_image'),
# ]
