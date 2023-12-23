from django.urls import path
from jobs import views as jv

urlpatterns = [
    path("tasks", jv.TaskListView.as_view(), name="tasks-list"),
    path("tasks/<uuid:pk>", jv.TaskDetailView.as_view(), name="tasks-detail"),
    path(
        "admin-tasks/task-logs/<uuid:task_id>",
        jv.TaskLogs.as_view(),
        name="task-logs",
    ),
    path(
        "admin-tasks/session/<uuid:session_pk>/task/<str:step_name>",
        jv.SessionTasksView.as_view(),
        name="session-tasks",
    ),
    path(
        "admin-tasks/status",
        jv.TasksStatusView.as_view(),
        name="tasks_status",
    ),
    path(
        "admin-tasks/status/<str:graph>",
        jv.TasksStatusView.as_view(),
        name="tasks_status_graph",
    ),
    path(
        "admin-tasks/status/<str:graph>/<str:lab>",
        jv.TasksStatusView.as_view(),
        name="tasks_status_graph_lab",
    ),
]
