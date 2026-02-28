---
area: general
name: fix-scipy-dependency
status: review-pending
created: 2026-02-28T07:29:39.5388450Z
assigned: Ethan
updated: 2026-02-28T07:31:28.3038700Z
---

# Task: fix-scipy-dependency

(No description)

## Progress

- [ ] (Not started)

## Files Changed

(None yet)

## Review Summary

Added 'scipy>=1.11.0' to pyproject.toml dependencies. classroom_simulation.py imports from scipy.signal but scipy was not declared as a dependency. All 46 simulation tests now pass. Two pre-existing test collection errors (test_assessment_models.py, test_assessment_routes.py) remain — they are unrelated (missing AssessmentBundle import).