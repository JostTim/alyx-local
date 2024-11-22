from django.urls import path
from . import views as job_views

urlpatterns = [
    path("tasks", job_views.TaskListView.as_view(), name="tasks-list"),
    path("tasks/<uuid:pk>", job_views.TaskDetailView.as_view(), name="tasks-detail"),
    path(
        "admin-tasks/task-logs/<uuid:task_id>",
        job_views.TaskLogs.as_view(),
        name="task-logs",
    ),
    path(
        "admin-tasks/create-task/<uuid:session_pk>/task/<str:step_name>",
        job_views.CreateAndViewTask.as_view(),
        name="create-session-task",
    ),
    path(
        "admin-tasks/session/<uuid:session_pk>/task/<str:step_name>",
        job_views.SessionTasksView.as_view(),
        name="session-task",
    ),
    path(
        "admin-tasks/session/<uuid:session_pk>/<str:pipeline>/task/<str:step_name>",
        job_views.SessionTasksView.as_view(),
        name="session-task-with-pipeline",
    ),
    path(
        "admin-tasks/session/<uuid:session_pk>/<str:pipeline>/",
        job_views.SessionTasksView.as_view(),
        name="session-tasks-with-pipeline",
    ),
    path(
        "admin-tasks/session/<uuid:session_pk>",
        job_views.SessionTasksView.as_view(),
        name="session-tasks",
    ),
    # path(
    #     "admin-tasks",
    #     job_views.TasksOverview.as_view(),
    #     name="session-tasks-overview",
    # ),
    path(
        "admin-tasks/status",
        job_views.TasksStatusView.as_view(),
        name="tasks_status",
    ),
    path(
        "admin-tasks/status/<str:graph>",
        job_views.TasksStatusView.as_view(),
        name="tasks_status_graph",
    ),
    path(
        "admin-tasks/status/<str:graph>/<str:lab>",
        job_views.TasksStatusView.as_view(),
        name="tasks_status_graph_lab",
    ),
]
