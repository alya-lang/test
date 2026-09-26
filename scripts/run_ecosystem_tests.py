#!/usr/bin/env python3
"""
run_ecosystem_tests.py

Comprehensive cross-platform test runner for the Alya language ecosystem.
Tests the Alya compiler (custom branch/ref) against all official Alya packages.

Compatible with Linux, macOS (Intel & Apple Silicon), and Windows.
Runs seamlessly both locally and inside GitHub Actions CI.
"""

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

# Official Alya ecosystem packages
OFFICIAL_PACKAGES = [
    "cache",
    "cli",
    "compress",
    "crypto",
    "csv",
    "dotenv",
    "event",
    "gui",
    "http",
    "i18n",
    "json",
    "jwt",
    "logger",
    "mime",
    "mustache",
    "rand",
    "regex",
    "semver",
    "sqlite",
    "sysinfo",
    "template",
    "tensor",
    "term",
    "tls",
    "toml",
    "url",
    "uuid",
    "uv",
    "xml",
    "yaml",
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
    prefix = f"{COLOR_BOLD}{COLOR_CYAN}[alya-test]{COLOR_RESET} "
    print(f"{prefix}{color}{msg}{COLOR_RESET}", flush=True)


def group_start(title):
    if IN_CI:
        print(f"::group::{title}", flush=True)
    else:
        log(f"--- {title} ---", COLOR_BOLD)


def group_end():
    if IN_CI:
        print("::endgroup::", flush=True)


def run_cmd(cmd, cwd=None, env=None, check=False, capture=False, stream=False, timeout=None):
    """Run a command with proper error logging, optional streaming or capture, and timeout."""
    exec_env = os.environ.copy()
    if env:
        exec_env.update(env)

    if stream:
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=exec_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except Exception as e:
            cmd_str = " ".join(str(c) for c in cmd)
            log(f"Failed to execute command '{cmd_str}': {e}", COLOR_RED)
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=-1,
                stdout=str(e),
                stderr="",
            )

        output_lines = []

        def reader():
            try:
                for line in iter(proc.stdout.readline, ""):
                    output_lines.append(line)
                    print(line, end="", flush=True)
            finally:
                proc.stdout.close()

        t = threading.Thread(target=reader, daemon=True)
        t.start()

        try:
            returncode = proc.wait(timeout=timeout)
            t.join(timeout=5)
            full_output = "".join(output_lines)
            res = subprocess.CompletedProcess(
                args=cmd,
                returncode=returncode,
                stdout=full_output,
                stderr="",
            )
        except subprocess.TimeoutExpired:
            proc.kill()
            t.join(timeout=2)
            cmd_str = " ".join(str(c) for c in cmd)
            log(f"Command timed out after {timeout}s: {cmd_str}", COLOR_RED)
            full_output = "".join(output_lines) + f"\n[ERROR] Command timed out after {timeout} seconds.\n"
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=-1,
                stdout=full_output,
                stderr="",
            )

        if check and res.returncode != 0:
            raise subprocess.CalledProcessError(res.returncode, cmd)
        return res

    try:
        if capture:
            res = subprocess.run(
                cmd,
                cwd=cwd,
                env=exec_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        else:
            res = subprocess.run(
                cmd,
                cwd=cwd,
                env=exec_env,
                timeout=timeout,
            )
    except subprocess.TimeoutExpired as e:
        cmd_str = " ".join(str(c) for c in cmd)
        log(f"Command timed out after {timeout}s: {cmd_str}", COLOR_RED)
        stdout = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode("utf-8", errors="replace") if e.stdout else "")
        stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode("utf-8", errors="replace") if e.stderr else "")
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=-1,
            stdout=(stdout or "") + f"\n[ERROR] Command timed out after {timeout} seconds.\n",
            stderr=(stderr or ""),
        )

    if check and res.returncode != 0:
        raise subprocess.CalledProcessError(res.returncode, cmd)
    return res


def clone_with_retry(cmd, cwd=None, retries=3, delay=2):
    """Executes git clone with retries on transient network errors."""
    for attempt in range(1, retries + 1):
        res = run_cmd(cmd, cwd=cwd, capture=True, timeout=180)
        if res.returncode == 0:
            return True
        if attempt < retries:
            log(f"Git clone attempt {attempt}/{retries} failed, retrying in {delay}s...", COLOR_YELLOW)
            time.sleep(delay)
    return False


def build_compiler(compiler_dir, profile="quick"):
    """Builds the Alya compiler using cargo and returns path to alya binary."""
    group_start("🔨 Building Alya Compiler")
    log(f"Building Alya compiler in {compiler_dir} (profile: {profile})...", COLOR_CYAN)
    
    cargo_cmd = ["cargo", "build", f"--profile={profile}"]
    res = run_cmd(cargo_cmd, cwd=compiler_dir, stream=True)
    if res.returncode != 0:
        log("Cargo build failed!", COLOR_RED)
        group_end()
        sys.exit(1)

    # Locate binary
    ext = ".exe" if sys.platform == "win32" else ""
    bin_name = f"alya{ext}"
    bin_path = compiler_dir / "target" / profile / bin_name
    
    if not bin_path.is_file():
        # Try release directory fallback
        bin_path = compiler_dir / "target" / "release" / bin_name

    if not bin_path.is_file():
        # Try debug directory fallback
        bin_path = compiler_dir / "target" / "debug" / bin_name

    if not bin_path.is_file():
        log(f"Compiler executable not found at: {bin_path}", COLOR_RED)
        group_end()
        sys.exit(1)

    log(f"Compiler ready: {bin_path}", COLOR_GREEN)
    
    # Add directory to PATH
    bin_dir = str(bin_path.parent.resolve())
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    
    # Export to GITHUB_PATH if running in GitHub Actions
    gh_path = os.environ.get("GITHUB_PATH")
    if gh_path and Path(gh_path).is_file():
        with open(gh_path, "a", encoding="utf-8") as f:
            f.write(f"{bin_dir}\n")

    # Verify version
    ver_res = run_cmd(["alya", "--version"], capture=True)
    version_str = ver_res.stdout.strip() if ver_res.returncode == 0 else "unknown"
    log(f"Installed alya version: {version_str}", COLOR_GREEN)
    
    # Ensure toolchain auto-installation is enabled for headless/CI test environments
    os.environ["ALYA_TOOLCHAIN_AUTO_INSTALL"] = "1"

    # Log active toolchain status
    tc_res = run_cmd(["alya", "toolchain", "status"], capture=True)
    if tc_res.returncode == 0:
        log(f"Active Toolchain:\n{tc_res.stdout.strip()}", COLOR_GRAY)

    group_end()
    return bin_path, version_str


def run_compiler_tests(compiler_dir):
    """Runs compiler test suite with cargo test."""
    group_start("🦀 Compiler Internal Tests (cargo test)")
    log("Running compiler test suite (cargo test)...", COLOR_CYAN)
    start = time.time()
    res = run_cmd(["cargo", "test"], cwd=compiler_dir, stream=True)
    duration = time.time() - start
    passed = (res.returncode == 0)
    
    if passed:
        log(f"Compiler tests passed ({duration:.1f}s)", COLOR_GREEN)
    else:
        log(f"Compiler tests FAILED ({duration:.1f}s)", COLOR_RED)
    group_end()
        
    return {
        "name": "alya (cargo test)",
        "passed": passed,
        "duration": duration,
        "output": res.stdout,
    }


def test_package(pkg_name, pkg_dir, sequential=False, jobs=None, timeout=300):
    """Runs fmt, install, and test on a single Alya package."""
    log(f"Testing Package: Lib/{pkg_name}...", COLOR_CYAN)
    start = time.time()
    
    # 1. Format check (timeout 60s)
    fmt_res = run_cmd(["alya", "fmt", ".", "--check"], cwd=pkg_dir, capture=True, timeout=60)
    if fmt_res.returncode != 0:
        log(f"  Notice: 'alya fmt' detected formatting differences", COLOR_YELLOW)

    # 2. Lint check (timeout 60s)
    lint_res = run_cmd(["alya", "lint", ".", "--check"], cwd=pkg_dir, capture=True, timeout=60)
    if lint_res.returncode != 0:
        log(f"  Notice: 'alya lint' detected issues", COLOR_YELLOW)
    
    # 2. Dependency install if needed (timeout 120s)
    if (pkg_dir / "alya.lock").is_file() or (pkg_dir / "alya.toml").is_file():
        log(f"  Checking dependencies ('alya install')...", COLOR_GRAY)
        install_res = run_cmd(["alya", "install"], cwd=pkg_dir, capture=True, timeout=120)
        if install_res.returncode != 0:
            log(f"  Notice: 'alya install' returned code {install_res.returncode}", COLOR_YELLOW)

    # 3. Documentation generation check (timeout 60s)
    doc_check_dir = pkg_dir / ".doc_check"
    doc_res = run_cmd(["alya", "doc", ".", "-o", ".doc_check", "--markdown"], cwd=pkg_dir, capture=True, timeout=60)
    if doc_check_dir.is_dir():
        shutil.rmtree(doc_check_dir, ignore_errors=True)
    if doc_res.returncode != 0:
        log(f"  Notice: 'alya doc' returned code {doc_res.returncode}", COLOR_YELLOW)

    # 4. Run test suite
    test_cmd = ["alya", "test"]
    if sequential:
        test_cmd.append("--sequential")
    elif jobs:
        test_cmd.extend(["-j", str(jobs)])

    log(f"  Running: {' '.join(test_cmd)}", COLOR_GRAY)
    test_res = run_cmd(test_cmd, cwd=pkg_dir, stream=True, timeout=timeout)
    duration = time.time() - start
    passed = (test_res.returncode == 0)

    if passed:
        log(f"  ✓ {pkg_name} passed ({duration:.2f}s)", COLOR_GREEN)
    else:
        log(f"  ✗ {pkg_name} FAILED ({duration:.2f}s)", COLOR_RED)

    return {
        "name": pkg_name,
        "passed": passed,
        "duration": duration,
        "fmt_ok": (fmt_res.returncode == 0),
        "lint_ok": (lint_res.returncode == 0),
        "doc_ok": (doc_res.returncode == 0),
        "output": test_res.stdout,
    }


def write_github_summary(os_name, arch_name, compiler_ver, compiler_branch, comp_res, pkg_results, suite_duration=0.0):
    """Writes detailed markdown summary to $GITHUB_STEP_SUMMARY."""
    gh_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not gh_summary:
        return

    total = len(pkg_results)
    passed_count = sum(1 for r in pkg_results if r["passed"])
    failed_count = total - passed_count
    all_ok = (failed_count == 0) and (comp_res is None or comp_res["passed"])

    lines = [
        f"## {'🎉 Ecosystem Integration Tests Passed' if all_ok else '❌ Ecosystem Integration Tests Failed'}",
        "",
        "| Metric | Value |",
        "|:---|:---|",
        f"| **OS** | `{os_name}` (`{arch_name}`) |",
        f"| **Alya Compiler** | `{compiler_ver}` (branch: `{compiler_branch}`) |",
        f"| **Total Run Duration** | `{suite_duration:.1f}s` |",
        f"| **Total Packages** | `{total}` |",
        f"| **Passed Packages** | `{passed_count} / {total}` |",
        f"| **Failed Packages** | `{failed_count}` |",
        "",
    ]

    if comp_res:
        status_icon = "✅ Passed" if comp_res["passed"] else "❌ Failed"
        lines.append(f"### 🦀 Compiler Internal Tests (`cargo test`): {status_icon} (`{comp_res['duration']:.1f}s`)")
        if not comp_res["passed"]:
            clean_comp_output = strip_ansi(comp_res["output"]).strip()
            lines.append(f"<details><summary>Compiler Test Failure Log</summary>\n\n```text\n{clean_comp_output}\n```\n</details>\n")

    lines.append("### 📦 Package Results")
    lines.append("")
    lines.append("| Package | Status | Duration | Format Check | Lint Check | Doc Check |")
    lines.append("|:---|:---:|:---:|:---:|:---:|:---:|")

    for r in pkg_results:
        icon = "✅ Passed" if r["passed"] else "❌ **FAILED**"
        fmt_icon = "✓" if r.get("fmt_ok", True) else "⚠️"
        lint_icon = "✓" if r.get("lint_ok", True) else "⚠️"
        doc_icon = "✓" if r.get("doc_ok", True) else "⚠️"
        lines.append(f"| [`{r['name']}`](https://github.com/alya-lang/{r['name']}) | {icon} | `{r['duration']:.2f}s` | {fmt_icon} | {lint_icon} | {doc_icon} |")

    # Add failure logs if any
    failed_pkgs = [r for r in pkg_results if not r["passed"]]
    if failed_pkgs:
        lines.append("\n### 🚨 Failure Details")
        for fp in failed_pkgs:
            clean_pkg_output = strip_ansi(fp["output"]).strip()
            lines.append(f"<details><summary><b>Failure output for {fp['name']}</b></summary>\n\n```text\n{clean_pkg_output}\n```\n</details>\n")

    with open(gh_summary, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Alya Ecosystem CI Test Runner")
    parser.add_argument(
        "--compiler-dir",
        type=Path,
        default=None,
        help="Path to pre-existing compiler repo. If omitted, cloned automatically.",
    )
    parser.add_argument(
        "--compiler-repo",
        type=str,
        default="https://github.com/alya-lang/alya.git",
        help="Git repository URL for Alya compiler (default: alya-lang/alya)",
    )
    parser.add_argument(
        "--compiler-branch",
        type=str,
        default="develop",
        help="Git branch or tag for Alya compiler (default: develop)",
    )
    parser.add_argument(
        "--packages",
        type=str,
        default="ALL",
        help="Comma-separated packages to test, or 'ALL' (default: ALL)",
    )
    parser.add_argument(
        "--packages-dir",
        type=Path,
        default=None,
        help="Path to local packages folder. If omitted, cloned automatically.",
    )
    parser.add_argument(
        "--skip-compiler-tests",
        action="store_true",
        help="Skip running cargo test on the compiler itself.",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run package test suites sequentially (alya test --sequential).",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        help="Number of parallel worker jobs for package tests (default: CPU cores).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for each package test run (default: 300).",
    )
    parser.add_argument(
        "--workspace-dir",
        type=Path,
        default=Path("workspace"),
        help="Directory to store cloned repos (default: ./workspace)",
    )

    args = parser.parse_args()
    suite_start = time.time()
    
    os_name = platform.system()
    arch_name = platform.machine()
    log(f"Running Alya Ecosystem Tests on {os_name} ({arch_name})", COLOR_BOLD)

    workspace = args.workspace_dir.resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    # 1. Resolve Compiler
    compiler_dir = args.compiler_dir
    if not compiler_dir:
        compiler_dir = workspace / "alya-compiler"
        if not compiler_dir.is_dir():
            log(f"Cloning compiler from {args.compiler_repo} (branch: {args.compiler_branch})...", COLOR_CYAN)
            clone_success = clone_with_retry([
                "git", "clone",
                "--depth", "1",
                "--branch", args.compiler_branch,
                args.compiler_repo,
                str(compiler_dir),
            ])
            if not clone_success:
                log(f"Failed to clone compiler repo after retries: {args.compiler_repo}", COLOR_RED)
                sys.exit(1)

    # 2. Build Compiler
    _, compiler_version = build_compiler(compiler_dir, profile="quick")

    # 3. Run Compiler Tests
    comp_res = None
    if not args.skip_compiler_tests:
        comp_res = run_compiler_tests(compiler_dir)

    # 4. Resolve Packages
    if args.packages.strip().upper() == "ALL":
        target_pkgs = OFFICIAL_PACKAGES
    else:
        target_pkgs = [p.strip() for p in args.packages.split(",") if p.strip()]

    total_pkgs = len(target_pkgs)
    log(f"Target packages to test ({total_pkgs}): {', '.join(target_pkgs)}", COLOR_CYAN)

    pkg_results = []
    packages_base = args.packages_dir

    for idx, pkg_name in enumerate(target_pkgs, 1):
        group_start(f"📦 [{idx}/{total_pkgs}] Lib/{pkg_name}")
        log(f"[{idx}/{total_pkgs}] Preparing Package: Lib/{pkg_name}...", COLOR_BOLD)
        pkg_dir = None
        if packages_base and (packages_base / pkg_name).is_dir():
            pkg_dir = packages_base / pkg_name
        else:
            pkg_dir = workspace / "packages" / pkg_name
            if not pkg_dir.is_dir():
                pkg_repo = f"https://github.com/alya-lang/{pkg_name}.git"
                log(f"  Cloning {pkg_name} from {pkg_repo} (branch: main)...", COLOR_GRAY)
                clone_success = clone_with_retry([
                    "git", "clone",
                    "--depth", "1",
                    "--branch", "main",
                    pkg_repo,
                    str(pkg_dir),
                ])
                if not clone_success:
                    log(f"  Failed to clone {pkg_name}!", COLOR_RED)

        if not pkg_dir.is_dir():
            log(f"Warning: Package directory {pkg_dir} could not be resolved. Skipping.", COLOR_YELLOW)
            group_end()
            continue

        res = test_package(
            pkg_name,
            pkg_dir,
            sequential=args.sequential,
            jobs=args.jobs,
            timeout=args.timeout,
        )
        pkg_results.append(res)
        group_end()

    # 5. Print Terminal Summary Table
    suite_duration = time.time() - suite_start
    print("\n" + "=" * 60, flush=True)
    print(f"{COLOR_BOLD}                 ECOSYSTEM TEST SUMMARY{COLOR_RESET}", flush=True)
    print("=" * 60, flush=True)
    print(f"  Platform:         {os_name} ({arch_name})", flush=True)
    print(f"  Compiler Version: {compiler_version}", flush=True)
    print(f"  Compiler Branch:  {args.compiler_branch}", flush=True)
    print(f"  Total Duration:   {suite_duration:.1f}s", flush=True)
    print("-" * 60, flush=True)

    if comp_res:
        comp_status = f"{COLOR_GREEN}PASSED{COLOR_RESET}" if comp_res["passed"] else f"{COLOR_RED}FAILED{COLOR_RESET}"
        print(f"  Compiler Test:    {comp_status} ({comp_res['duration']:.1f}s)", flush=True)

    passed_pkgs = [r for r in pkg_results if r["passed"]]
    failed_pkgs = [r for r in pkg_results if not r["passed"]]

    print(f"\n  Passed Packages ({len(passed_pkgs)}/{len(pkg_results)}):", flush=True)
    for r in passed_pkgs:
        print(f"    {COLOR_GREEN}✓{COLOR_RESET} {r['name']:<15} ({r['duration']:.2f}s)", flush=True)

    if failed_pkgs:
        print(f"\n  {COLOR_RED}Failed Packages ({len(failed_pkgs)}/{len(pkg_results)}):{COLOR_RESET}", flush=True)
        for r in failed_pkgs:
            print(f"    {COLOR_RED}✗{COLOR_RESET} {r['name']:<15} ({r['duration']:.2f}s)", flush=True)

    print("=" * 60 + "\n", flush=True)

    # 6. Output to GitHub Summary
    write_github_summary(
        os_name=os_name,
        arch_name=arch_name,
        compiler_ver=compiler_version,
        compiler_branch=args.compiler_branch,
        comp_res=comp_res,
        pkg_results=pkg_results,
        suite_duration=suite_duration,
    )

    # 7. Exit Code
    all_passed = (len(failed_pkgs) == 0) and (comp_res is None or comp_res["passed"])
    if not all_passed:
        log("Ecosystem tests finished with failures.", COLOR_RED)
        sys.exit(1)
    else:
        log("All ecosystem tests completed successfully!", COLOR_GREEN)
        sys.exit(0)


if __name__ == "__main__":
    main()
