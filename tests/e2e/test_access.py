"""התחברות והרשאות: מי רואה איזה קורס, ונעילה גם בגישה ישירה לכתובת."""
from playwright.sync_api import expect
from conftest import login, shot, card, PW


def test_anonymous_home_all_courses_locked(page, users):
    page.goto(users + "/")
    for cid in ["ctfl", "genai", "sql"]:
        expect(card(page, cid)).to_have_class("course locked")
        expect(card(page, cid).locator(".go")).to_have_text("התחברות לקורס 🔒")
    # counts on the cards come from courses.json
    expect(card(page, "ctfl").locator(".chip").first).to_have_text("6 פרקים")
    expect(card(page, "sql").locator(".chip").nth(2)).to_contain_text("שאלות תרגול")
    shot(page, "home-anonymous")


def test_wrong_password_hebrew_error(page, users):
    login(page, users, "ctfl@test.local", "wrong-password")
    expect(page.locator("#fLogin .err")).to_have_text("המייל או הסיסמה שגויים.")


def test_password_eye_in_login(page, users):
    page.goto(users + "/")
    page.click("#liB")
    page.fill("#fLogin [name=password]", "Secret123")
    page.click("#fLogin .eye")
    expect(page.locator("#fLogin [name=password]")).to_have_attribute("type", "text")


def test_student_sees_only_own_course(page, users):
    login(page, users, "ctfl@test.local")
    expect(card(page, "ctfl")).not_to_have_class("course locked")
    expect(card(page, "genai").locator(".go")).to_have_text("אין לך גישה לקורס")
    expect(card(page, "sql")).to_have_class("course locked")
    card(page, "genai").click()
    expect(page.locator("#notice")).to_contain_text("אין לך גישה לקורס")
    expect(page).to_have_url(users + "/")
    shot(page, "home-student-ctfl")


def test_direct_url_to_other_course_is_blocked(page, users):
    login(page, users, "ctfl@test.local")
    expect(card(page, "ctfl")).not_to_have_class("course locked")
    page.goto(users + "/courses/genai/")
    expect(page).to_have_url(users + "/")
    expect(page.locator("#notice")).to_contain_text("אין לך גישה לקורס CT-GenAI")


def test_anonymous_deep_link_returns_after_login(page, users):
    page.goto(users + "/courses/sql/#ch2/3")
    expect(page.locator("#fLogin")).to_be_visible()
    page.fill("#fLogin [name=email]", "sql@test.local")
    page.fill("#fLogin [name=password]", PW)
    page.click("#fLogin .pbtn")
    expect(page).to_have_url(users + "/courses/sql/#ch2/3")
    expect(page.locator("#count")).to_contain_text("3 מתוך")


def test_blocked_student_has_no_access(page, users):
    login(page, users, "blocked@test.local")
    expect(card(page, "ctfl")).to_have_class("course locked")
    page.goto(users + "/courses/ctfl/")
    expect(page).not_to_have_url(users + "/courses/ctfl/")


def test_student_without_courses_gets_message(page, users):
    login(page, users, "none@test.local")
    expect(page.locator("#notice")).to_contain_text("עדיין לא נפתחו לך קורסים")


def test_logout(page, users):
    login(page, users, "ctfl@test.local")
    page.click("#umB")
    page.click("#lo")
    expect(page.locator("#notice")).to_have_text("התנתקת.")
    expect(card(page, "ctfl")).to_have_class("course locked")
    page.goto(users + "/courses/ctfl/")
    expect(page).not_to_have_url(users + "/courses/ctfl/")


def test_forgot_password_sends_link_and_recovery_sets_new_password(page, users):
    from conftest import mail
    page.goto(users + "/")
    page.click("#liB")
    page.click("#toForgot")
    page.fill("#fF [name=email]", "ctfl@test.local")
    page.click("#fF .pbtn")
    expect(page.locator("#fF .ok")).to_contain_text("אם המייל רשום אצלנו")
    tok = [m for m in mail(users) if m["to"] == "ctfl@test.local" and m["type"] == "recovery"][-1]["token"]
    page.goto("about:blank")  # an e-mail link opens a fresh page load
    page.goto(users + "/#recovery_token=" + tok)
    expect(page.locator("#fR")).to_be_visible()
    page.fill("#fR [name=p1]", "BrandNew123")
    page.fill("#fR [name=p2]", "BrandNew123")
    page.click("#fR .pbtn")
    expect(page.locator("#notice")).to_contain_text("הסיסמה עודכנה")
    page.click("#umB"); page.click("#lo")
    login(page, users, "ctfl@test.local", "BrandNew123")
    expect(card(page, "ctfl")).not_to_have_class("course locked")
