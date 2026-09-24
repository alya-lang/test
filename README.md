# Alya Ecosystem CI & Integration Test Suite

[![Ecosystem CI](https://github.com/alya-lang/test/actions/workflows/ci.yml/badge.svg)](https://github.com/alya-lang/test/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/alya-lang/test?color=blue&label=License)](LICENSE)

Official multi-platform integration testing and ecosystem CI for the [Alya](https://github.com/alya-lang/alya) programming language.

This repository compiles the Alya compiler (against any branch or tag, default: `develop`), clones all 28 official Alya packages, and executes their test suites across **Linux (`ubuntu-latest`)**, **Windows (`windows-latest`)**, and **macOS (`macos-latest`)**.

---

## ⚡ Key Features

- **Multi-OS Matrix:** Verifies the full ecosystem on Linux, Windows, and macOS (Intel & Apple Silicon).
- **Flexible Compiler Branching:** Test the compiler on `develop`, `main`, or any feature branch before releasing.
- **Selective Package Testing:** Run tests for all 28 official packages or target a specific package (e.g. `json`, `http`, `crypto`, `term`, `mustache`).
- **Rich GitHub Step Summary:** Generates clear markdown reports with status tables and execution times for each package.
- **Standalone & Cross-Platform:** Single universal runner (`scripts/run_ecosystem_tests.py`) working seamlessly across Windows, Linux, and macOS without requiring a monorepo setup.

---

## 📦 Tested Ecosystem Packages

| Package | Repository | Description |
|:---|:---|:---|
| [`cache`](https://github.com/alya-lang/cache) | `alya-lang/cache` | High-performance in-memory cache with LRU eviction, TTL expiry, and statistics for Alya |
| [`cli`](https://github.com/alya-lang/cli) | `alya-lang/cli` | Modern command-line interface, argument parsing, flag handling, and subcommand router |
| [`compress`](https://github.com/alya-lang/compress) | `alya-lang/compress` | 10 compression modules + full LZ family (LZ4, LZ77, LZ78, LZJB, LZMA, LZMA2, LZSS, LZW), Huffman & ZIP archives |
| [`crypto`](https://github.com/alya-lang/crypto) | `alya-lang/crypto` | Comprehensive cryptography, hashing (SHA-2/3, BLAKE2s, Keccak, HMAC), AEAD (ChaCha20-Poly1305), KDF, and encodings |
| [`csv`](https://github.com/alya-lang/csv) | `alya-lang/csv` | RFC-4180 compliant CSV and TSV parser, serializer, and data processor |
| [`dotenv`](https://github.com/alya-lang/dotenv) | `alya-lang/dotenv` | Environment variable (.env) parser, interpolation, and configuration loader |
| [`event`](https://github.com/alya-lang/event) | `alya-lang/event` | High-throughput single-threaded reactor event loop, timers, and I/O multiplexer for Alya |
| [`gui`](https://github.com/alya-lang/gui) | `alya-lang/gui` | Native cross-platform GUI toolkit: windowing, widgets, layout, and 2D canvas for Alya |
| [`http`](https://github.com/alya-lang/http) | `alya-lang/http` | Production-ready HTTP client, server, router, compression, and middleware toolkit |
| [`i18n`](https://github.com/alya-lang/i18n) | `alya-lang/i18n` | Lightweight internationalization: locale bundles, gettext-style .tr and JSON loaders, CLDR-lite plurals |
| [`json`](https://github.com/alya-lang/json) | `alya-lang/json` | RFC 8259 JSON parser, recursive serializer, JSONPath, JSON Schema validator, NDJSON, and builder |
| [`jwt`](https://github.com/alya-lang/jwt) | `alya-lang/jwt` | Native RFC 7519 JSON Web Token library with HMAC-SHA256 and fluent builder |
| [`logger`](https://github.com/alya-lang/logger) | `alya-lang/logger` | Structured logging, leveled output, JSON format, and file rotation |
| [`mime`](https://github.com/alya-lang/mime) | `alya-lang/mime` | MIME type and media type detection library |
| [`mustache`](https://github.com/alya-lang/mustache) | `alya-lang/mustache` | Fast, zero-dependency Mustache template engine (variables, sections, partials, HTML escaping) |
| [`rand`](https://github.com/alya-lang/rand) | `alya-lang/rand` | Modern pseudo-random number generator (PRNG), statistical distributions, and sampling toolkit |
| [`regex`](https://github.com/alya-lang/regex) | `alya-lang/regex` | High-performance regular expression engine with named groups, lookarounds, and global multilingual Unicode support |
| [`semver`](https://github.com/alya-lang/semver) | `alya-lang/semver` | Semantic Versioning (SemVer 2.0.0) parser, comparator, bumper, and range checker |
| [`sqlite`](https://github.com/alya-lang/sqlite) | `alya-lang/sqlite` | Fast and lightweight SQLite3 bindings with bundled C engine (zero external dependencies) |
| [`sysinfo`](https://github.com/alya-lang/sysinfo) | `alya-lang/sysinfo` | Cross-platform system information: OS, CPU, memory, disk, host, timezone, power, process, env, load, and locale for Alya |
| [`template`](https://github.com/alya-lang/template) | `alya-lang/template` | Official template repository for all future Alya packages (GitHub Template enabled) |
| [`tensor`](https://github.com/alya-lang/tensor) | `alya-lang/tensor` | N-dimensional tensor engine with multi-dtype storage, broadcasting, and GPU acceleration (CUDA/Metal/OpenCL) |
| [`term`](https://github.com/alya-lang/term) | `alya-lang/term` | Modern terminal UI toolkit: ANSI styling, tables, callouts, trees, progress bars, charts, prompts, cursor controls |
| [`toml`](https://github.com/alya-lang/toml) | `alya-lang/toml` | TOML v1.0.0 parser, serializer, and TomlBuilder API |
| [`url`](https://github.com/alya-lang/url) | `alya-lang/url` | WHATWG and RFC 3986 compliant URL parser, serializer, normalizer, and query string library |
| [`uuid`](https://github.com/alya-lang/uuid) | `alya-lang/uuid` | RFC 4122 UUID v4, RFC 9562 UUID v7, ULID, and NanoID toolkit |
| [`uv`](https://github.com/alya-lang/uv) | `alya-lang/uv` | High-performance OS kernel I/O multiplexing (epoll, WSAPoll, kqueue) and asynchronous event engine for Alya |
| [`yaml`](https://github.com/alya-lang/yaml) | `alya-lang/yaml` | Fast, zero-dependency YAML 1.2 parser and serializer |

---

## 🚀 Running on GitHub Actions

### 1. Manual Run (`workflow_dispatch`)
Go to [Actions -> Ecosystem CI -> Run workflow](https://github.com/alya-lang/test/actions/workflows/ci.yml):

- **Compiler branch / ref**: `develop` (or any feature branch/tag)
- **Packages**: `ALL` (or comma-separated: `http,json,crypto`)
- **Run compiler tests**: `true`
- **Sequential**: `false` (set `true` to force sequential test execution)
- **Jobs**: Parallel worker count per package (e.g. `2`, `4`; default: CPU cores)

### 2. Scheduled Nightly Runs
The test suite runs automatically every night at **02:00 UTC** against the latest `develop` branch of the compiler and `main` of all packages.

---

## 💻 Running Locally

The ecosystem test suite is fully standalone and runs seamlessly across Windows, macOS, and Linux using a single cross-platform Python runner:

```bash
# 1. Run full test suite (builds compiler, runs compiler cargo tests, tests all 28 packages in parallel):
python scripts/run_ecosystem_tests.py

# 2. Test specific packages only:
python scripts/run_ecosystem_tests.py --packages "json,http,rand"

# 3. Test a custom compiler branch or tag:
python scripts/run_ecosystem_tests.py --compiler-branch my-feature-branch

# 4. Skip compiler unit tests and test packages directly:
python scripts/run_ecosystem_tests.py --skip-compiler-tests

# 5. Run tests sequentially (alya test --sequential):
python scripts/run_ecosystem_tests.py --sequential

# 6. Specify worker thread count (alya test -j 4):
python scripts/run_ecosystem_tests.py --jobs 4

# 7. Custom per-package timeout (default: 300s):
python scripts/run_ecosystem_tests.py --timeout 180
```

### ⚙️ Runner Architecture & Self-Sufficiency

- **100% Standalone & Universal:** The runner is completely self-contained. It clones the compiler (`alya-lang/alya`) and packages directly into an isolated local `workspace/` folder.
- **Custom Local Paths (Optional):** If you want to test against specific local directories, simply pass `--compiler-dir <path>` or `--packages-dir <path>`.
- **Automatic Toolchain Provisioning:** Sets `ALYA_TOOLCHAIN_AUTO_INSTALL=1` and automatically configures minimal C/Assembly build tools if no host GCC or Clang is detected in `PATH`.

### 📐 Template Compliance Checking

Verify that all official ecosystem packages follow the canonical template standard (required files, exact README headings/badges, alya.toml spec, zero hardcoded version functions, zero legacy aliases, and pure English):

```bash
# Verify compliance for all packages:
python scripts/check_template_compliance.py

# Verify compliance for specific packages:
python scripts/check_template_compliance.py --packages "json,http,rand"
```

---

## 📄 License

This test suite is open source under the [MIT License](LICENSE).