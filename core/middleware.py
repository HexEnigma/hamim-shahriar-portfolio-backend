import logging
import time

logger = logging.getLogger("request")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        ms = (time.perf_counter() - start) * 1000
        response["X-Response-Time"] = f"{ms:.0f}ms"
        logger.info("%s %s → %s (%.0f ms)", request.method, request.path, response.status_code, ms)
        return response