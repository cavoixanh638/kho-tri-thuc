import json

from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import RequestDataTooBig
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods


def session_response(request):
    authenticated = request.user.is_authenticated
    return JsonResponse(
        {
            "authenticated": authenticated,
            "username": request.user.get_username() if authenticated else None,
            "csrf_token": get_token(request),
        }
    )


@never_cache
@require_http_methods(["GET", "POST", "DELETE"])
def session_api(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
        except (ValueError, RequestDataTooBig):
            return JsonResponse({"code": "invalid_request"}, status=400)
        if not isinstance(payload, dict):
            return JsonResponse({"code": "invalid_request"}, status=400)
        username, password = payload.get("username"), payload.get("password")
        if not (
            isinstance(username, str)
            and isinstance(password, str)
            and 0 < len(username) <= 150
            and 0 < len(password) <= 4096
        ):
            return JsonResponse({"code": "invalid_credentials"}, status=401)
        user = authenticate(request, username=username, password=password)
        if user is None:
            return JsonResponse({"code": "invalid_credentials"}, status=401)
        login(request, user)
    elif request.method == "DELETE":
        logout(request)
    return session_response(request)
