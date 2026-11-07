# Week 1 Testing Baseline — SP-W1-005

## 1. Environment

- Python version: 3.12.10
- Repository: `saayam-for-all/spatial`
- Test environment: Local Python virtual environment (`.venv`)
- Test framework: pytest
- Dependencies installed using `requirements-dev.txt`

## 2. Test Results — `test` Branch

- Branch: `test`
- Commit: `540ed30`

### Application tests

Command:

```powershell
python -m pytest test_app.py -v
```

Result:
- Passed: 20
- Failed: 0
- Warnings: 97

### Location tests

Command:

```powershell
python -m pytest test_location.py -v
```

Result:
- Collection error: 1
- Tests executed: 0

Failure:

```text
ImportError: cannot import name 'get_nearest_volunteers' from 'location'
```

This is a legacy test compatibility issue. Per Lead guidance, it is deferred to SP-W2-005 and is not addressed in this PR.

## 3. Test Results — `dev` Branch

- Branch: `dev`
- Commit: `714e4e3`

### Application tests

Command:

```powershell
python -m pytest test_app.py -v
```

Result:
- Passed: 20
- Failed: 0
- Warnings: 97

### Location write tests

Command:

```powershell
python -m pytest test_location_write.py -v
```

Result:
- Passed: 4
- Failed: 0
- Warnings: 97

## 4. Warnings

The test runs reported 97 warnings. The displayed warnings originate from Werkzeug deprecation warnings in `werkzeug/routing.py`, including deprecated AST handling.

These warnings did not prevent the tests from passing.

## 5. Summary

- `test_app.py` passed all 20 tests on both branches.
- `test_location.py` on `test` failed during collection because `get_nearest_volunteers` could not be imported.
- `test_location_write.py` on `dev` passed all 4 tests.
- The legacy location test collection issue is tracked for SP-W2-005.
- Baseline results were captured using Python 3.12.10 and the local virtual environment.

## 6. Scope and Follow-up

This document records the Week 1 baseline results for SP-W1-005.

The legacy `test_location.py` collection failure is documented for follow-up under SP-W2-005. No production location code was changed as part of this documentation update.