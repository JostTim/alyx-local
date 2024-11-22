from django.urls import path
from . import views as experiment_views

urlpatterns = [
    path("insertions", experiment_views.ProbeInsertionList.as_view(), name="probeinsertion-list"),
    path("insertions/<uuid:pk>", experiment_views.ProbeInsertionDetail.as_view(), name="probeinsertion-detail"),
    path("trajectories", experiment_views.TrajectoryEstimateList.as_view(), name="trajectoryestimate-list"),
    path(
        "trajectories/<uuid:pk>", experiment_views.TrajectoryEstimateDetail.as_view(), name="trajectoryestimate-detail"
    ),
    path("channels", experiment_views.ChannelList.as_view(), name="channel-list"),
    path("channels/<uuid:pk>", experiment_views.ChannelDetail.as_view(), name="channel-detail"),
    path("brain-regions", experiment_views.BrainRegionList.as_view(), name="brainregion-list"),
    path("brain-regions/<int:pk>", experiment_views.BrainRegionDetail.as_view(), name="brainregion-detail"),
]
