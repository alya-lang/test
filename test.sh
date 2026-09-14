#!/usr/bin/env bash
# Alya Local Test Suite - Auto-detecting Unix Entrypoint (Linux / macOS)
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/scripts/run-local-tests.sh" "$@"
