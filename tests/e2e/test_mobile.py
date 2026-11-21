"""טלפון: בלי גלילה לרוחב, ניווט בשקפים עובד."""
import pytest
from playwright.sync_api import expect
from conftest import login, shot, card


@pytest.mark.parametrize("path", ["/", "/courses/ctfl/", "/courses/genai/", "/courses/sql/", "/courses/ctfl/#ch1/1"])
def test_no_horizontal_scroll(mobile, users, path):
    login(mobile, users, "all@test.local")
    expect(mobile.locator("#umB")).to_be_visible()
    mobile.goto(users + path)
    mobile.wait_for_load_state("networkidle")
    sw, cw = mobile.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
    assert sw <= cw + 1, f"{path}: page scrolls sideways ({sw} > {cw})"
    if path in ("/", "/courses/sql/"):
        shot(mobile, "mobile" + path.replace("/", "-").rstrip("-"))


def test_mobile_login_dialog_fits_screen(mobile, users):
    mobile.goto(users + "/")
    mobile.click("#liB")
    box = mobile.locator("#dlg").bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= 390
