"""בדיקות על אתר אמיתי ב-Netlify (Deploy Preview או האתר החי). קריאה בלבד – לא משנות שום דבר.

Run:  BASE_URL=https://deploy-preview-12--ngqa-ctfl40.netlify.app pytest tests/preview
"""
import json
import os
import urllib.error
import urllib.request

import pytest

BASE = os.environ.get("BASE_URL", "").rstrip("/")
COURSES = ["ctfl", "genai", "sql"]

pytestmark = pytest.mark.skipif(not BASE, reason="BASE_URL not set – live checks run only against a real Netlify deploy")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def get(path, cookie=None, headers=None):
    req = urllib.request.Request(BASE + path, headers={**(headers or {}), **({"Cookie": cookie} if cookie else {})})
    try:
        r = _opener.open(req, timeout=20)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


@pytest.mark.parametrize("cid", COURSES)
def test_anonymous_course_redirects_to_login(cid):
    for p in (f"/courses/{cid}/", f"/courses/{cid}/decks.json", f"/courses/{cid}/index.html"):
        st, h, _ = get(p)
        assert st == 302, f"{p} -> {st} (course files must be locked)"
        assert h.get("Location", h.get("location", "")).endswith(f"/?login=1&next=/courses/{cid}/")


def test_function_sources_not_served():
    st, _, _ = get("/netlify/functions/admin.js")
    assert st == 404


def test_security_headers():
    st, h, _ = get("/")
    h = {k.lower(): v for k, v in h.items()}
    assert st == 200
    assert h.get("x-content-type-options") == "nosniff"
    assert h.get("x-frame-options") == "SAMEORIGIN"


def test_identity_is_invite_only():
    st, _, body = get("/.netlify/identity/settings")
    assert st == 200, "Netlify Identity must be enabled"
    assert json.loads(body).get("disable_signup") is True, "open sign-up would let anyone register"


def test_admin_function_requires_login():
    st, _, _ = get("/.netlify/functions/admin")
    assert st == 401
