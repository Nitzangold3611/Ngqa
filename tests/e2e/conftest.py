"""Fixtures for the course-site browser tests (local Netlify + Identity stand-in).

Each test module gets a fresh server; each test gets fresh users.
Any JavaScript error on a page fails the test.
"""
import json
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright, Page, expect

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "tests" / ".artifacts" / "screens"
PW = "Password123"
OWNER = "owner@test.local"

expect.set_options(timeout=6000)


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def base_url():
    port = _free_port()
    proc = subprocess.Popen(["node", str(ROOT / "tests/support/server.mjs"), str(port)], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env={"ADMIN_EMAILS": OWNER, "PATH": __import__("os").environ["PATH"]})
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    else:
        proc.kill()
        raise RuntimeError("test server did not start")
    yield f"http://127.0.0.1:{port}"
    proc.terminate()
    proc.wait(timeout=5)


def _post(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"content-type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req).read() or b"{}")


@pytest.fixture
def users(base_url):
    """Fresh users for each test: owner(admin), one student per course, a multi-course student, a blocked one."""
    _post(base_url + "/.netlify/identity/__test/reset", {})
    _post(base_url + "/.netlify/identity/__test/users", {"users": [
        {"email": OWNER, "password": PW, "name": "ניצן"},
        {"email": "ctfl@test.local", "password": PW, "roles": ["ctfl"], "name": "תלמיד CTFL"},
        {"email": "sql@test.local", "password": PW, "roles": ["sql"], "name": "תלמידת SQL"},
        {"email": "all@test.local", "password": PW, "roles": ["ctfl", "genai", "sql"], "name": "כל הקורסים"},
        {"email": "none@test.local", "password": PW, "roles": [], "name": "בלי קורסים"},
        {"email": "blocked@test.local", "password": PW, "roles": ["ctfl"], "blocked": True, "name": "חסום"},
    ]})
    return base_url


def mail(base_url):
    return json.loads(urllib.request.urlopen(base_url + "/.netlify/identity/__test/mail").read())["mail"]


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _page(browser, request, **kw) -> Page:
    ctx = browser.new_context(locale="he-IL", **kw)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("dialog", lambda d: d.accept())  # the admin page uses confirm() for destructive actions
    request.node._errors = errors
    request.addfinalizer(ctx.close)
    return page


@pytest.fixture
def page(browser, request):
    p = _page(browser, request, viewport={"width": 1366, "height": 860})
    yield p
    assert not request.node._errors, f"JavaScript errors: {request.node._errors}"


@pytest.fixture
def mobile(browser, request):
    p = _page(browser, request, viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
    yield p
    assert not request.node._errors, f"JavaScript errors: {request.node._errors}"


def login(page: Page, base_url: str, email: str, password: str = PW, start="/"):
    page.goto(base_url + start)
    if not page.locator("#fLogin").is_visible():
        page.click("#liB")
    page.fill("#fLogin [name=email]", email)
    page.fill("#fLogin [name=password]", password)
    page.click("#fLogin .pbtn")


def shot(page: Page, name: str, full_page=False):
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / f"{name}.png"), full_page=full_page)


def card(page: Page, cid: str):
    return page.locator(f".course[data-c='{cid}']")
