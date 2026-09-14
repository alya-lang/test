# Alya Ecosystem CI & Integration Test Suite

[![Ecosystem CI](https://github.com/alya-lang/test/actions/workflows/ci.yml/badge.svg)](https://github.com/alya-lang/test/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/alya-lang/test?color=blue&label=License)](LICENSE)

Official multi-platform integration testing and ecosystem CI for the [Alya](https://github.com/alya-lang/alya) programming language.

This repository compiles the Alya compiler (against any branch or tag, default: `develop`), clones all 16 official Alya packages, and executes their test suites across **Linux (`ubuntu-latest`)**, **Windows (`windows-latest`)**, and **macOS (`macos-latest`)**.

---

## ⚡ Key Features

- **Multi-OS Matrix:** Verifies the full ecosystem on Linux, Windows, and macOS (Intel & Apple Silicon).
- **Flexible Compiler Branching:** Test the compiler on `develop`, `main`, or any feature branch before releasing.
- **Selective Package Testing:** Run tests for all 16 official packages or target a specific package (e.g. `json`, `http`, `crypto`).
- **Rich GitHub Step Summary:** Generates clear markdown reports with status tables and execution times for each package.
- **Standalone & Cross-Platform:** Single universal runner (`scripts/run_ecosystem_tests.py`) working seamlessly across Windows, Linux, and macOS without requiring a monorepo setup.

---

## 📦 Tested Ecosystem Packages

| Package | Repository | Description |
|:---|:---|:---|
| [`cli`](https://github.com/alya-lang/cli) | `alya-lang/cli` | Command-line interface, argument parsing, flag handling |
| [`crypto`](https://github.com/alya-lang/crypto) | `alya-lang/crypto` | Cryptography and hashing library |
| [`csv`](https://github.com/alya-lang/csv) | `alya-lang/csv` | RFC 4180 CSV and TSV parser/serializer |
| [`dotenv`](https://github.com/alya-lang/dotenv) | `alya-lang/dotenv` | Environment variable loader and interpolator |
| [`http`](https://github.com/alya-lang/http) | `alya-lang/http` | HTTP client, server, router, and middleware toolkit |
| [`json`](https://github.com/alya-lang/json) | `alya-lang/json` | RFC 8259 JSON parser, serializer, builder, and JSONPath |
| [`jwt`](https://github.com/alya-lang/jwt) | `alya-lang/jwt` | JSON Web Token (RFC 7519) library |
| [`logger`](https://github.com/alya-lang/logger) | `alya-lang/logger` | Leveled structured logging, rotation, and formats |
| [`mime`](https://github.com/alya-lang/mime) | `alya-lang/mime` | MIME and media type detection |
| [`rand`](https://github.com/alya-lang/rand) | `alya-lang/rand` | PRNG, UUID v4/v7, ULID, and sampling toolkit |
| [`semver`](https://github.com/alya-lang/semver) | `alya-lang/semver` | Semantic Versioning (SemVer 2.0.0) parser and checker |
| [`sqlite`](https://github.com/alya-lang/sqlite) | `alya-lang/sqlite` | SQLite3 bindings with bundled C engine |
| [`template`](https://github.com/alya-lang/template) | `alya-lang/template` | Standard package scaffold template |
| [`toml`](https://github.com/alya-lang/toml) | `alya-lang/toml` | TOML v1.0.0 parser and serializer |
| [`url`](https://github.com/alya-lang/url) | `alya-lang/url` | WHATWG & RFC 3986 compliant URL parser and builder |
| [`uuid`](https://github.com/alya-lang/uuid) | `alya-lang/uuid` | RFC 4122 / RFC 9562 UUID generator and validator |

---

## 🚀 Running on GitHub Actions

### 1. Manual Run (`workflow_dispatch`)
Go to [Actions -> Ecosystem CI -> Run workflow](https://github.com/alya-lang/test/actions/workflows/ci.yml):

- **Compiler branch / ref**: `develop` (or any feature branch/tag)
- **Packages**: `ALL` (or comma-separated: `http,json,crypto`)
- **Run compiler tests**: `true`

### 2. Scheduled Nightly Runs
The test suite runs automatically every night at **02:00 UTC** against the latest `develop` branch of the compiler and `main` of all packages.

---

## 💻 Running Locally

The ecosystem test suite is fully standalone and runs seamlessly across Windows, macOS, and Linux using a single cross-platform Python runner:

```bash
# 1. Run full test suite (builds compiler, runs compiler cargo tests, tests all 16 packages):
python scripts/run_ecosystem_tests.py

# 2. Test specific packages only:
python scripts/run_ecosystem_tests.py --packages "json,http,rand"

# 3. Test a custom compiler branch or tag:
python scripts/run_ecosystem_tests.py --compiler-branch my-feature-branch

# 4. Skip compiler unit tests and test packages directly:
python scripts/run_ecosystem_tests.py --skip-compiler-tests

# 5. Fast iteration with specific packages:
python scripts/run_ecosystem_tests.py --packages "uuid,semver" --skip-compiler-tests
```

### ⚙️ Runner Architecture & Self-Sufficiency

- **Standalone Mode (Clean Clone):** Anyone cloning this repository in isolation can run the test suite immediately. The runner automatically clones `alya-lang/alya` and the required package repositories into a local `workspace/` directory.
- **Local Workspace Optimization:** When run inside the full Alya workspace (where `Src/alya` and `Lib/` exist), the runner automatically detects them and tests against your local working tree for instant iteration.
- **Automatic Toolchain Provisioning:** Exports `ALYA_TOOLCHAIN_AUTO_INSTALL=1` and dynamically provisions minimal C/Assembly build tools if no host GCC or Clang compiler is detected in `PATH`.

---

## 📄 License

This test suite is open source under the [MIT License](LICENSE).
