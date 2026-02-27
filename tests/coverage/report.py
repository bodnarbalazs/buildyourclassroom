"""Unified coverage pipeline.

Collects Cobertura XML coverage data from backend, frontend, and microservices,
enriches XMLs with cyclomatic complexity data, generates a unified HTML report
via ReportGenerator, and prints a CRAP/T1 summary.

Usage:
    python tests/coverage/report.py                  # all stacks, report only
    python tests/coverage/report.py backend          # backend only
    python tests/coverage/report.py frontend backend # multiple stacks
    python tests/coverage/report.py --run-tests      # run tests first, then report
    python tests/coverage/report.py --no-open        # skip opening browser
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import webbrowser
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
COVERAGE_DIR = ROOT / "tests" / "coverage"
REPORT_DIR = COVERAGE_DIR / "report"
RUNSETTINGS = COVERAGE_DIR / "coverage.runsettings"

STACKS = ["backend", "frontend", "microservices"]

# Where each stack's Cobertura XMLs live
XML_PATTERNS = {
    "backend": "tests/backend/**/coverage.cobertura.xml",
    "frontend": "tests/coverage/frontend/cobertura-coverage.xml",
    "microservices": "tests/coverage/microservices/coverage.xml",
}

# Commands to run tests with coverage collection
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

# Microservices source directories (mirrors [tool.coverage.run].source in pyproject.toml)
MICROSERVICES_SRC = "src/microservices/microservice"
MICROSERVICES_SOURCE_DIRS = ["api", "services", "shared", "workers"]

GENERATED_MARKERS = ["\\obj\\", "/obj/", ".g.cs", ".generated.cs", "node_modules"]

# Async state machine pattern: /<MethodName>d__N or /<<Method>b__N>d
ASYNC_STATE_MACHINE = re.compile(r"/<?<?\w+>?[bdk]__\d+>?d?$")


def find_xmls(stacks: list[str]) -> list[Path]:
    """Find all Cobertura XML files for the given stacks."""
    xmls = []
    for stack in stacks:
        pattern = XML_PATTERNS[stack]
        found = sorted(ROOT.glob(pattern))
        if found:
            xmls.extend(found)
        else:
            print(f"  [{stack}] No coverage XML found ({pattern})")
    return xmls


def clean_stale_coverage(stacks: list[str]):
    """Remove old coverage XMLs so only fresh data is used."""
    for stack in stacks:
        for xml in sorted(ROOT.glob(XML_PATTERNS[stack])):
            xml.unlink()
            print(f"  Cleaned {xml.relative_to(ROOT)}")


def clean_report_dir():
    """Delete and recreate the report directory to prevent stale files."""
    if REPORT_DIR.exists():
        shutil.rmtree(REPORT_DIR)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


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


def generate_report(xmls: list[Path]) -> bool:
    """Run ReportGenerator to produce unified HTML from Cobertura XMLs."""
    reports_arg = ";".join(str(x) for x in xmls)
    cmd = [
        "reportgenerator",
        f"-reports:{reports_arg}",
        f"-targetdir:{REPORT_DIR}",
        "-reporttypes:Html",
    ]
    print(f"\n--- Generating report ---")
    result = subprocess.run(cmd, cwd=ROOT, shell=True)
    return result.returncode == 0


# --- CC Enrichment ---


def enrich_frontend_cc():
    """Run ESLint complexity analysis and inject CC values into frontend cobertura XML."""
    xml_path = ROOT / "tests/coverage/frontend/cobertura-coverage.xml"
    if not xml_path.exists():
        return

    print("\n--- Enriching frontend CC (ESLint) ---")
    cmd = ["npx", "eslint", "--rule", "complexity: [warn, 1]", "--format", "json", "src/"]
    result = subprocess.run(
        cmd, cwd=ROOT / "src" / "frontend", shell=True,
        capture_output=True, text=True,
    )
    if result.returncode not in (0, 1):  # 1 = warnings found (expected)
        print(f"  ESLint failed (exit {result.returncode}), skipping CC enrichment")
        return

    try:
        eslint_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("  ESLint output not valid JSON, skipping CC enrichment")
        return

    # Build {normalized_path: total_cc}
    cc_by_file: dict[str, int] = {}
    cc_pattern = re.compile(r"has a complexity of (\d+)")
    for entry in eslint_data:
        filepath = entry.get("filePath", "").replace("\\", "/")
        # ESLint returns absolute paths — strip to relative from src/frontend/
        marker = "src/frontend/"
        idx = filepath.find(marker)
        if idx != -1:
            filepath = filepath[idx + len(marker):]
        total = 0
        for msg in entry.get("messages", []):
            if msg.get("ruleId") == "complexity":
                m = cc_pattern.search(msg.get("message", ""))
                if m:
                    total += int(m.group(1))
        if total > 0:
            cc_by_file[filepath] = total

    if not cc_by_file:
        print("  No complexity data found")
        return

    # Inject into XML
    tree = ET.parse(xml_path)
    enriched = 0
    for cls in tree.findall(".//class"):
        filename = cls.get("filename", "").replace("\\", "/")
        if filename in cc_by_file:
            cls.set("complexity", str(cc_by_file[filename]))
            enriched += 1

    tree.write(xml_path, xml_declaration=True)
    print(f"  Enriched {enriched} classes with CC data ({len(cc_by_file)} files from ESLint)")


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

    # Build {normalized_path: total_cc}
    cc_by_file: dict[str, int] = {}
    for filepath, functions in radon_data.items():
        normalized = filepath.replace("\\", "/")
        total = sum(f.get("complexity", 0) for f in functions)
        if total > 0:
            cc_by_file[normalized] = total

    if not cc_by_file:
        print("  No complexity data found")
        return

    # Inject into XML — match by suffix
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


# --- CRAP Analysis ---


def is_generated(filename: str, classname: str) -> bool:
    for marker in GENERATED_MARKERS:
        if marker in filename:
            return True
    if "Generated" in classname and ".<" in classname:
        return True
    return False


def normalize_class(name: str) -> str:
    """Strip async state machine suffixes to group with parent class."""
    return ASYNC_STATE_MACHINE.sub("", name)


def normalize_filename(filename: str) -> str:
    """Normalize path: forward slashes, strip leading project directory prefixes.

    Different test assemblies report the same file with different prefixes:
      - 'Hackathon.Domain\\Models\\Foo.cs'
      - 'Models\\Foo.cs'
    We normalize to just the filename portion after the last known project dir.
    """
    f = filename.replace("\\", "/")
    for prefix in ["Hackathon.Domain/", "Hackathon.Application/", "Hackathon.Infrastructure/",
                    "Hackathon.Api/", "Hackathon.ServiceDefaults/", "Hackathon.AppHost/"]:
        idx = f.find(prefix)
        if idx != -1:
            f = f[idx:]
            break
    return f


def collect_from_xml(xml_file: Path, stack: str):
    """Parse a cobertura XML, return entries grouped by normalized (class, file)."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    entries = []
    skipped = 0
    for package in root.findall(".//package"):
        for cls in package.findall(".//class"):
            name = cls.get("name", "")
            filename = cls.get("filename", "")
            if is_generated(filename, name):
                skipped += 1
                continue
            line_rate = float(cls.get("line-rate", 0))
            complexity = float(cls.get("complexity", 0))
            if complexity > 0:
                crap = (complexity ** 2) * ((1 - line_rate) ** 3) + complexity
            else:
                crap = 0
            norm_name = normalize_class(name)
            norm_file = normalize_filename(filename)
            entries.append((norm_name, norm_file, crap, complexity, line_rate, stack))
    return entries, skipped


def crap_summary(xmls: list[Path]):
    """Print CRAP/T1 summary from cobertura XMLs."""
    all_entries = []
    total_skipped = 0

    for xml_file in xmls:
        path_str = str(xml_file.relative_to(ROOT)).replace("\\", "/")
        if "backend" in path_str:
            stack = "backend"
        elif "frontend" in path_str:
            stack = "frontend"
        elif "microservices" in path_str:
            stack = "microservices"
        else:
            stack = "unknown"
        entries, skipped = collect_from_xml(xml_file, stack)
        all_entries.extend(entries)
        total_skipped += skipped

    # Group by (normalized_class, normalized_file, stack)
    groups: dict[tuple, dict] = {}
    for norm_name, norm_file, crap, cc, cov, stack in all_entries:
        key = (norm_name, norm_file, stack)
        if key not in groups:
            groups[key] = {"total_cc": 0, "max_crap": 0, "min_cov": 1.0,
                           "name": norm_name, "file": norm_file, "stack": stack}
        g = groups[key]
        g["total_cc"] = max(g["total_cc"], cc)
        g["max_crap"] = max(g["max_crap"], crap)
        g["min_cov"] = min(g["min_cov"], cov)

    results = []
    for g in groups.values():
        results.append((g["max_crap"], g["total_cc"], g["min_cov"],
                        g["name"], g["file"], g["stack"]))
    results.sort(reverse=True)

    total = len(results)
    failing = [r for r in results if r[0] > 30]

    print(f"\n=== T1 Summary ===")
    print(f"Total unique source classes: {total} (skipped {total_skipped} generated)")
    for stack in STACKS:
        stack_results = [r for r in results if r[5] == stack]
        if not stack_results:
            continue
        stack_fail = sum(1 for r in stack_results if r[0] > 30)
        stack_pass = len(stack_results) - stack_fail
        pct = stack_pass / len(stack_results) * 100
        print(f"  {stack + ':':<16} {stack_pass}/{len(stack_results)} pass ({pct:.0f}%), {stack_fail} fail")

    if failing:
        print(f"\nT1 failures (CRAP > 30):")
        print(f"{'CRAP':>8} {'CC':>5} {'Cov%':>6} {'Stack':<14} Class (file)")
        print("-" * 120)
        for crap, cc, cov, name, filename, stack in failing:
            print(f"{crap:8.1f} {cc:5.0f} {cov*100:5.1f}% {stack:<14} {name} ({filename})")
    else:
        print(f"\nAll {total} classes pass T1!")


def main():
    parser = argparse.ArgumentParser(description="Unified coverage pipeline")
    parser.add_argument(
        "stacks", nargs="*", default=STACKS,
        metavar="STACK",
        help=f"Stacks to include (default: all). Options: {', '.join(STACKS)}",
    )
    parser.add_argument(
        "--run-tests", action="store_true",
        help="Run tests with coverage collection before generating report",
    )
    parser.add_argument(
        "--no-open", action="store_true",
        help="Don't open the report in a browser",
    )
    args = parser.parse_args()

    stacks = args.stacks
    invalid = [s for s in stacks if s not in STACKS]
    if invalid:
        parser.error(f"invalid stack(s): {', '.join(invalid)}. Choose from: {', '.join(STACKS)}")
    print(f"Stacks: {', '.join(stacks)}")

    if args.run_tests:
        if not run_tests(stacks):
            print("\nSome tests failed. Generating report from available data anyway.")

        if "frontend" in stacks:
            enrich_frontend_cc()
        if "microservices" in stacks:
            enrich_microservices_cc()

    xmls = find_xmls(stacks)
    if not xmls:
        print("\nNo coverage data found. Run with --run-tests to collect coverage first.")
        sys.exit(1)

    print(f"\nFound {len(xmls)} coverage file(s):")
    for x in xmls:
        print(f"  {x.relative_to(ROOT)}")

    clean_report_dir()

    if not generate_report(xmls):
        print("\nReport generation failed.")
        sys.exit(1)

    crap_summary(xmls)

    report_index = REPORT_DIR / "index.html"
    print(f"\nReport: {report_index}")

    if not args.no_open:
        webbrowser.open(report_index.as_uri())


if __name__ == "__main__":
    main()
