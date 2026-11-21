#!/usr/bin/env bash
# Full QA run for the course site: static checks -> functions & lock -> browser tests -> (live checks) -> report.
# Usage: npm test        (live checks too: BASE_URL=https://... npm test)
set -u
cd "$(dirname "$0")/.."
rm -rf tests/.artifacts && mkdir -p tests/.artifacts
echo "▶ Static checks"
node --test --test-reporter=spec --test-reporter-destination=stdout --test-reporter=junit --test-reporter-destination=tests/.artifacts/integrity.xml tests/integrity.test.mjs
echo "▶ Functions and course lock"
node --test --test-reporter=spec --test-reporter-destination=stdout --test-reporter=junit --test-reporter-destination=tests/.artifacts/functions.xml tests/functions.test.mjs
echo "▶ Browser tests"
python3 -m pytest tests/e2e -q -p no:cacheprovider --junitxml=tests/.artifacts/e2e.xml -o junit_family=xunit2
if [ -n "${BASE_URL:-}" ]; then
  echo "▶ Live checks on $BASE_URL"
  python3 -m pytest tests/preview -q -p no:cacheprovider --junitxml=tests/.artifacts/live.xml -o junit_family=xunit2
fi
echo "▶ Report"
python3 tests/report.py > tests/.artifacts/summary.md
status=$?
head -22 tests/.artifacts/summary.md
echo "full report: tests/reports/latest.html"
exit $status
