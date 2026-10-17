from django.db.models import ProtectedError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        return Response(
            {"detail": "This item is still used by existing posts and cannot be deleted."},
            status=400,
        )
    return exception_handler(exc, context)