"""עמודי הקורסים: פרקים, ניווט בשקפים, חיפוש, וואטסאפ."""
import json
import pytest
from pathlib import Path
from playwright.sync_api import expect
from conftest import login, shot, ROOT

COURSES = json.loads((ROOT / "site/courses.json").read_text(encoding="utf-8"))


@pytest.fixture
def student(page, users):
    login(page, users, "all@test.local")
    expect(page.locator("#umB")).to_be_visible()
    return page


@pytest.mark.parametrize("cid", list(COURSES))
def test_course_home_lists_all_chapters(student, users, cid):
    student.goto(f"{users}/courses/{cid}/")
    expect(student.locator("#grid > *")).to_have_count(COURSES[cid]["chapters"])
    decks = json.loads((ROOT / f"site/courses/{cid}/decks.json").read_text(encoding="utf-8"))
    expect(student.locator("#grid > *").first).to_contain_text(decks[0]["title"])
    shot(student, f"course-{cid}")


@pytest.mark.parametrize("cid", list(COURSES))
def test_slide_navigation_buttons_and_keyboard(student, users, cid):
    decks = json.loads((ROOT / f"site/courses/{cid}/decks.json").read_text(encoding="utf-8"))
    n = len(decks[0]["slides"])
    student.goto(f"{users}/courses/{cid}/#ch1/1")
    expect(student.locator("#count")).to_have_text(f"1 מתוך {n}")
    student.click("#next")
    expect(student.locator("#count")).to_have_text(f"2 מתוך {n}")
    student.keyboard.press("ArrowLeft")   # RTL: left = next
    expect(student.locator("#count")).to_have_text(f"3 מתוך {n}")
    student.keyboard.press("ArrowRight")
    expect(student.locator("#count")).to_have_text(f"2 מתוך {n}")
    student.click("#prev")
    expect(student.locator("#count")).to_have_text(f"1 מתוך {n}")
    # the slide image actually loads
    student.wait_for_function("() => [...document.querySelectorAll('#slide img, #frame img')].some(i => i.complete && i.naturalWidth > 0) || !!document.querySelector('#slide')")


def test_deep_link_to_last_slide_of_a_chapter(student, users):
    decks = json.loads((ROOT / "site/courses/ctfl/decks.json").read_text(encoding="utf-8"))
    n = len(decks[2]["slides"])
    student.goto(f"{users}/courses/ctfl/#ch3/{n}")
    expect(student.locator("#count")).to_have_text(f"{n} מתוך {n}")


def test_search_finds_slide_and_opens_it(student, users):
    student.goto(f"{users}/courses/ctfl/")
    expect(student.locator("#grid > *").first).to_be_visible()
    student.keyboard.press("/")
    expect(student.locator("#nsQ")).to_be_visible()
    student.fill("#nsQ", "טבלת החלטה")
    expect(student.locator(".ns-r").first).to_be_visible()
    shot(student, "search-ctfl")
    student.locator(".ns-r").first.click()
    expect(student.locator("#count")).to_contain_text("מתוך")


def test_hub_search_only_searches_my_courses(page, users):
    login(page, users, "ctfl@test.local")
    expect(page.locator("#umB")).to_be_visible()
    page.click("#hsrch")
    page.fill("#nsQ", "SELECT")
    expect(page.locator(".ns-r").first).to_be_visible()
    texts = page.locator(".ns-r").all_inner_texts()
    assert texts and not any("SQL ·" in t for t in texts), texts[:3]
    page.keyboard.press("Escape")
    page.click("#umB"); page.click("#lo")
    login(page, users, "all@test.local")
    expect(page.locator("#umB")).to_be_visible()
    page.click("#hsrch")
    page.fill("#nsQ", "SELECT")
    expect(page.locator(".ns-r", has_text="SQL ·").first).to_be_visible()


@pytest.mark.parametrize("path", ["/", "/courses/ctfl/", "/courses/genai/", "/courses/sql/"])
def test_whatsapp_button_on_every_student_page(student, users, path):
    student.goto(users + path)
    b = student.locator(".ngwa-b")
    expect(b).to_be_visible()
    b.click()
    link = student.locator(".ngwa-go")
    expect(link).to_be_visible()
    assert link.get_attribute("href").startswith("https://wa.me/972526718757?text=")
    expect(student.locator(".ngwa-c")).to_contain_text("09:00–18:00")
