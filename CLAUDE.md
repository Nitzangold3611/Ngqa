# Working rules for this repo (NGQA course site, courses.ngqa.net)

- UI language is Hebrew (RTL). Netlify base directory is `site/`; everything outside it (tests, scripts) is never published.
- **Batch fixes into a version; push to `main` only with the owner's approval** (every push to `main` deploys production). Preview work goes on a `preview-vX.Y` branch + Pull request.
- **Before proposing a release, run the full QA suite (`npm test`, and `npm run test:live` for read-only checks on the real site) and give the owner the report** (`tests/reports/v<version>.md` summary + `tests/reports/latest.html` with screenshots). Never release with failing tests.
- New features / courses need tests. A new course must be added in all places the integrity tests check (auth.js COURSES, `_common.js` COURSE_ROLES, courses.json, home card, hub search list, admin NAMES, and a lock rule pair in `_redirects`).
- Fix flaky tests at the root cause; no sleeps.
- Every version: README versions row + CHANGELOG entry + home footer version (the integrity test enforces they match) + commit `tests/reports/v<version>.md`.
- Live checks (`tests/preview`) are read-only. Never create, change or delete real users from tests.
