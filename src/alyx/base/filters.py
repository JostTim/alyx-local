# filters.py
import django_filters
from .base import Session

class SessionFilter(django_filters.FilterSet):
    class Meta:
        model = Session
        fields = '__all__'  # Enable filtering on all fields

# views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from .models import Session
from .serializers import SessionSerializer
from .filters import SessionFilter

class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = SessionFilter

# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SessionViewSet

router = DefaultRouter()
router.register(r'sessions', SessionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
