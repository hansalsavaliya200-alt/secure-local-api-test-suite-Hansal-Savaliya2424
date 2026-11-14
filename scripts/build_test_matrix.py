"""Builds docs/test-matrix.md from REAL results: a pytest JUnit XML run plus docs/evidence/*.
Run:  python scripts/build_test_matrix.py      (it runs pytest itself)
"""
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XML = ROOT / "docs" / "evidence" / "junit.xml"
subprocess.run([sys.executable, "-m", "pytest", "-q", "--tb=short", f"--junitxml={XML}"], cwd=ROOT, check=True,
               stdout=subprocess.DEVNULL)

report_root = ET.parse(XML).getroot()
test_cases = list(report_root.iter("testcase"))
if not test_cases:
    raise SystemExit(f"no test cases found in {XML}")

results = {}
for case in test_cases:
    name = case.get("name").split("[")[0]
    bad = case.find("failure") is not None or case.find("error") is not None
    results[name] = results.get(name, True) and not bad

# (category, test, scenario, expected)
CURATED = [
    ("Positive", "test_health_response_contains_only_status", "Health response exposes only its status field",
     '`{"status":"ok"}`'),
    ("Positive", "test_login_success_returns_bearer_token", "Valid login", "200 and a bearer token"),
    ("Positive", "test_owner_can_read_own_ticket", "User reads own ticket", "200"),
    ("Positive", "test_status_change_by_role", "Agent/admin change ticket status", "200 for agent and admin"),
    ("Positive", "test_delete_ticket_is_admin_only", "Admin deletes a ticket", "204 for admin"),
    ("Negative", "test_login_wrong_password_is_401", "Wrong password", "401, generic message"),
    ("Negative", "test_protected_route_without_token_is_401", "No token on a protected route", "401"),
    ("Negative", "test_user_cannot_read_another_users_ticket", "User reads someone else's ticket", "404 (not 403)"),
    ("Negative", "test_admin_users_list_by_role", "User/agent list accounts", "403 for user and agent"),
    ("Negative", "test_user_cannot_make_themselves_admin", "Privilege escalation attempt", "403, role unchanged"),
    ("Negative", "test_tampered_token_is_401", "Modified JWT", "401"),
    ("Negative", "test_unsigned_alg_none_token_is_refused", "JWT with alg=none", "401"),
    ("Negative", "test_expired_token_is_401", "Expired JWT", "401"),
    ("Negative", "test_login_is_limited_after_five_attempts", "6th login attempt in 60 s", "429 with Retry-After"),
    ("Negative", "test_wrong_content_type_is_415", "Form data instead of JSON", "415"),
    ("Negative", "test_invalid_ticket_bodies_are_rejected", "Unknown field, empty title, wrong types", "422"),
    ("Boundary", "test_title_length_boundaries", "Title of 100 vs 101 characters", "100 accepted, 101 rejected"),
    ("Boundary", "test_description_length_boundaries", "Description of 1000 vs 1001 characters", "1000 accepted, 1001 rejected"),
    ("Boundary", "test_oversized_body_is_413", "Body above the size limit", "413"),
    ("Boundary", "test_chunked_oversized_body_is_413", "Chunked body above the size limit without Content-Length", "413"),
    ("Boundary", "test_malformed_ticket_ids_are_404_not_500", "Ticket ID that is not a UUID", "404, no crash"),
    ("Boundary", "test_limit_resets_after_the_window", "Wait out the 60 s window (fake clock)", "Login allowed again"),
    ("Boundary", "test_forged_forwarding_header_cannot_bypass_the_limit", "New X-Forwarded-For on each attempt", "Still limited (429)"),
    ("Boundary", "test_admin_cannot_remove_own_admin_role", "Last admin demotes themselves", "409"),
    ("Boundary", "test_role_is_read_from_the_server_not_the_token", "Role changed after token was issued", "New role applies at once"),
]
mut = json.loads((ROOT / "docs" / "evidence" / "mutation-results.json").read_text(encoding="utf-8"))
mutations = mut.get("mutations", [])
detected_mutations = sum(bool(item.get("detected")) for item in mutations)
retest = mut.get("retest_on_real_code", {})
failed_cases = sum(case.find("failure") is not None for case in test_cases)
error_cases = sum(case.find("error") is not None for case in test_cases)
skipped_cases = sum(case.find("skipped") is not None for case in test_cases)
passed_cases = len(test_cases) - failed_cases - error_cases - skipped_cases
demo_output = (ROOT / "docs" / "evidence" / "demo-output.txt").read_text(encoding="utf-8-sig")
proxy_output = (ROOT / "docs" / "evidence" / "xff-before-after.txt").read_text(encoding="utf-8-sig")
demo_passed = "ALL CHECKS PASSED" in demo_output
proxy_before_failed = "[FAIL] forged X-Forwarded-For" in proxy_output
proxy_after_passed = "[PASS] forged X-Forwarded-For" in proxy_output
function_passed = sum(results.values())

lines = [
    "# Security verification matrix",
    "",
    "**Project:** Build a secure local API and test suite",
    "",
    "**Scope:** Local FastAPI demonstration using fictional data and loopback requests only.",
    "",
    "This document summarizes representative security tests and the captured verification records. "
    "The build script runs pytest and reads its JUnit report; expected outcomes and selected examples "
    "are maintained in this script.",
    "",
    "## Verification summary",
    "",
    "| Check | Recorded result | Evidence source |",
    "|---|---|---|",
    f"| Pytest cases | {passed_cases} passed, {failed_cases} failed, {error_cases} errors, "
    f"{skipped_cases} skipped ({len(test_cases)} total) | `junit.xml` |",
    f"| Test functions | {function_passed} passed, {len(results) - function_passed} failed "
    f"({len(results)} functions; parametrized cases grouped) | `junit.xml` |",
    f"| Mutation checks | {detected_mutations} of {len(mutations)} weakened controls detected | "
    "`mutation-results.json` |",
    f"| Live demo | {'All checks passed' if demo_passed else 'Pass marker not found; inspect saved output'} "
    "| `demo-output.txt` |",
    "",
    "## Representative test cases",
    "",
    "Expected behavior is shown alongside the result for each selected test function. "
    "A `PASS` means the function passed in the latest pytest run; parametrized cases are grouped by function.",
    "",
    "| # | Class | Scenario | Expected behavior | Latest result | Test function |",
    "|---:|---|---|---|---|---|",
]
for i, (kind, test, scenario, expected) in enumerate(CURATED, 1):
    if test not in results:
        raise SystemExit(f"unknown test name {test}")
    lines.append(f"| {i} | {kind} | {scenario} | {expected} | {'PASS' if results[test] else 'FAIL'} | `{test}` |")

lines += [
    "",
    "## Mutation test results",
    "",
    "Each listed weakness was introduced only in a temporary copy. Detection means at least one test failed "
    "under that mutation; the unmodified project was then retested.",
    "",
    "| Temporary weakness | Failing tests | Detection result |",
    "|---|---:|---|",
]
for item in mutations:
    status = "Detected" if item.get("detected") else "Not detected"
    lines.append(f"| {item['weakness']} | {len(item['tests_that_failed'])} | {status} |")

retest_status = "PASS" if retest.get("passed") else "FAIL"
lines += [
    "",
    f"Retest on unmodified code: **{retest_status}** — {retest.get('summary', 'result not recorded')}.",
    "",
    "## Live-server proxy-header check",
    "",
    "| Run | Recorded outcome |",
    "|---|---|",
    "| Initial run with Uvicorn's default proxy-header handling | "
    f"{'Forwarded-header rate-limit check failed (expected 429, received 401).' if proxy_before_failed else 'See captured before/after output.'} |",
    "| Follow-up with `--no-proxy-headers` | "
    f"{'Forwarded-header check passed (429).' if proxy_after_passed else 'See captured before/after output.'} |",
    "| Full demo after the configuration change | "
    f"{'All checks passed.' if demo_passed else 'Pass marker not found in saved output.'} |",
    "",
    "The demo runs through Uvicorn and covers its proxy-header configuration. FastAPI `TestClient` "
    "does not start Uvicorn, so this server-level behavior is recorded separately from the pytest suite.",
    "",
    "## Evidence files",
    "",
    "- [JUnit report](evidence/junit.xml) — generated by this matrix build.",
    "- [Pytest transcript](evidence/pytest-output.txt) — saved console output from a recorded run.",
    "- [Mutation results](evidence/mutation-results.json) and [mutation transcript](evidence/mutation-check-output.txt).",
    "- [Live demo transcript](evidence/demo-output.txt).",
    "- [Proxy-header before/after transcript](evidence/xff-before-after.txt).",
    "",
    "## Evidence provenance",
    "",
    "Test counts and outcomes in this matrix are derived from the local JUnit and saved experiment/demo records.",
    "",
]
(ROOT / "docs" / "test-matrix.md").write_text("\n".join(lines), encoding="utf-8")
print("wrote docs/test-matrix.md;", passed_cases, "of", len(test_cases), "pytest cases passed")
