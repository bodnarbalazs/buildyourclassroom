---
area: general
type: reference
---

# Coverage Tools

Two in-house Python scripts for measuring and enforcing test coverage across all stacks. Located in `tests/coverage/`.

---

## `report.py` — Visual Report (for humans)

Collects Cobertura XML coverage data, enriches it with cyclomatic complexity, and generates an HTML report via ReportGenerator.

```bash
python tests/coverage/report.py                  # all stacks, report from existing data
python tests/coverage/report.py backend          # single stack
python tests/coverage/report.py frontend backend # multiple stacks
python tests/coverage/report.py --run-tests      # run tests first, then report
python tests/coverage/report.py --no-open        # skip opening browser
```

**Output:** HTML report at `tests/coverage/report/index.html`, CRAP summary to stdout.

---

## `gap_check.py` — Tier Compliance (for agents)

Self-contained tier compliance checker. Runs tests, collects coverage, enriches CC, and checks every source module against its tier's requirements. Exits with code 0 (all pass) or 1 (failures).

```bash
python tests/coverage/gap_check.py                    # run tests, check all stacks
python tests/coverage/gap_check.py frontend            # single stack
python tests/coverage/gap_check.py backend frontend    # multiple stacks
python tests/coverage/gap_check.py --skip-tests        # analyze existing coverage data only
python tests/coverage/gap_check.py --detail            # show uncovered lines in failures
python tests/coverage/gap_check.py --inspect Auth      # inspect modules matching 'Auth'
```

### What it checks (per module, against assigned tier)

| Metric | T1 | T2 | T3 |
|--------|----|----|-----|
| Has test file | required | required | required |
| Line coverage | >= 80% | 100% | 100% |
| Branch coverage | >= 60% | >= 80% | 100% |
| CRAP score | <= 30 | <= 15 | <= 5 |

### Tier detection

All modules default to T1. Higher tiers are declared with a comment annotation in the first 10 lines of the **test file**:

```typescript
// @test-tier: 2
```

```csharp
// @test-tier: 2
```

```python
# @test-tier: 2
```

### Tier registry

Promotions are tracked in `tests/coverage/tier_registry.json` (committed to git). Adding a `@test-tier` annotation auto-registers the module. Removing an annotation without manually editing the registry produces an error — this prevents accidental demotions.

---

## Directory Structure

```
tests/coverage/
├── report.py              # Human-facing: HTML report pipeline
├── gap_check.py           # Agent-facing: tier compliance checker
├── tier_registry.json     # Tracks T2/T3 promotions (committed to git)
├── coverage.runsettings   # .NET coverage config
├── report/                # Generated HTML report (gitignored)
├── frontend/              # Raw frontend coverage data (gitignored)
└── microservices/         # Raw microservices coverage data (gitignored)
```

---

## Related

- [Testing Strategy](../guides/testing-strategy.md) — Tier definitions and thresholds
- [Coverage Tooling Decision](../project/decisions/006-coverage-tooling-split.md) — Why two scripts, design rationale
- [CRAP Score Thresholds](../project/decisions/002-crap-score-tier-thresholds.md) — CRAP formula analysis
