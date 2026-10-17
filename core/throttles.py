from rest_framework.permissions import SAFE_METHODS
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle

from .permissions import is_owner


class AnonReadThrottle(AnonRateThrottle):
    scope = "anon_read"
    def allow_request(self, request, view):
        if request.method not in SAFE_METHODS:
            return True
        return super().allow_request(request, view)


class AnonWriteThrottle(AnonRateThrottle):
    scope = "anon_write"
    def allow_request(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)


class IPScopedThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        if is_owner(request.user):
            return None
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class CommentThrottle(IPScopedThrottle):
    scope = "comment"

class ContactThrottle(IPScopedThrottle):
    scope = "contact"

class LikeThrottle(IPScopedThrottle):
    scope = "like"

class LoginThrottle(IPScopedThrottle):
    scope = "login"