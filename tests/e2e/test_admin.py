"""דף הניהול: הזמנה, השלמת הרשמה, פתיחה וסגירה של קורסים, חסימה, מחיקה."""
from playwright.sync_api import expect
from conftest import login, shot, card, mail, OWNER


def _switch(scope, sel, on):
    """Toggle a styled switch the way a user does: click its label."""
    inp = scope.locator(sel)
    if inp.is_checked() != on:
        inp.locator("xpath=ancestor::label[1]").click()
    expect(inp).to_be_checked(checked=on)


def _open_admin(page, base):
    login(page, base, OWNER)
    expect(page.locator("#umB")).to_be_visible()
    page.goto(base + "/admin/")
    expect(page.locator("#list .u").first).to_be_visible()


def test_students_cannot_open_admin(page, users):
    login(page, users, "ctfl@test.local")
    expect(page.locator("#umB")).to_be_visible()
    page.click("#umB")
    expect(page.locator("a[href='/admin/']")).to_have_count(0)
    page.goto(users + "/admin/")
    expect(page.locator("#list .u")).to_have_count(0)


def test_invite_then_student_completes_registration(page, browser, users, request):
    _open_admin(page, users)
    page.fill("#inv [name=name]", "רונית לוי")
    page.fill("#inv [name=email]", "ronit@test.local")
    _switch(page.locator("#inv"), "[name=r][value=genai]", False)
    _switch(page.locator("#inv"), "[name=r][value=sql]", False)
    page.click("#inv .btn")
    expect(page.locator("#toast")).to_contain_text("ההזמנה נשלחה ל-ronit@test.local")
    expect(page.locator("#waT")).to_contain_text("courses.ngqa.net")
    row = page.locator(".u", has_text="ronit@test.local")
    expect(row).to_contain_text("טרם נרשם")
    shot(page, "admin-invite")
    tok = [m for m in mail(users) if m["to"] == "ronit@test.local" and m["type"] == "invite"][-1]["token"]
    ctx = browser.new_context(); request.addfinalizer(ctx.close); s = ctx.new_page()
    s.goto(users + "/#invite_token=" + tok)
    expect(s.locator("#fI")).to_be_visible()
    s.fill("#fI [name=p1]", "RonitPass123"); s.fill("#fI [name=p2]", "RonitPass999")
    s.click("#fI .pbtn")
    expect(s.locator("#fI .err")).to_have_text("הסיסמאות לא זהות.")
    s.fill("#fI [name=p2]", "RonitPass123")
    s.click("#fI .pbtn")
    expect(s.locator("#notice")).to_contain_text("ההרשמה הושלמה")
    expect(s.locator(".course[data-c='ctfl']")).not_to_have_class("course locked")
    expect(s.locator(".course[data-c='genai']")).to_have_class("course locked")


def test_toggle_course_takes_effect_for_student_on_refresh(page, browser, users, request):
    ctx = browser.new_context(); request.addfinalizer(ctx.close); s = ctx.new_page()
    login(s, users, "ctfl@test.local")
    expect(s.locator(".course[data-c='sql']")).to_have_class("course locked")
    _open_admin(page, users)
    row = page.locator(".u", has_text="ctfl@test.local")
    _switch(row, "input[data-c=sql]", True)
    expect(page.locator("#toast")).to_contain_text("SQL: נפתח")
    s.reload()
    expect(s.locator(".course[data-c='sql']")).not_to_have_class("course locked")
    s.goto(users + "/courses/sql/")
    expect(s).to_have_url(users + "/courses/sql/")
    # close it again -> the server lock applies on the next visit
    _switch(row, "input[data-c=sql]", False)
    expect(page.locator("#toast")).to_contain_text("SQL: נסגר")
    s.goto(users + "/")
    expect(s.locator(".course[data-c='sql']")).to_have_class("course locked")
    s.goto(users + "/courses/sql/")
    expect(s).not_to_have_url(users + "/courses/sql/")


def test_block_and_unblock_restores_courses(page, users):
    _open_admin(page, users)
    row = page.locator(".u", has_text="all@test.local")
    row.locator(".more>button").click()
    row.locator("[data-a=block]").click()
    expect(row.locator(".chip.blk")).to_be_visible()
    expect(row.locator("input[data-c=ctfl]")).not_to_be_checked()
    row.locator(".more>button").click()
    row.locator("[data-a=block]").click()
    expect(row.locator(".chip.blk")).to_have_count(0)
    for c in ["ctfl", "genai", "sql"]:
        expect(row.locator(f"input[data-c={c}]")).to_be_checked()


def test_search_and_delete_student(page, users):
    _open_admin(page, users)
    page.fill("#q", "sql@")
    expect(page.locator("#list .u")).to_have_count(1)
    row = page.locator(".u", has_text="sql@test.local")
    row.locator(".more>button").click()
    row.locator("[data-a=delete]").click()
    expect(page.locator(".u", has_text="sql@test.local")).to_have_count(0)
    page.fill("#q", "")
    me = page.locator(".u", has_text=OWNER)
    me.locator(".more>button").click()
    expect(me.locator("[data-a=delete]")).to_have_count(0)
