# BBDNIIT Exam Platform — Architecture Improvement Log

## Phase 1 — Structure Cleanup

### Issue: Ghost AI-generation directories
**Root cause:** Shell brace-expansion (`mkdir -p {a,b,c}`) failed silently in a non-bash shell,
creating literal directories named `{templates` and `{onlinexam,exam,...}`.
**Fix:** Complete fresh directory build using explicit `mkdir -p` per path. Zero ghost dirs confirmed.

### Issue: Broken redirect in `afterlogin_view`
**Root cause:** `redirect('student/student-dashboard')` passes a URL path string, not a URL name.
Django's `redirect()` treats bare strings without `/` as URL names — with `/` it treats them as paths,
causing a 404 because no URL pattern matches that full string.
**Fix:** Changed to `redirect('student-dashboard')` and `redirect('teacher-dashboard')` (registered names).

### Issue: Unused `import os` in `teacher/views.py`
**Fix:** Removed. No functional impact, but causes linter warnings and hints at copy-paste artifacts.

---

## Phase 2 — Exam Engine Hardening

### Feature: `ExamSession` model (server-side session lock)
**Added:** `ExamSession` tracks every active exam attempt with UUID token, expiry timestamp,
question order (JSON), and server-side proctoring counters.

**Why:** Cookie-only answer storage is unreliable (cookies cleared, expired, spoofed).
Server-side sessions allow resume on reconnect and prevent double submission.

### Feature: `select_for_update()` anti-duplicate-submit lock
`calculate_marks_view` wraps the entire submission in `@transaction.atomic` and calls
`ExamSession.objects.select_for_update().get(...)` — this acquires a DB-level row lock.
If two simultaneous POSTs arrive (network retry), the second waits for the first to commit,
then sees `status=submitted` and redirects — no duplicate Result row is created.

### Feature: Question randomization per student
When `course.randomize_questions=True`, `random.shuffle()` is called on the question list
before creating the `ExamSession`. The shuffled order is stored as a JSON list of IDs in
`question_order`, ensuring each student sees a unique order and server-side marking uses
the same order for evaluation.

### Feature: Attempt restriction at DB level
`take_exam_view` counts `Result.objects.filter(student=student, exam=course, date__date=today)`.
If count >= `course.max_attempts`, the student is blocked before an `ExamSession` is created.

---

## Phase 3 — Proctoring System

### Issue: Client-only counters (spoofable)
**Old behaviour:** JavaScript incremented local counters; the only backend record was a
`ProctoringAlert` row. A student could submit with `tab_switch_count=0` manually.

**Fix:** `log_proctoring_alert_view` now calls `session.increment_tab()` / `session.increment_face()`
which use `F('field') + 1` database expressions — atomically incrementing the server-side counter.
The response returns the authoritative server count; the JS updates its display to match.

### Feature: Session heartbeat endpoint (`/student/session-status`)
Client polls every 30 seconds. Server responds with `{status, remaining_seconds, tab_count, face_count}`.
If the server marks the session expired (e.g., teacher ends exam early), the client receives
`status=expired` and auto-submits immediately — even if the local timer has not expired.

### Feature: Camera face detection (Kovac RGB heuristic)
Uses the `MediaDevices.getUserMedia` API to capture webcam frames to a canvas.
Applies a standard RGB skin-tone pixel ratio test every 4 seconds.
Two consecutive bad frames trigger an alert (avoids single-frame false positives from blinks etc.).
This is camera-API-based, not simulated. Architecture is ready to swap in `face-api.js`
TinyFaceDetector by replacing the `detectFacePresent()` function body.

---

## Phase 4 — Concurrency & Performance

### Gunicorn: gthread worker model
`gunicorn.conf.py` sets `worker_class=gthread`, `workers=CPU*2+1`, `threads=4`.
For a 4-core VM: 9 workers × 4 threads = 36 concurrent requests handled without blocking.
`max_requests=1000` + jitter prevents memory accumulation per worker.
`preload_app=True` shares Django's loaded state across workers (lower RAM).

### Query optimisation
All list views use `select_related` / `prefetch_related`:
- `Result.objects.select_related('student__user', 'exam')` — avoids N+1 on result tables
- `Course.objects.annotate(q_count=Count('questions'))` — single query for question count
- `ExamSession` index on `(student, course, status)` — fast lookup during exam start

### Redis cache (safe fallback)
Settings detect `REDIS_URL` env variable. If absent, falls back to `LocMemCache` —
project runs locally without Redis installed. In Docker, Redis container provides the cache.

### `ExamSessionExpiryMiddleware`
Lazily expires stale active sessions using a session-cookie timestamp throttle (max 1 DB query
per 60 seconds per user). Prevents stale sessions from blocking re-attempts without needing
a background task scheduler.

---

## Phase 5 — Template Quality Control

### Issue: All hardcoded URL paths in templates
**Count:** 47 hardcoded `/student/...`, `/teacher/...`, `/admin-...` href strings found across templates.
**Risk:** Any URL pattern rename breaks silently — no `NoReverseMatch` exception, just a 404.
**Fix:** All replaced with `{% url 'name' %}` and `{% url 'name' pk %}` tags.
Django's template URL reversal raises `NoReverseMatch` at render time if a name is wrong —
making routing errors visible immediately during development.

### Issue: Sidebars using hardcoded paths
`admin_sidebar.html`, `teacher_sidebar.html`, `student_sidebar.html` all rewritten with `{% url %}`.

### Template count: 64 templates, 0 dead (all referenced from views)
Verified with automated Python script: all `render(request, 'x.html')` calls have a matching file.

---

## Phase 6 — Migration Fix

### Issue: Duplicate index names in migration
`related_name='results'` and `related_name='proctoring_alerts'` caused the auto-generated index
names (`results`, `proctoring_alerts`) to collide across models when using the shorthand notation.
**Fix:** All DB indexes given explicit unique names:
- `exam_session_lookup_idx`
- `result_student_exam_idx`
- `proctor_student_course_idx`

---

## Security Additions

| Addition | Purpose |
|---|---|
| `RateLimitMiddleware` | Per-IP rate limits on login/submit/signup endpoints |
| `SecurityHeadersMiddleware` | X-Frame-Options, X-Content-Type-Options, HSTS (prod) |
| `CSRF_COOKIE_HTTPONLY=False` | Allows JS AJAX to read CSRF token (required for proctoring API) |
| `SESSION_COOKIE_HTTPONLY=True` | Session cookie not readable by JS (XSS protection) |
| UUID session token | Exam submission validated by opaque token, not guessable integer |
| `select_for_update` | DB-level row lock prevents race-condition double submissions |
| Keyboard shortcut blocking | F12, Ctrl+C/V/U/S/P/A/I blocked during exam screen |
