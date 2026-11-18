from django.urls import path

from .api import api
from .session import session_api

urlpatterns = [
    path("api/v1/session", session_api),
    path("api/v1/", api.urls),
]
