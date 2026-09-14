#!/usr/bin/env bash
# Alya Local Test Suite - Linux Entrypoint
# Runs package test suites on native Linux without Docker
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/scripts/run-local-tests.sh" --os linux "$@"
