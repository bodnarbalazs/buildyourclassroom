#!/usr/bin/env python3
"""Tier compliance checker.

Runs tests, collects coverage data, enriches with cyclomatic complexity,
and checks every source module against its tier's requirements.

Coverage formats:
  - Backend (.NET):      Cobertura XML via coverlet
  - Frontend (React):    LCOV via Istanbul (accurate branch coverage)
  - Microservices (Py):  Cobertura XML via pytest-cov

Usage:
    python tests/coverage/gap_check.py                    # run tests, check all stacks
    python tests/coverage/gap_check.py frontend            # single stack
    python tests/coverage/gap_check.py backend frontend    # multiple stacks
    python tests/coverage/gap_check.py --skip-tests        # analyze existing data only
    python tests/coverage/gap_check.py --detail            # show uncovered lines in failures
    python tests/coverage/gap_check.py --inspect Auth      # inspect modules matching 'Auth'
    python tests/coverage/gap_check.py --skip-tests --inspect waveform --detail
"""

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants (self-contained — not imported from report.py)
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent.parent
COVERAGE_DIR = ROOT / "tests" / "coverage"
RUNSETTINGS = COVERAGE_DIR / "coverage.runsettings"
TIER_REGISTRY_PATH = COVERAGE_DIR / "tier_registry.json"
SRC_BACKEND = ROOT / "src" / "backend"

STACKS = ["backend", "frontend", "microservices"]

XML_PATTERNS = {
    "backend": "tests/backend/**/coverage.cobertura.xml",
    "microservices": "tests/coverage/microservices/coverage.xml",
}

FRONTEND_LCOV_CANDIDATES = [
    "tests/coverage/frontend/lcov.info",
    "src/frontend/coverage/lcov.info",
]


def _find_frontend_lcov() -> Optional[Path]:
    """Return the first existing LCOV candidate path, or None."""
    for candidate in FRONTEND_LCOV_CANDIDATES:
        p = ROOT / candidate
        if p.exists():
            return p
    return None

TEST_COMMANDS = {
    "backend": [
        "dotnet", "test", "Hackathon.slnx",
        "--collect:XPlat Code Coverage",
        f"--settings:{RUNSETTINGS}",
    ],
    "frontend": ["npm", "run", "test:coverage", "--prefix", "src/frontend"],
    "microservices": [
        "uv", "run", "--directory", "src/microservices/microservice",
        "pytest", "--cov", "--cov-report", "xml",
    ],
}

MICROSERVICES_SRC = "src/microservices/microservice"
MICROSERVICES_SOURCE_DIRS = ["api", "services", "shared", "workers"]

# Tier thresholds (from testing-strategy.md / decision 005)
TIER_THRESHOLDS = {
    1: {"line_coverage": 0.80, "crap": 30, "branch_coverage": 0.60},
    2: {"line_coverage": 1.00, "crap": 15, "branch_coverage": 0.80},
    3: {"line_coverage": 1.00, "crap": 5,  "branch_coverage": 1.00},
}

# Exclusion patterns
GENERATED_PATTERNS = ["/obj/", ".g.cs", ".generated.cs", "node_modules", "/Migrations/", "GlobalUsings"]
BACKEND_EXCLUDED_CLASSES = {"Program"}
BACKEND_DATA_MODEL_MAX_LINES = 3
FRONTEND_EXCLUDED_PATTERNS = ["vite-env.d.ts", "reportWebVitals", "setupTests", "/generated/"]

TIER_ANNOTATION_RE = re.compile(r"(?://|#)\s*@test-tier:\s*(\d+)")
CONDITION_COVERAGE_RE = re.compile(r"\((\d+)/(\d+)\)")

STACK_LABELS = {
    "backend": "BACKEND (.NET)",
    "frontend": "FRONTEND (TypeScript/React)",
    "microservices": "MICROSERVICES (Python)",
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class LineLevelData:
    """Per-line hit counts for merging overlapping coverage across backend
    test assemblies."""
    lines_hits: Dict[int, int] = field(default_factory=dict)
    # Per-line branch conditions: {line_no: (covered, total)}
    branch_conditions: Dict[int, Tuple[int, int]] = field(default_factory=dict)
    class_name: str = ""
    complexity: float = 0.0

    def merge(self, line_no: int, hits: int):
        self.lines_hits[line_no] = max(self.lines_hits.get(line_no, 0), hits)

    def merge_branch(self, line_no: int, covered: int, total: int):
        existing = self.branch_conditions.get(line_no)
        if existing is None:
            self.branch_conditions[line_no] = (covered, total)
        else:
            self.branch_conditions[line_no] = (max(existing[0], covered), total)

    def merge_complexity(self, cc: float):
        self.complexity = max(self.complexity, cc)

    @property
    def lines_valid(self) -> int:
        return len(self.lines_hits)

    @property
    def lines_covered(self) -> int:
        return sum(1 for h in self.lines_hits.values() if h > 0)

    @property
    def line_rate(self) -> float:
        if self.lines_valid == 0:
            return 0.0
        return self.lines_covered / self.lines_valid

    @property
    def branch_rate(self) -> float:
        if not self.branch_conditions:
            return 1.0  # No branches to cover — vacuously satisfied
        total_covered = sum(c for c, _ in self.branch_conditions.values())
        total_possible = sum(t for _, t in self.branch_conditions.values())
        if total_possible == 0:
            return 1.0
        return total_covered / total_possible


@dataclass
class ModuleCoverage:
    """Coverage data for a single source module (file)."""
    filename: str           # Normalized path relative to src/<stack>/
    class_name: str         # Class/module name from XML
    line_rate: float        # 0.0 - 1.0
    branch_rate: float      # 0.0 - 1.0 (from condition-coverage in XML)
    lines_valid: int        # Total coverable lines
    lines_covered: int      # Lines actually hit
    complexity: float       # Cyclomatic complexity (from XML or CC enrichment)
    stack: str = ""
    tier: int = 1           # 1, 2, or 3 (detected from annotations)
    # Line-level detail for --detail / --inspect modes
    line_hits: Dict[int, int] = field(default_factory=dict)
    branch_conditions: Dict[int, Tuple[int, int]] = field(default_factory=dict)

    @property
    def crap(self) -> float:
        """CRAP = CC^2 * (1 - coverage)^3 + CC"""
        if self.complexity > 0:
            return (self.complexity ** 2) * ((1 - self.line_rate) ** 3) + self.complexity
        return 0.0

    @property
    def has_tests(self) -> bool:
        return self.lines_covered > 0

    @property
    def tier_thresholds(self) -> dict:
        return TIER_THRESHOLDS[self.tier]

    @property
    def failures(self) -> list[str]:
        """Return list of human-readable failure reasons."""
        reasons = []
        t = self.tier_thresholds
        if not self.has_tests:
            reasons.append("no test coverage")
        if self.line_rate < t["line_coverage"]:
            reasons.append(f"line: {self.line_rate*100:.1f}% (need >= {t['line_coverage']*100:.0f}%)")
        if self.complexity > 0 and self.crap > t["crap"]:
            reasons.append(f"CRAP: {self.crap:.1f} (need <= {t['crap']})")
        if self.branch_rate < t["branch_coverage"]:
            reasons.append(f"branch: {self.branch_rate*100:.1f}% (need >= {t['branch_coverage']*100:.0f}%)")
        return reasons

    @property
    def passes(self) -> bool:
        return len(self.failures) == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_generated(filename: str) -> bool:
    """Return True if the normalized (forward-slash) path looks auto-generated."""
    for pat in GENERATED_PATTERNS:
        if pat in filename:
            return True
    return False


def normalize_to_forward_slash(raw: str) -> str:
    return raw.replace("\\", "/")


def collapse_ranges(numbers: List[int]) -> str:
    """Collapse sorted integers into range notation: [1,2,3,5,7,8,9] -> '1-3, 5, 7-9'."""
    if not numbers:
        return ""
    sorted_nums = sorted(numbers)
    ranges: List[str] = []
    start = prev = sorted_nums[0]
    for n in sorted_nums[1:]:
        if n == prev + 1:
            prev = n
        else:
            ranges.append(f"{start}-{prev}" if start != prev else str(start))
            start = prev = n
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ", ".join(ranges)


def format_line_detail(module: "ModuleCoverage") -> List[str]:
    """Format uncovered lines and partial branches for display."""
    if not module.line_hits:
        return []
    lines: List[str] = []
    uncovered = [lno for lno, hits in module.line_hits.items() if hits == 0]
    if uncovered:
        lines.append(f"        uncovered lines:  {collapse_ranges(uncovered)}")
    partial = sorted(
        lno for lno, (covered, total) in module.branch_conditions.items()
        if covered < total
    )
    if partial:
        parts = [f"{lno} ({module.branch_conditions[lno][0]}/{module.branch_conditions[lno][1]})" for lno in partial]
        lines.append(f"        partial branches: {', '.join(parts)}")
    return lines


def resolve_backend_filename(source_dir: str, raw_filename: str) -> str:
    """Resolve a backend filename to a path relative to src/backend/.

    Different test assemblies report different <source> base directories:
      - Hackathon.Application.Tests: source = .../src/backend/
        filename = Hackathon.Domain/Models/Foo.cs
      - Hackathon.Domain.Tests:      source = .../src/backend/Hackathon.Domain/Models/
        filename = Foo.cs

    We join source + filename, normalize, then make relative to src/backend/.
    """
    abs_path = os.path.normpath(os.path.join(source_dir, raw_filename))
    try:
        rel = os.path.relpath(abs_path, SRC_BACKEND)
    except ValueError:
        rel = normalize_to_forward_slash(raw_filename)
    return normalize_to_forward_slash(rel)


# ---------------------------------------------------------------------------
# XML parsing
# ---------------------------------------------------------------------------

def _parse_branch_conditions(line_el) -> Optional[Tuple[int, int]]:
    """Extract (covered, total) branch conditions from a <line> element.

    Parses the condition-coverage attribute, e.g. "50% (1/2)" -> (1, 2).
    Returns None if the line has no branch conditions.
    """
    if line_el.get("branch", "").lower() != "true":
        return None
    cond_cov = line_el.get("condition-coverage", "")
    m = CONDITION_COVERAGE_RE.search(cond_cov)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def parse_backend_xml(xml_path: str) -> List[Tuple[str, str, Dict[int, int], Dict[int, Tuple[int, int]], float]]:
    """Parse a backend Cobertura XML using <source> for path resolution.

    Returns list of (resolved_relative_filename, class_name, {line_no: hits},
                      {line_no: (conditions_covered, conditions_total)}, complexity).
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    source_dirs = []
    for src_el in root.findall(".//source"):
        if src_el.text:
            source_dirs.append(src_el.text.strip())
    source_dir = source_dirs[0] if source_dirs else ""

    results = []
    for pkg in root.findall(".//package"):
        for cls in pkg.findall(".//class"):
            raw_fname = cls.get("filename", "")
            cname = cls.get("name", "")
            if not raw_fname:
                continue

            resolved = resolve_backend_filename(source_dir, raw_fname)
            complexity = float(cls.get("complexity", 0))

            line_hits: Dict[int, int] = {}
            branch_conds: Dict[int, Tuple[int, int]] = {}
            lines_el = cls.find("lines")
            if lines_el is not None:
                for line_el in lines_el.findall("line"):
                    try:
                        lno = int(line_el.get("number", "0"))
                        hits = int(line_el.get("hits", "0"))
                        line_hits[lno] = max(line_hits.get(lno, 0), hits)
                    except (ValueError, TypeError):
                        continue
                    cond = _parse_branch_conditions(line_el)
                    if cond is not None:
                        branch_conds[lno] = cond

            results.append((resolved, cname, line_hits, branch_conds, complexity))

    return results


def parse_generic_xml(xml_path: str) -> List[Tuple[str, str, Dict[int, int], Dict[int, Tuple[int, int]], float]]:
    """Parse a Cobertura XML for frontend/microservices.

    Returns list of (filename, class_name, {line_no: hits},
                      {line_no: (conditions_covered, conditions_total)}, complexity).
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    results = []
    for pkg in root.findall(".//package"):
        for cls in pkg.findall(".//class"):
            fname = cls.get("filename", "")
            cname = cls.get("name", "")
            if not fname:
                continue

            complexity = float(cls.get("complexity", 0))

            line_hits: Dict[int, int] = {}
            branch_conds: Dict[int, Tuple[int, int]] = {}
            lines_el = cls.find("lines")
            if lines_el is not None:
                for line_el in lines_el.findall("line"):
                    try:
                        lno = int(line_el.get("number", "0"))
                        hits = int(line_el.get("hits", "0"))
                        line_hits[lno] = max(line_hits.get(lno, 0), hits)
                    except (ValueError, TypeError):
                        continue
                    cond = _parse_branch_conditions(line_el)
                    if cond is not None:
                        branch_conds[lno] = cond

            results.append((normalize_to_forward_slash(fname), cname, line_hits, branch_conds, complexity))

    return results


# ---------------------------------------------------------------------------
# LCOV parsing (frontend)
# ---------------------------------------------------------------------------

def parse_lcov(
    lcov_path: str,
    cc_data: Optional[Dict[str, int]] = None,
) -> List[Tuple[str, str, Dict[int, int], Dict[int, Tuple[int, int]], float]]:
    """Parse an LCOV info file.

    LCOV cleanly separates line (DA), branch (BRDA), and function (FN/FNDA)
    coverage.  Unlike Istanbul's Cobertura XML reporter, it does not fabricate
    branch entries from function coverage.

    Args:
        lcov_path: Path to the lcov.info file.
        cc_data: Optional {filename: max_cyclomatic_complexity} from ESLint.

    Returns list of (filename, class_name, {line_no: hits},
                      {line_no: (conditions_covered, conditions_total)}, complexity).
    """
    if cc_data is None:
        cc_data = {}

    results = []
    current_file: Optional[str] = None
    line_hits: Dict[int, int] = {}
    branch_arms: Dict[int, List[int]] = {}

    with open(lcov_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            if line.startswith("SF:"):
                current_file = line[3:]
                line_hits = {}
                branch_arms = {}

            elif line.startswith("DA:"):
                parts = line[3:].split(",")
                if len(parts) >= 2:
                    try:
                        lno = int(parts[0])
                        hits = int(parts[1])
                        line_hits[lno] = hits
                    except ValueError:
                        pass

            elif line.startswith("BRDA:"):
                # BRDA:<line>,<block>,<branch>,<taken>
                parts = line[5:].split(",")
                if len(parts) >= 4:
                    try:
                        lno = int(parts[0])
                        taken = 0 if parts[3].strip() == "-" else int(parts[3])
                        if lno not in branch_arms:
                            branch_arms[lno] = []
                        branch_arms[lno].append(taken)
                    except ValueError:
                        pass

            elif line == "end_of_record":
                if current_file:
                    fname = normalize_to_forward_slash(current_file)
                    # Aggregate branch arms into (covered, total) per line
                    branch_conds: Dict[int, Tuple[int, int]] = {}
                    for lno, arms in branch_arms.items():
                        total = len(arms)
                        covered = sum(1 for a in arms if a > 0)
                        branch_conds[lno] = (covered, total)

                    complexity = float(cc_data.get(fname, 0))
                    cname = fname.rsplit("/", 1)[-1] if "/" in fname else fname

                    results.append((fname, cname, line_hits, branch_conds, complexity))
                current_file = None

    return results


# ---------------------------------------------------------------------------
# Test running
# ---------------------------------------------------------------------------

def clean_stale_coverage(stacks: list[str]):
    """Remove old coverage files so only fresh data is used."""
    for stack in stacks:
        if stack in XML_PATTERNS:
            for xml in sorted(ROOT.glob(XML_PATTERNS[stack])):
                xml.unlink()
                print(f"  Cleaned {xml.relative_to(ROOT)}")
        if stack == "frontend":
            for candidate in FRONTEND_LCOV_CANDIDATES:
                lcov = ROOT / candidate
                if lcov.exists():
                    lcov.unlink()
                    print(f"  Cleaned {lcov.relative_to(ROOT)}")


def run_tests(stacks: list[str]) -> bool:
    """Run test commands for the given stacks. Returns True if all succeed."""
    clean_stale_coverage(stacks)
    ok = True
    for stack in stacks:
        cmd = TEST_COMMANDS[stack]
        print(f"\n--- Running {stack} tests ---")
        print(f"  {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=ROOT, shell=True)
        if result.returncode != 0:
            print(f"  [{stack}] Tests failed (exit code {result.returncode})")
            ok = False
    return ok


# ---------------------------------------------------------------------------
# CC enrichment
# ---------------------------------------------------------------------------

def compute_frontend_cc() -> Dict[str, int]:
    """Run ESLint complexity analysis, return {filename: max_cc} mapping.

    Unlike the old enrich_frontend_cc() which injected CC into Cobertura XML,
    this returns the data directly so it can be passed to parse_lcov().
    """
    print("\n--- Computing frontend CC (ESLint) ---")
    cmd = ["npx", "eslint", "--rule", "complexity: [warn, 1]", "--format", "json", "src/"]
    result = subprocess.run(
        cmd, cwd=ROOT / "src" / "frontend", shell=True,
        capture_output=True, text=True,
    )
    if result.returncode not in (0, 1):  # 1 = warnings found (expected)
        print(f"  ESLint failed (exit {result.returncode}), skipping CC")
        return {}

    try:
        eslint_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("  ESLint output not valid JSON, skipping CC")
        return {}

    cc_by_file: Dict[str, int] = {}
    cc_pattern = re.compile(r"has a complexity of (\d+)")
    for entry in eslint_data:
        filepath = entry.get("filePath", "").replace("\\", "/")
        marker = "src/frontend/"
        idx = filepath.find(marker)
        if idx != -1:
            filepath = filepath[idx + len(marker):]
        # Use max per-function CC (CRAP is a per-method metric per decision 005)
        max_cc = 0
        for msg in entry.get("messages", []):
            if msg.get("ruleId") == "complexity":
                m = cc_pattern.search(msg.get("message", ""))
                if m:
                    max_cc = max(max_cc, int(m.group(1)))
        if max_cc > 0:
            cc_by_file[filepath] = max_cc

    print(f"  Found CC data for {len(cc_by_file)} files")
    return cc_by_file


def enrich_microservices_cc():
    """Run radon complexity analysis and inject CC values into microservices cobertura XML."""
    xml_path = ROOT / "tests/coverage/microservices/coverage.xml"
    if not xml_path.exists():
        return

    print("\n--- Enriching microservices CC (radon) ---")
    source_paths = [
        f"{MICROSERVICES_SRC}/{d}" for d in MICROSERVICES_SOURCE_DIRS
        if (ROOT / MICROSERVICES_SRC / d).exists()
    ]
    if not source_paths:
        print("  No source directories found, skipping CC enrichment")
        return

    cmd = ["uvx", "radon", "cc", "-j"] + source_paths
    result = subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  radon failed (exit {result.returncode}), skipping CC enrichment")
        return

    try:
        radon_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("  radon output not valid JSON, skipping CC enrichment")
        return

    cc_by_file: dict[str, int] = {}
    for filepath, functions in radon_data.items():
        normalized = filepath.replace("\\", "/")
        # Use max per-function CC (CRAP is a per-method metric per decision 005)
        max_cc = max((f.get("complexity", 0) for f in functions), default=0)
        if max_cc > 0:
            cc_by_file[normalized] = max_cc

    if not cc_by_file:
        print("  No complexity data found")
        return

    tree = ET.parse(xml_path)
    enriched = 0
    for cls in tree.findall(".//class"):
        filename = cls.get("filename", "").replace("\\", "/")
        for radon_path, cc in cc_by_file.items():
            if radon_path.endswith("/" + filename):
                cls.set("complexity", str(cc))
                enriched += 1
                break

    tree.write(xml_path, xml_declaration=True)
    print(f"  Enriched {enriched} classes with CC data ({len(cc_by_file)} files from radon)")


# ---------------------------------------------------------------------------
# Coverage collection
# ---------------------------------------------------------------------------

def collect_backend() -> List[ModuleCoverage]:
    """Parse backend XMLs, merge line-level data across test assemblies, apply exclusions."""
    xml_files = sorted(ROOT.glob(XML_PATTERNS["backend"]))

    if not xml_files:
        print("[WARN] No backend coverage XML files found.")
        return []

    print(f"  Backend: found {len(xml_files)} coverage XML files")

    merged: Dict[str, LineLevelData] = {}

    for xml_path in xml_files:
        entries = parse_backend_xml(str(xml_path))
        for fname, cname, line_hits, branch_conds, complexity in entries:
            if is_generated(fname):
                continue

            if fname not in merged:
                merged[fname] = LineLevelData(class_name=cname)
            for lno, hits in line_hits.items():
                merged[fname].merge(lno, hits)
            for lno, (covered, total) in branch_conds.items():
                merged[fname].merge_branch(lno, covered, total)
            merged[fname].merge_complexity(complexity)
            # Prefer the most-qualified class name
            if len(cname) > len(merged[fname].class_name):
                merged[fname].class_name = cname

    results: List[ModuleCoverage] = []
    for fname, data in merged.items():
        if data.lines_valid == 0:
            continue

        short_name = data.class_name.split(".")[-1] if data.class_name else ""
        if short_name in BACKEND_EXCLUDED_CLASSES:
            continue

        if data.lines_valid <= BACKEND_DATA_MODEL_MAX_LINES and data.lines_covered == 0:
            continue

        results.append(ModuleCoverage(
            filename=fname,
            class_name=data.class_name,
            line_rate=data.line_rate,
            branch_rate=data.branch_rate,
            lines_valid=data.lines_valid,
            lines_covered=data.lines_covered,
            complexity=data.complexity,
            stack="backend",
            line_hits=dict(data.lines_hits),
            branch_conditions=dict(data.branch_conditions),
        ))

    return results


def collect_frontend(cc_data: Optional[Dict[str, int]] = None) -> List[ModuleCoverage]:
    """Parse frontend LCOV, apply exclusions."""
    lcov_path = _find_frontend_lcov()
    if lcov_path is None:
        print("[WARN] Frontend LCOV file not found.")
        return []

    print(f"  Frontend: parsing {lcov_path.relative_to(ROOT)}")

    entries = parse_lcov(str(lcov_path), cc_data)
    results: List[ModuleCoverage] = []

    for fname, cname, line_hits, branch_conds, complexity in entries:
        if is_generated(fname):
            continue

        skip = False
        for pat in FRONTEND_EXCLUDED_PATTERNS:
            if pat in fname:
                skip = True
                break
        if skip:
            continue

        lines_valid = len(line_hits)
        lines_covered = sum(1 for h in line_hits.values() if h > 0)
        if lines_valid == 0:
            continue

        line_rate = lines_covered / lines_valid
        total_covered = sum(c for c, _ in branch_conds.values())
        total_possible = sum(t for _, t in branch_conds.values())
        branch_rate = total_covered / total_possible if total_possible > 0 else 1.0

        results.append(ModuleCoverage(
            filename=fname,
            class_name=cname,
            line_rate=line_rate,
            branch_rate=branch_rate,
            lines_valid=lines_valid,
            lines_covered=lines_covered,
            complexity=complexity,
            stack="frontend",
            line_hits=dict(line_hits),
            branch_conditions=dict(branch_conds),
        ))

    return results


def collect_microservices() -> List[ModuleCoverage]:
    """Parse microservices XML, apply exclusions."""
    xml_path = ROOT / XML_PATTERNS["microservices"]
    if not xml_path.exists():
        print("[WARN] Microservices coverage XML not found.")
        return []

    print("  Microservices: parsing coverage.xml")

    entries = parse_generic_xml(str(xml_path))
    results: List[ModuleCoverage] = []

    for fname, cname, line_hits, branch_conds, complexity in entries:
        if is_generated(fname):
            continue

        lines_valid = len(line_hits)
        lines_covered = sum(1 for h in line_hits.values() if h > 0)
        if lines_valid == 0:
            continue

        line_rate = lines_covered / lines_valid
        total_covered = sum(c for c, _ in branch_conds.values())
        total_possible = sum(t for _, t in branch_conds.values())
        branch_rate = total_covered / total_possible if total_possible > 0 else 1.0

        results.append(ModuleCoverage(
            filename=fname,
            class_name=cname,
            line_rate=line_rate,
            branch_rate=branch_rate,
            lines_valid=lines_valid,
            lines_covered=lines_covered,
            complexity=complexity,
            stack="microservices",
            line_hits=dict(line_hits),
            branch_conditions=dict(branch_conds),
        ))

    return results


# ---------------------------------------------------------------------------
# Tier annotation scanning
# ---------------------------------------------------------------------------

def find_test_file(module: ModuleCoverage) -> Optional[Path]:
    """Find the corresponding test file for a source module."""
    if module.stack == "frontend":
        # Co-located: src/components/Foo.tsx -> src/components/Foo.test.tsx
        source_path = ROOT / "src" / "frontend" / module.filename
        stem = source_path.stem
        parent = source_path.parent
        for ext in [".test.tsx", ".test.ts"]:
            candidate = parent / f"{stem}{ext}"
            if candidate.exists():
                return candidate

    elif module.stack == "backend":
        # Hackathon.Domain/Models/Foo.cs -> tests/backend/Hackathon.Domain.Tests/**/FooTests.cs
        base_name = Path(module.filename).stem
        test_name = f"{base_name}Tests.cs"
        parts = module.filename.split("/")
        project = parts[0] if parts else ""
        test_project = f"{project}.Tests"
        test_dir = ROOT / "tests" / "backend" / test_project
        if test_dir.exists():
            matches = list(test_dir.rglob(test_name))
            if matches:
                return matches[0]

    elif module.stack == "microservices":
        # api/routes/health.py -> tests/test_health.py
        base_name = Path(module.filename).stem
        test_name = f"test_{base_name}.py"
        test_dir = ROOT / MICROSERVICES_SRC / "tests"
        candidate = test_dir / test_name
        if candidate.exists():
            return candidate
        matches = list(test_dir.rglob(test_name))
        if matches:
            return matches[0]

    return None


def read_tier_from_test_file(test_file: Path) -> Optional[int]:
    """Read @test-tier annotation from the first 10 lines of a test file."""
    try:
        with open(test_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 10:
                    break
                m = TIER_ANNOTATION_RE.search(line)
                if m:
                    tier = int(m.group(1))
                    if tier in (2, 3):
                        return tier
    except (OSError, UnicodeDecodeError):
        pass
    return None


def assign_tiers(modules: List[ModuleCoverage]) -> None:
    """Find test files, read tier annotations, assign tiers to modules."""
    for module in modules:
        test_file = find_test_file(module)
        if test_file is not None:
            tier = read_tier_from_test_file(test_file)
            if tier is not None:
                module.tier = tier


# ---------------------------------------------------------------------------
# Tier registry
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    if TIER_REGISTRY_PATH.exists():
        with open(TIER_REGISTRY_PATH, "r") as f:
            return json.load(f)
    return {}


def save_registry(registry: dict) -> None:
    with open(TIER_REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2, sort_keys=True)
        f.write("\n")


def check_tier_registry(modules: List[ModuleCoverage]) -> List[str]:
    """Sync tier annotations with the registry. Returns list of error messages.

    Rules:
    1. Module has annotation + not in registry -> add to registry (auto)
    2. Module has annotation + in registry with same tier -> no action
    3. Module has annotation + in registry with different tier -> update registry
    4. Module has no annotation + in registry -> ERROR (accidental demotion)
    5. Registry entry but test file doesn't exist -> ERROR
    """
    registry = load_registry()
    errors = []
    seen_keys = set()

    for module in modules:
        if module.tier > 1:
            key = module.filename
            seen_keys.add(key)
            test_file = find_test_file(module)
            test_path = str(test_file.relative_to(ROOT)) if test_file else ""
            registry[key] = {"tier": module.tier, "test_file": test_path.replace("\\", "/")}

    # Check for orphaned registry entries
    for key, entry in registry.items():
        if key not in seen_keys:
            errors.append(
                f"TIER REGISTRY: '{key}' is registered as T{entry['tier']} "
                f"but no @test-tier annotation found in test file. "
                f"If demotion is intentional, remove the entry from tier_registry.json manually."
            )

    save_registry(registry)
    return errors


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_report(all_modules: List[ModuleCoverage], stacks: list[str], *, detail: bool = False) -> bool:
    """Print per-stack and grand summary. Returns True if any module fails."""
    print(f"=== COVERAGE GAP CHECK ===")
    print(f"  Stacks: {', '.join(stacks)}")

    grand_total = 0
    grand_passing = 0
    grand_failing = 0
    has_failures = False

    for stack in stacks:
        stack_modules = [m for m in all_modules if m.stack == stack]
        if not stack_modules:
            continue

        total = len(stack_modules)
        passing = sum(1 for m in stack_modules if m.passes)
        failing = total - passing
        pct = passing / total * 100 if total else 0

        grand_total += total
        grand_passing += passing
        grand_failing += failing

        print(f"\n=== {STACK_LABELS[stack]} ===\n")
        print(f"  Total modules:      {total}")
        print(f"  Passing:            {passing}  ({pct:.1f}%)")
        print(f"  Failing:            {failing}")

        failing_modules = [m for m in stack_modules if not m.passes]
        if failing_modules:
            has_failures = True
            print()
            failing_sorted = sorted(failing_modules, key=lambda m: m.lines_valid, reverse=True)
            for m in failing_sorted:
                reasons = "  |  ".join(m.failures)
                print(f"  FAIL  {m.filename}  [T{m.tier}]")
                print(f"        {reasons}")
                if detail:
                    for line in format_line_detail(m):
                        print(line)
        else:
            print(f"\n  All modules pass.")

    # Grand summary
    print(f"\n=== GRAND SUMMARY ===\n")
    grand_pct = grand_passing / grand_total * 100 if grand_total else 0
    print(f"  Total modules:  {grand_total}")
    print(f"  Passing:        {grand_passing}  ({grand_pct:.1f}%)")
    print(f"  Failing:        {grand_failing}")

    if has_failures:
        print(f"\n  [RESULT] {grand_failing} modules fail tier requirements. See details above.")
    else:
        print(f"\n  [RESULT] All modules pass tier requirements.")

    return has_failures


def print_inspect_report(all_modules: List[ModuleCoverage], pattern: str) -> None:
    """Print detailed line-level coverage for modules matching a pattern."""
    pattern_lower = pattern.lower()
    matched = [
        m for m in all_modules
        if pattern_lower in m.filename.lower() or pattern_lower in m.class_name.lower()
    ]

    if not matched:
        print(f"\n  No modules matching '{pattern}'.")
        # Suggest alternatives using the longest word in the pattern
        words = pattern_lower.replace("/", " ").replace("\\", " ").replace(".", " ").split()
        suggestions = set()
        for word in words:
            if len(word) < 3:
                continue
            for m in all_modules:
                if word in m.filename.lower() or word in m.class_name.lower():
                    suggestions.add(m.filename)
        if suggestions:
            print(f"  Did you mean one of these?")
            for s in sorted(suggestions)[:10]:
                print(f"    - {s}")
        else:
            print(f"  Available modules (showing first 10):")
            for m in sorted(all_modules, key=lambda x: x.filename)[:10]:
                print(f"    - {m.filename}")
        return

    print(f"\n=== INSPECT: '{pattern}' ({len(matched)} match{'es' if len(matched) != 1 else ''}) ===\n")

    for m in sorted(matched, key=lambda x: (x.stack, x.filename)):
        status = "PASS" if m.passes else "FAIL"
        print(f"  [{status}]  {m.filename}  [{m.stack}]  [T{m.tier}]")
        print(f"        lines: {m.lines_covered}/{m.lines_valid} ({m.line_rate*100:.1f}%)  "
              f"branches: {m.branch_rate*100:.1f}%  "
              f"CRAP: {m.crap:.1f}  CC: {m.complexity:.0f}")
        if m.failures:
            print(f"        failures: {' | '.join(m.failures)}")
        detail_lines = format_line_detail(m)
        if detail_lines:
            for line in detail_lines:
                print(line)
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Tier compliance checker")
    parser.add_argument(
        "stacks", nargs="*", default=STACKS,
        metavar="STACK",
        help=f"Stacks to include (default: all). Options: {', '.join(STACKS)}",
    )
    parser.add_argument(
        "--skip-tests", action="store_true",
        help="Skip test execution, analyze existing data only",
    )
    parser.add_argument(
        "--detail", action="store_true",
        help="Show uncovered line numbers and partial branches for failing modules",
    )
    parser.add_argument(
        "--inspect", metavar="PATTERN",
        help="Show full line-level detail for modules matching PATTERN "
             "(substring match on filename or class name)",
    )
    args = parser.parse_args()

    stacks = args.stacks
    invalid = [s for s in stacks if s not in STACKS]
    if invalid:
        parser.error(f"invalid stack(s): {', '.join(invalid)}. Choose from: {', '.join(STACKS)}")

    # 1. Run tests (unless --skip-tests)
    if not args.skip_tests:
        tests_ok = run_tests(stacks)
        if not tests_ok:
            print("\nSome tests failed. Analyzing available coverage data anyway.")
        if "microservices" in stacks:
            enrich_microservices_cc()

    # 2. Compute frontend CC (ESLint — runs on source, independent of tests)
    frontend_cc: Dict[str, int] = {}
    if "frontend" in stacks:
        frontend_cc = compute_frontend_cc()

    # 3. Collect coverage data
    print("\nCollecting coverage data...")
    all_modules: List[ModuleCoverage] = []
    if "backend" in stacks:
        all_modules.extend(collect_backend())
    if "frontend" in stacks:
        all_modules.extend(collect_frontend(frontend_cc))
    if "microservices" in stacks:
        all_modules.extend(collect_microservices())

    if not all_modules:
        print("\nNo coverage data found.")
        if args.skip_tests:
            print("Run without --skip-tests to execute tests first.")
        sys.exit(1)

    # 4. Assign tiers from annotations
    assign_tiers(all_modules)

    # 5. Check tier registry
    registry_errors = check_tier_registry(all_modules)

    # 6. Print report
    print()
    has_failures = print_report(all_modules, stacks, detail=args.detail)

    # 7. Print inspect report (if requested)
    if args.inspect:
        print_inspect_report(all_modules, args.inspect)

    # 8. Print registry errors
    if registry_errors:
        print()
        for err in registry_errors:
            print(f"  ERROR: {err}")

    # 9. Exit
    if has_failures or registry_errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
