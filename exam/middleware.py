"""
exam/middleware.py
─────────────────────────────────────────────────────────────────
Security & rate-limiting middleware for BBDNIIT Exam Platform.
"""
import time
import hashlib
from collections import defaultdict
from threading import Lock

from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


# ── Simple in-process rate limiter (works for single-process deployments) ──
# For multi-worker production, swap _store for Redis-backed counter.

_store = defaultdict(list)   # ip -> [timestamp, ...]
_lock = Lock()

RATE_LIMIT_RULES = {
    '/student/calculate-marks': (5,  60),   # 5 submits / 60s
    '/student/log-proctoring-alert': (60, 60),  # 60 alerts / 60s
    '/student/studentsignup': (5, 300),     # 5 signups / 5 min
    '/teacher/teachersignup': (5, 300),
    '/adminlogin':  (10, 60),
    '/studentlogin': (10, 60),
    '/teacherlogin': (10, 60),
}


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


class RateLimitMiddleware(MiddlewareMixin):
    """
    Per-IP rate limiting for sensitive endpoints.
    Returns 429 if the limit is exceeded.
    """
    def process_request(self, request):
        path = request.path_info
        rule = RATE_LIMIT_RULES.get(path)
        if not rule:
            return None

        max_calls, window = rule
        ip = _get_client_ip(request)
        key = hashlib.md5(f"{ip}:{path}".encode()).hexdigest()
        now = time.time()

        with _lock:
            hits = [t for t in _store[key] if now - t < window]
            if len(hits) >= max_calls:
                return HttpResponse(
                    "Too many requests. Please slow down.",
                    status=429,
                    content_type='text/plain',
                )
            hits.append(now)
            _store[key] = hits
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adds security headers to every response.
    """
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Only enforce HTTPS in production
        from django.conf import settings
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response


class ExamSessionExpiryMiddleware(MiddlewareMixin):
    """
    Marks expired ExamSessions lazily when a student makes any request.
    Prevents stale 'active' sessions from blocking new attempts.
    """
    def process_request(self, request):
        if hasattr(request, 'user') and not request.user.is_authenticated:
            return None
        if not request.path.startswith('/student/'):
            return None
        # Run expiry cleanup at most once per user per 60 seconds
        # using a session variable to avoid a DB hit on every request
        last_check = request.session.get('_session_expiry_check', 0)
        if time.time() - last_check < 60:
            return None
        try:
            from exam.models import ExamSession
            from django.utils import timezone
            ExamSession.objects.filter(
                student__user=request.user,
                status=ExamSession.STATUS_ACTIVE,
                expires_at__lt=timezone.now(),
            ).update(status=ExamSession.STATUS_EXPIRED)
            request.session['_session_expiry_check'] = time.time()
        except Exception:
            pass
        return None
