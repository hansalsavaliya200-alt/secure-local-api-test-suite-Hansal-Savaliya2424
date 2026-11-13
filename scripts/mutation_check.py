"""Retest-after-fix experiment ("test the tests").

For each control, this script:
  1. copies the project to a temporary folder,
  2. deliberately BREAKS that one control in the copy (a mutation),
  3. runs the test suite and expects it to FAIL (proving the tests notice the weakness),
  4. runs the suite on the real, unmodified code and expects it to PASS (the retest).

Your real source files are never modified. Run:  python scripts/mutation_check.py
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# marker comment on the line, file, text to replace, replacement, what the weakness means
MUTATIONS = [
    ("MUT:rbac-admin-users", "app/main.py", 'require_roles("admin")', 'require_roles("user", "agent", "admin")',
     "any logged-in user may list all accounts (broken access control)"),
    ("MUT:rbac-delete", "app/main.py", 'require_roles("admin")', 'require_roles("user", "agent", "admin")',
     "any logged-in user may delete tickets (broken access control)"),
    ("MUT:ticket-ownership", "app/main.py", "not can_view(user, ticket)", "False",
     "any logged-in user may read anyone's ticket (IDOR)"),
    ("MUT:forbid-extra", "app/models.py", 'extra="forbid"', 'extra="ignore"',
     "unknown fields such as 'owner' or 'role' are silently accepted (mass assignment)"),
    ("MUT:login-limit", "app/config.py", "(5, 60)", "(5000, 60)",
     "unlimited password guessing on the login endpoint"),
]


def run_pytest(project: Path):
    result = subprocess.run([sys.executable, "-m", "pytest", "-o", "addopts=", "-q", "--tb=no", "-p", "no:cacheprovider"],
                            cwd=project, capture_output=True, text=True)
    failed = sorted(line.split(" ")[1] for line in result.stdout.splitlines() if line.startswith("FAILED "))
    summary = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    return result.returncode, failed, summary


def main() -> int:
    results, ok = [], True
    for marker, rel, old, new, meaning in MUTATIONS:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "project"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", ".venv", "venv", "__pycache__",
                                                                      ".pytest_cache", "docs", "report"))
            target = copy / rel
            lines = target.read_text().splitlines(keepends=True)
            hits = [i for i, line in enumerate(lines) if marker in line and old in line]
            if len(hits) != 1:
                print(f"[{marker}] cannot apply mutation: found {len(hits)} matching lines")
                return 2
            lines[hits[0]] = lines[hits[0]].replace(old, new)
            target.write_text("".join(lines))
            code, failed, summary = run_pytest(copy)
        detected = code != 0 and len(failed) > 0
        ok &= detected
        results.append({"mutation": marker, "weakness": meaning, "detected": detected,
                        "tests_that_failed": failed, "summary": summary})
        print(f"[{marker}] {meaning}\n    -> {'DETECTED' if detected else 'NOT DETECTED'}: {summary}")
        for name in failed[:6]:
            print(f"       failing: {name}")
    code, _failed, summary = run_pytest(ROOT)       # the retest on the real code
    retest = code == 0
    ok &= retest
    print(f"\nRetest on the real, unmodified code -> {'PASS' if retest else 'FAIL'}: {summary}")
    out = ROOT / "docs" / "evidence" / "mutation-results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"mutations": results, "retest_on_real_code": {"passed": retest, "summary": summary}}, indent=2))
    print(f"Results saved to {out.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
