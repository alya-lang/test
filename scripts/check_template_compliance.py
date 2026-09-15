#!/usr/bin/env python3
"""
check_template_compliance.py

Comprehensive compliance and linter suite for official Alya ecosystem packages.
Verifies that all official packages strictly conform to the canonical template standards:
1. Standard required files (alya.toml, README.md, LICENSE, .gitignore, .github/workflows/ci.yml)
2. README.md structure, badge standards, and required headings in exact order:
   - ## 🌟 Features
   - ## 📁 Project Architecture
   - ## 📦 Installation
   - ## 🚀 Quick Start
   - ## 📖 API Reference
   - ## 🧪 Running Tests & Benchmarks
   - ## 🤝 Contributing
   - ## 📄 License
3. alya.toml manifest completeness (name, version, alya-version, entry, description, license, repository)
4. Zero hardcoded package version functions or constants in source code
5. Zero deprecated / legacy backward-compatibility functions or fallbacks
6. Strict English language compliance in source code, comments, and documentation

Compatible with Linux, macOS, and Windows. Runs standalone locally or in GitHub Actions CI.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Official Alya ecosystem packages
OFFICIAL_PACKAGES = [
    "cli",
    "compress",
    "crypto",
    "csv",
    "dotenv",
    "http",
    "json",
    "jwt",
    "logger",
    "mime",
    "mustache",
    "rand",
    "semver",
    "sqlite",
    "template",
    "term",
    "toml",
    "url",
    "uuid",
    "yaml",
]

REQUIRED_HEADINGS = [
    "## 🌟 Features",
    "## 📁 Project Architecture",
    "## 📦 Installation",
    "## 🚀 Quick Start",
    "## 📖 API Reference",
    "## 🧪 Running Tests & Benchmarks",
    "## 🤝 Contributing",
    "## 📄 License",
]

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_GREEN = "\033[0;32m"
COLOR_RED = "\033[0;31m"
COLOR_CYAN = "\033[0;36m"
COLOR_YELLOW = "\033[1;33m"
COLOR_GRAY = "\033[0;90m"

# Ensure UTF-8 output across all consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def log(msg, color=""):
    prefix = f"{COLOR_BOLD}{COLOR_CYAN}[template-check]{COLOR_RESET} "
    print(f"{prefix}{color}{msg}{COLOR_RESET}")


def run_cmd(cmd, cwd=None, capture=True, timeout=120):
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except Exception as e:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=-1,
            stdout="",
            stderr=str(e),
        )


def check_package_compliance(pkg_name: str, pkg_dir: Path) -> dict:
    """Evaluates a package against all official template compliance rules."""
    violations = []
    warnings = []

    # --- Rule 1: Required Files ---
    required_files = [
        "alya.toml",
        "README.md",
        "LICENSE",
        ".gitignore",
        ".github/workflows/ci.yml",
    ]
    for rf in required_files:
        p = pkg_dir / rf
        if not p.is_file():
            violations.append(f"Missing required file: `{rf}`")

    # --- Rule 2: alya.toml Manifest Integrity ---
    manifest_path = pkg_dir / "alya.toml"
    if manifest_path.is_file():
        content = manifest_path.read_text(encoding="utf-8", errors="replace")
        if "[package]" not in content:
            violations.append("`alya.toml` is missing `[package]` header")
        if f'name = "{pkg_name}"' not in content and f"name = '{pkg_name}'" not in content:
            if pkg_name != "template":
                violations.append(f"`alya.toml` package name does not match `{pkg_name}`")
        if "version =" not in content:
            violations.append("`alya.toml` is missing `version` declaration")
        if "alya-version =" not in content:
            violations.append("`alya.toml` is missing `alya-version` requirement")
        if "entry =" not in content:
            violations.append("`alya.toml` is missing `entry` path")
        if "license = \"MIT\"" not in content and "license = 'MIT'" not in content:
            violations.append("`alya.toml` license is not set to `MIT`")
        if pkg_name != "template":
            repo_expected = f"https://github.com/alya-lang/{pkg_name}"
            if repo_expected not in content:
                violations.append(f"`alya.toml` repository should point to `{repo_expected}`")

    # --- Rule 3: README.md Structure & Headings ---
    readme_path = pkg_dir / "README.md"
    if readme_path.is_file():
        readme_text = readme_path.read_text(encoding="utf-8", errors="replace")
        lines = readme_text.splitlines()

        # 3.1 Title check
        first_heading = next((l.strip() for l in lines if l.startswith("# ")), None)
        expected_title = f"# {pkg_name}" if pkg_name != "template" else "# {{PACKAGE_NAME}}"
        if first_heading != expected_title:
            violations.append(f"README title should be `{expected_title}`, found: `{first_heading}`")

        # 3.2 Badges check
        if "actions/workflows/ci.yml/badge.svg" not in readme_text:
            violations.append("README is missing GitHub Actions CI badge")
        if "github/license/alya-lang" not in readme_text:
            violations.append("README is missing License badge")
        if "package.alya-version" not in readme_text:
            violations.append("README is missing Alya compiler version badge")
        if "package.version" not in readme_text:
            violations.append("README is missing package version badge")

        # 3.3 Required Headings in Exact Order
        found_headings = [l.strip() for l in lines if l.startswith("## ")]
        
        # Check presence of each required heading
        for req in REQUIRED_HEADINGS:
            if req not in found_headings:
                # Check if slightly mismatched
                close = [h for h in found_headings if req.split()[-1] in h]
                if close:
                    violations.append(f"README heading mismatch: found `{close[0]}`, expected `{req}`")
                else:
                    violations.append(f"README is missing required section: `{req}`")

        # Verify relative ordering of the standard headings
        indices = []
        for req in REQUIRED_HEADINGS:
            if req in found_headings:
                indices.append(found_headings.index(req))
            else:
                indices.append(-1)
        
        valid_indices = [i for i in indices if i != -1]
        if valid_indices != sorted(valid_indices):
            violations.append("README standard sections are not in canonical order")

    # --- Rule 4: Zero Hardcoded Package Versions in Code ---
    src_dir = pkg_dir / "src"
    if src_dir.is_dir():
        for alya_file in src_dir.glob("**/*.alya"):
            code = alya_file.read_text(encoding="utf-8", errors="replace")
            # Prohibit <pkg>_version() functions returning package version strings
            if re.search(r"function\s+\w+_version\s*\(\s*\)", code):
                violations.append(f"Hardcoded version function found in `{alya_file.relative_to(pkg_dir)}`")

    # --- Rule 5: Zero Legacy Backward-Compatibility / Fallback Aliases ---
    if src_dir.is_dir():
        for alya_file in src_dir.glob("**/*.alya"):
            code = alya_file.read_text(encoding="utf-8", errors="replace")
            if "parsed.url_host" in code or "parsed.url_scheme" in code:
                violations.append(f"Legacy struct fallback found in `{alya_file.relative_to(pkg_dir)}`")
            if re.search(r"function\s+(lz|lz_str|unlz|unlz_str|huffman_encode|huffman_decode)\s*\(", code):
                violations.append(f"Deprecated alias function found in `{alya_file.relative_to(pkg_dir)}`")
            if re.search(r"function\s+(new_rng|rand_rng_float|uniform_int)\s*\(", code):
                violations.append(f"Deprecated RNG alias function found in `{alya_file.relative_to(pkg_dir)}`")

    # --- Rule 6: Strict English Language Compliance ---
    for f in pkg_dir.glob("**/*"):
        if (
            f.is_file()
            and f.suffix in (".alya", ".md", ".toml", ".yml")
            and ".alya" not in f.parts
            and ".git" not in f.parts
            and "tests" not in f.parts  # Allow UTF-8 unicode test fixtures in test files
        ):
            ftext = f.read_text(encoding="utf-8", errors="replace")
            turkish_matches = re.findall(
                r"\b(veya|için|dönük|uyumluluk|takma|değer|fonksiyon|özellik|kurulum)\b",
                ftext,
                re.I,
            )
            if turkish_matches:
                violations.append(
                    f"Non-English / Turkish words `{turkish_matches}` found in `{f.relative_to(pkg_dir)}`"
                )
            if "Geriye Dönük" in ftext:
                violations.append(
                    f"Turkish phrase 'Geriye Dönük' found in `{f.relative_to(pkg_dir)}`"
                )

    passed = len(violations) == 0
    return {
        "name": pkg_name,
        "path": pkg_dir,
        "passed": passed,
        "violations": violations,
        "warnings": warnings,
    }


def write_github_summary(results: list):
    """Writes detailed markdown report to GITHUB_STEP_SUMMARY if available."""
    gh_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not gh_summary:
        return

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count
    all_ok = failed_count == 0

    lines = [
        f"## {'🎉 All Official Packages Follow Template Standards' if all_ok else '❌ Package Template Compliance Violations Detected'}",
        "",
        "| Metric | Value |",
        "|:---|:---|",
        f"| **Total Packages Checked** | `{total}` |",
        f"| **Compliant Packages** | `{passed_count} / {total}` |",
        f"| **Violations Found** | `{failed_count}` |",
        "",
        "### 📋 Package Compliance Matrix",
        "",
        "| Package | Status | Violations Count | Notes |",
        "|:---|:---:|:---:|:---|",
    ]

    for r in results:
        status = "✅ **Compliant**" if r["passed"] else "❌ **VIOLATION**"
        v_count = len(r["violations"])
        note = "All rules passed" if r["passed"] else f"{v_count} issue(s)"
        lines.append(f"| [`{r['name']}`](https://github.com/alya-lang/{r['name']}) | {status} | `{v_count}` | {note} |")

    failed_results = [r for r in results if not r["passed"]]
    if failed_results:
        lines.append("\n### 🚨 Violation Breakdown\n")
        for fr in failed_results:
            lines.append(f"<details open><summary><b>Package: {fr['name']} ({len(fr['violations'])} violations)</b></summary>\n")
            for v in fr["violations"]:
                lines.append(f"- ❌ {v}")
            lines.append("\n</details>\n")

    with open(gh_summary, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Alya Ecosystem Template Compliance Linter")
    parser.add_argument(
        "--packages-dir",
        type=Path,
        default=None,
        help="Path to directory containing package folders. Defaults to workspace or auto-detection.",
    )
    parser.add_argument(
        "--packages",
        type=str,
        default="ALL",
        help="Comma-separated package names or 'ALL' (default: ALL)",
    )
    args = parser.parse_args()

    log(f"Starting Alya Package Template Compliance Audit...", COLOR_BOLD + COLOR_CYAN)

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    # Determine packages directory
    packages_dir = args.packages_dir
    if packages_dir is None:
        # Check if running adjacent to local Lib directory
        adjacent_lib = (repo_root.parent / "Lib").resolve()
        if adjacent_lib.is_dir() and (adjacent_lib / "rand" / "alya.toml").is_file():
            packages_dir = adjacent_lib
        else:
            packages_dir = repo_root / "workspace" / "packages"

    # Filter target packages
    if args.packages.strip().upper() == "ALL":
        target_packages = OFFICIAL_PACKAGES
    else:
        target_packages = [p.strip() for p in args.packages.split(",") if p.strip()]

    log(f"Packages Directory: {packages_dir}", COLOR_GRAY)
    log(f"Target Packages ({len(target_packages)}): {', '.join(target_packages)}\n")

    results = []
    has_failures = False

    for pkg in target_packages:
        pkg_path = packages_dir / pkg

        # If package is not locally available, clone it
        if not pkg_path.is_dir() or not (pkg_path / "alya.toml").is_file():
            packages_dir.mkdir(parents=True, exist_ok=True)
            clone_url = f"https://github.com/alya-lang/{pkg}.git"
            log(f"Fetching remote package {pkg} from {clone_url}...", COLOR_GRAY)
            clone_res = run_cmd(["git", "clone", "--depth", "1", clone_url, str(pkg_path)])
            if clone_res.returncode != 0:
                results.append({
                    "name": pkg,
                    "path": pkg_path,
                    "passed": False,
                    "violations": [f"Failed to clone repository: {clone_res.stderr.strip()}"],
                    "warnings": [],
                })
                has_failures = True
                continue

        res = check_package_compliance(pkg, pkg_path)
        results.append(res)

        if res["passed"]:
            print(f"  {COLOR_GREEN}✓{COLOR_RESET} {pkg:<12} {COLOR_GREEN}Compliant{COLOR_RESET}")
        else:
            print(f"  {COLOR_RED}✗{COLOR_RESET} {pkg:<12} {COLOR_RED}FAILED ({len(res['violations'])} violations){COLOR_RESET}")
            for v in res["violations"]:
                print(f"      {COLOR_RED}• {v}{COLOR_RESET}")
            has_failures = True

    # Write GitHub Summary
    write_github_summary(results)

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print("\n" + "═" * 60)
    if not has_failures:
        log(f"🎉 All {total} package(s) fully comply with template specifications!", COLOR_BOLD + COLOR_GREEN)
        sys.exit(0)
    else:
        log(f"❌ Compliance Audit Failed: {passed} passed, {failed} failed.", COLOR_BOLD + COLOR_RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
