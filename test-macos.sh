#!/usr/bin/env bash
# Alya Local Test Suite - macOS Entrypoint
# Runs package test suites on native macOS (Apple Silicon & Intel)
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/scripts/run-local-tests.sh" --os macos "$@"
