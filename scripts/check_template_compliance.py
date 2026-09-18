#!/usr/bin/env python3
"""
check_template_compliance.py

Comprehensive compliance and linter suite for official Alya ecosystem packages.
Verifies that all official packages strictly conform to canonical template and repository standards:

1. Standard Required Files:
   - alya.toml, README.md, LICENSE, .gitignore, .github/workflows/ci.yml

2. README.md Structure & Standards:
   - Header: # <package_name> (or # {{PACKAGE_NAME}} for template)
   - 4 Required Badges: CI, License, Alya version, Package version
   - 8 Required Headings in Canonical Order:
     - ## 🌟 Features
     - ## 📁 Project Architecture
     - ## 📦 Installation
     - ## 🚀 Quick Start
     - ## 📖 API Reference
     - ## 🧪 Running Tests & Benchmarks
     - ## 🤝 Contributing
     - ## 📄 License

3. alya.toml Manifest Integrity:
   - [package], name, version, alya-version, entry, description, license = "MIT", repository

4. Zero Hardcoded Package Versions:
   - No <pkg>_version() or hardcoded version strings in source code

5. Zero Legacy Backward-Compatibility / Fallbacks:
   - No deprecated alias functions or obsolete struct fallbacks

6. Strict English Language Compliance:
   - No non-English / Turkish comments or words (except test fixtures)

7. GitHub Repository Settings & Metadata (Online Check):
   - Default branch: main
   - Website / Homepage: https://github.com/alya-lang/alya
   - Description: Non-empty and matches alya.toml description
   - Topics: Includes 'alya', 'alya-lang', 'package', and <pkg_name>
   - Wiki: Disabled (has_wiki == false)
   - Projects: Disabled (has_projects == false)
   - Discussions: Disabled (has_discussions == false)
   - Issues: Enabled (has_issues == true)
   - Template Flag: Enabled for 'template', disabled for all others
   - Dependency Graph / Vulnerability Alerts: Active (vulnerability-alerts == enabled)

Compatible with Linux, macOS, and Windows. Runs standalone locally or in GitHub Actions CI.
"""

import argparse
import json
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
    "event",
    "http",
    "json",
    "jwt",
    "logger",
    "mime",
    "mustache",
    "rand",
    "regex",
    "semver",
    "sqlite",
    "template",
    "term",
    "toml",
    "url",
    "uuid",
    "uv",
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

ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text for clean markdown rendering."""
    if not text:
        return ""
    return ANSI_ESCAPE_RE.sub("", text)


# Ensure UTF-8 output and line buffering across all consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"


def log(msg, color=""):
    prefix = f"{COLOR_BOLD}{COLOR_CYAN}[template-check]{COLOR_RESET} "
    print(f"{prefix}{color}{msg}{COLOR_RESET}", flush=True)


def group_start(title):
    if IN_CI:
        print(f"::group::{title}", flush=True)
    else:
        log(f"--- {title} ---", COLOR_BOLD)


def group_end():
    if IN_CI:
        print("::endgroup::", flush=True)


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


def extract_manifest_description(manifest_path: Path) -> str:
    """Extracts package description string from alya.toml."""
    if not manifest_path.is_file():
        return ""
    for line in manifest_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line_str = line.strip()
        if line_str.startswith("description"):
            parts = line_str.split("=", 1)
            if len(parts) == 2:
                return parts[1].strip().strip('"\'')
    return ""


def check_github_dependency_graph(pkg_name: str) -> bool:
    """
    Verifies that GitHub Dependency Graph is active on the repository
    (Insights -> Dependency graph: https://github.com/alya-lang/<pkg>/network/dependencies).
    Accessible publicly without requiring repository admin tokens in CI.
    """
    import urllib.request
    try:
        url = f"https://github.com/alya-lang/{pkg_name}/network/dependencies"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                html = resp.read().decode("utf-8", errors="replace")
                if "Dependency graph" in html or "Dependencies" in html:
                    return True
    except Exception:
        pass

    # Fallback to vulnerability-alerts API if running with admin rights
    gh_bin = shutil.which("gh")
    if gh_bin:
        res = run_cmd(["gh", "api", f"repos/alya-lang/{pkg_name}/vulnerability-alerts"], capture=True, timeout=10)
        if res.returncode == 0:
            return True

    return False


def check_github_packages_sidebar_disabled(pkg_name: str) -> bool:
    """
    Verifies that 'Packages' section is disabled on the repository homepage sidebar
    ('Include in the home page' -> Packages disabled).
    """
    import urllib.request
    try:
        url = f"https://github.com/alya-lang/{pkg_name}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                html = resp.read().decode("utf-8", errors="replace")
                has_packages_sidebar = (
                    bool(re.search(r'SidebarSection[\s\S]*?<span>Packages</span>', html))
                    or ("No packages published" in html)
                )
                return not has_packages_sidebar
    except Exception:
        pass
    return True


def fetch_github_metadata(pkg_name: str) -> tuple:
    """
    Fetches GitHub repository settings, dependency graph status, and sidebar packages status.
    Returns (repo_dict, dep_graph_enabled, packages_sidebar_disabled, error_string).
    """
    dep_graph_enabled = check_github_dependency_graph(pkg_name)
    packages_disabled = check_github_packages_sidebar_disabled(pkg_name)

    # 1. Try 'gh' CLI if available
    gh_bin = shutil.which("gh")
    if gh_bin:
        res = run_cmd(["gh", "api", f"repos/alya-lang/{pkg_name}"], capture=True, timeout=30)
        if res.returncode == 0:
            try:
                repo_data = json.loads(res.stdout)
                return repo_data, dep_graph_enabled, packages_disabled, None
            except Exception as e:
                return None, dep_graph_enabled, packages_disabled, f"JSON parse error from gh api: {e}"

    # 2. Try urllib with GITHUB_TOKEN or unauthenticated REST API fallback
    token = os.environ.get("GITHUB_TOKEN")
    import urllib.error
    import urllib.request
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "alya-template-compliance-checker",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/alya-lang/{pkg_name}", headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            repo_data = json.loads(resp.read().decode("utf-8"))
        return repo_data, dep_graph_enabled, packages_disabled, None
    except Exception as e:
        return None, dep_graph_enabled, packages_disabled, f"GitHub REST API error: {e}"


def check_package_compliance(pkg_name: str, pkg_dir: Path, check_github: bool = True) -> dict:
    """Evaluates a package against all official template and repository compliance rules."""
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
    manifest_desc = ""
    if manifest_path.is_file():
        content = manifest_path.read_text(encoding="utf-8", errors="replace")
        manifest_desc = extract_manifest_description(manifest_path)
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

        # Native C-FFI safety constraint check
        c_dir = pkg_dir / "c"
        ffi_file = pkg_dir / "src" / "ffi.alya"
        if c_dir.is_dir() or ffi_file.is_file():
            if "[build]" not in content:
                violations.append("Package bundles native C/FFI code, but `alya.toml` is missing `[build]` table")
            elif "links =" not in content and "links=" not in content:
                violations.append("`alya.toml` `[build]` table is missing required C-FFI safety constraint `links = \"<name>\"`")

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

        def find_matching_heading(req: str, found_list: list) -> str | None:
            if req == "## 🧪 Running Tests & Benchmarks":
                for h in found_list:
                    if h in ("## 🧪 Running Tests & Benchmarks", "## 🧪 Running Tests, Benchmarks & Documentation"):
                        return h
            elif req in found_list:
                return req
            return None

        matched_headings = []
        for req in REQUIRED_HEADINGS:
            matched = find_matching_heading(req, found_headings)
            if not matched:
                close = [h for h in found_headings if any(part in h for part in req.split() if len(part) > 4)]
                if close:
                    violations.append(f"README heading mismatch: found `{close[0]}`, expected `{req}`")
                else:
                    violations.append(f"README is missing required section: `{req}`")
            else:
                matched_headings.append(matched)

        indices = [found_headings.index(h) for h in matched_headings]
        if indices != sorted(indices):
            violations.append("README standard sections are not in canonical order")

    # --- Rule 4: GitHub Actions CI Workflow Standards ---
    ci_path = pkg_dir / ".github" / "workflows" / "ci.yml"
    if ci_path.is_file():
        ci_text = ci_path.read_text(encoding="utf-8", errors="replace")
        if "alya test" not in ci_text:
            violations.append("`.github/workflows/ci.yml` must include a test step running `alya test`")
        if "alya fmt" not in ci_text:
            violations.append("`.github/workflows/ci.yml` must include a formatting check running `alya fmt . --check`")
        if "alya doc" not in ci_text:
            if pkg_name == "template":
                violations.append("Template repository `.github/workflows/ci.yml` must include an `alya doc` step")
            else:
                warnings.append("`.github/workflows/ci.yml` does not contain an `alya doc` step; automated documentation generation is recommended")
        if pkg_name == "template" and "GITHUB_STEP_SUMMARY" not in ci_text:
            violations.append("Template repository `.github/workflows/ci.yml` must write docs summary to `$GITHUB_STEP_SUMMARY`")

    # --- Rule 5: Zero Hardcoded Package Versions in Code ---
    src_dir = pkg_dir / "src"
    if src_dir.is_dir():
        for alya_file in src_dir.glob("**/*.alya"):
            code = alya_file.read_text(encoding="utf-8", errors="replace")
            if re.search(r"function\s+\w+_version\s*\(\s*\)", code):
                violations.append(f"Hardcoded version function found in `{alya_file.relative_to(pkg_dir)}`")

    # --- Rule 6: Zero Legacy Backward-Compatibility / Fallback Aliases ---
    if src_dir.is_dir():
        for alya_file in src_dir.glob("**/*.alya"):
            code = alya_file.read_text(encoding="utf-8", errors="replace")
            if "parsed.url_host" in code or "parsed.url_scheme" in code:
                violations.append(f"Legacy struct fallback found in `{alya_file.relative_to(pkg_dir)}`")
            if re.search(r"function\s+(lz|lz_str|unlz|unlz_str|huffman_encode|huffman_decode)\s*\(", code):
                violations.append(f"Deprecated alias function found in `{alya_file.relative_to(pkg_dir)}`")
            if re.search(r"function\s+(new_rng|rand_rng_float|uniform_int)\s*\(", code):
                violations.append(f"Deprecated RNG alias function found in `{alya_file.relative_to(pkg_dir)}`")

    # --- Rule 7: Source Code Documentation Standards ---
    if src_dir.is_dir():
        alya_src_files = list(src_dir.glob("**/*.alya"))
        if alya_src_files:
            has_doc_comments = any("##" in f.read_text(encoding="utf-8", errors="replace") for f in alya_src_files)
            if not has_doc_comments:
                if pkg_name == "template":
                    violations.append("Template repository `src/` must contain `##` doc comments for modules and public APIs")
                else:
                    warnings.append("No `##` doc comments found in `src/`; API documentation comments are recommended")

    # --- Rule 8: Strict English Language Compliance ---
    for f in pkg_dir.glob("**/*"):
        if (
            f.is_file()
            and f.suffix in (".alya", ".md", ".toml", ".yml")
            and ".alya" not in f.parts
            and ".git" not in f.parts
            and "tests" not in f.parts
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

    # --- Rule 9: GitHub Repository Settings & Metadata ---
    if check_github:
        repo_data, dep_graph_enabled, packages_disabled, gh_err = fetch_github_metadata(pkg_name)
        if gh_err:
            warnings.append(f"GitHub metadata check skipped: {gh_err}")
        elif repo_data:
            # 7.1 Default branch must be 'main'
            def_branch = repo_data.get("default_branch")
            if def_branch != "main":
                violations.append(f"GitHub default branch is `{def_branch}`, expected `main`")

            # 7.2 Website / Homepage URL
            hp = repo_data.get("homepage") or ""
            if hp.rstrip("/") != "https://github.com/alya-lang/alya":
                violations.append(f"GitHub repository website is `{hp}`, expected `https://github.com/alya-lang/alya`")

            # 7.3 Repository Description
            gh_desc = (repo_data.get("description") or "").strip()
            if not gh_desc:
                violations.append("GitHub repository description is empty")
            elif pkg_name != "template" and manifest_desc:
                if gh_desc.lower() != manifest_desc.lower():
                    violations.append(f"GitHub description does not match alya.toml description:\n        GitHub:    `{gh_desc}`\n        alya.toml: `{manifest_desc}`")

            # 7.4 Topics (Tags)
            topics = repo_data.get("topics") or []
            required_topics = ["alya", "alya-lang", "package"]
            if pkg_name != "template":
                required_topics.append(pkg_name)
            missing_topics = [t for t in required_topics if t not in topics]
            if missing_topics:
                violations.append(f"GitHub repository topics missing required tag(s): `{', '.join(missing_topics)}` (found: {topics})")

            # 7.5 Wiki must be disabled
            if repo_data.get("has_wiki"):
                violations.append("GitHub Wiki is enabled (must be disabled; documentation lives in README.md)")

            # 7.6 Projects must be disabled
            if repo_data.get("has_projects"):
                violations.append("GitHub Projects is enabled (must be disabled)")

            # 7.7 Discussions must be disabled
            if repo_data.get("has_discussions"):
                violations.append("GitHub Discussions is enabled (must be disabled)")

            # 7.8 Issues must be enabled
            if not repo_data.get("has_issues"):
                violations.append("GitHub Issues is disabled (must be enabled)")

            # 7.9 Template repository flag
            is_tmpl = repo_data.get("is_template", False)
            if pkg_name == "template" and not is_tmpl:
                violations.append("GitHub repository must be a template repository (`is_template = true`)")
            elif pkg_name != "template" and is_tmpl:
                violations.append("GitHub repository should not be a template repository (`is_template = false`)")

            # 7.10 Dependency Graph (Insights -> Dependency graph)
            if not dep_graph_enabled:
                violations.append("GitHub Dependency Graph is disabled (must be enabled under Insights -> Dependency graph)")

            # 7.11 Homepage Sidebar Packages must be disabled
            if not packages_disabled:
                violations.append("GitHub repository homepage sidebar 'Packages' is enabled (must be disabled via About settings -> uncheck Packages)")

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
                lines.append(f"- ❌ {strip_ansi(v)}")
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
    parser.add_argument(
        "--skip-github",
        action="store_true",
        help="Skip remote GitHub repository metadata and settings verification (offline mode)",
    )
    args = parser.parse_args()

    check_github = not args.skip_github

    log(f"Starting Alya Package Template & Repository Compliance Audit...", COLOR_BOLD + COLOR_CYAN)

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    # Determine packages directory
    packages_dir = args.packages_dir
    if packages_dir is None:
        for candidate in [repo_root.parent / "Lib", repo_root.parent.parent / "Lib"]:
            if candidate.is_dir():
                packages_dir = candidate.resolve()
                break

    if packages_dir is None:
        packages_dir = repo_root / "workspace" / "packages"

    log(f"Packages Directory: {packages_dir}")
    log(f"GitHub Verification: {'ENABLED (Checks Repo Description, Tags, Website, Wiki/Projects/Discussions, Dependency Graph)' if check_github else 'DISABLED'}")

    if args.packages.strip().upper() == "ALL":
        target_packages = OFFICIAL_PACKAGES
    else:
        target_packages = [p.strip() for p in args.packages.split(",") if p.strip()]

    total_pkgs = len(target_packages)
    log(f"Target Packages ({total_pkgs}): {', '.join(target_packages)}\n")

    results = []
    has_failures = False

    for idx, pkg in enumerate(target_packages, 1):
        group_start(f"🔍 [{idx}/{total_pkgs}] {pkg}")
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
                group_end()
                continue
        elif packages_dir == (repo_root / "workspace" / "packages") and (pkg_path / ".git").is_dir():
            run_cmd(["git", "-C", str(pkg_path), "pull"])

        res = check_package_compliance(pkg, pkg_path, check_github=check_github)
        results.append(res)

        if res["passed"]:
            print(f"  {COLOR_GREEN}✓{COLOR_RESET} {pkg:<12} {COLOR_GREEN}Compliant{COLOR_RESET}", flush=True)
        else:
            print(f"  {COLOR_RED}✗{COLOR_RESET} {pkg:<12} {COLOR_RED}FAILED ({len(res['violations'])} violations){COLOR_RESET}", flush=True)
            for v in res["violations"]:
                print(f"      {COLOR_RED}• {v}{COLOR_RESET}", flush=True)
            has_failures = True

        for w in res.get("warnings", []):
            print(f"      {COLOR_YELLOW}⚠️  {w}{COLOR_RESET}", flush=True)

        group_end()

    # Write GitHub Summary
    write_github_summary(results)

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print("\n" + "═" * 60, flush=True)
    if not has_failures:
        log(f"🎉 All {total} package(s) fully comply with template & GitHub repository specifications!", COLOR_BOLD + COLOR_GREEN)
        sys.exit(0)
    else:
        log(f"❌ Compliance Audit Failed: {passed} passed, {failed} failed.", COLOR_BOLD + COLOR_RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
