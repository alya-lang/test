#!/usr/bin/env bash
# Alya Local Test Suite for Linux & macOS
set -eo pipefail

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_BOLD='\033[1m'
COLOR_RESET='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LIB_DIR="${ROOT_DIR}/Lib"

# Default options
TARGET_OS=""
TARGET_PKGS=""
CHECK_FMT=0
RUN_COMPILER=0

print_usage() {
    echo -e "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --pkg <names>     Test specific packages (comma-separated, e.g. 'json,http')"
    echo "  -f, --fmt             Check formatting with 'alyac fmt . --check'"
    echo "  -c, --compiler        Also run compiler unit tests ('cargo test')"
    echo "      --os <os>         Target OS label ('linux' or 'macos', defaults to uname)"
    echo "  -h, --help            Show this help message"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--pkg|--package|--packages)
            TARGET_PKGS="$2"
            shift 2
            ;;
        -f|--fmt)
            CHECK_FMT=1
            shift
            ;;
        -c|--compiler)
            RUN_COMPILER=1
            shift
            ;;
        --os)
            TARGET_OS="$2"
            shift 2
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${COLOR_RED}Unknown option: $1${COLOR_RESET}"
            print_usage
            exit 1
            ;;
    esac
done

# Detect OS if not specified
if [ -z "$TARGET_OS" ]; then
    UNAME_S="$(uname -s)"
    case "$UNAME_S" in
        Darwin*) TARGET_OS="macos" ;;
        Linux*)  TARGET_OS="linux" ;;
        *)       TARGET_OS="unix" ;;
    esac
fi

OS_LABEL="$(echo "$TARGET_OS" | tr '[:lower:]' '[:upper:]')"
ARCH_NAME="$(uname -m)"

echo -e "${COLOR_BOLD}${COLOR_CYAN}====================================================${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_CYAN}       ALYA LOCAL TEST RUNNER (${OS_LABEL} - ${ARCH_NAME})    ${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_CYAN}====================================================${COLOR_RESET}"

# Find or verify alyac compiler
if ! command -v alyac &> /dev/null; then
    # Check if built in local workspace (../Src/alya)
    SRC_DIR="${ROOT_DIR}/Src/alya"
    LOCAL_ALYAC=""
    for candidate in \
        "${SRC_DIR}/target/quick/alyac" \
        "${SRC_DIR}/target/release/alyac" \
        "${SRC_DIR}/target/debug/alyac"; do
        if [ -f "$candidate" ]; then
            LOCAL_ALYAC="$candidate"
            break
        fi
    done

    if [ -n "$LOCAL_ALYAC" ]; then
        export PATH="$(dirname "$LOCAL_ALYAC"):$PATH"
        echo -e "${COLOR_YELLOW}Using local workspace compiler: ${LOCAL_ALYAC}${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}Error: 'alyac' is not in PATH.${COLOR_RESET}"
        echo -e "Please install it or build it first:"
        echo -e "  cd Src/alya && cargo build --profile quick && export PATH=\"\$(pwd)/target/quick:\$PATH\""
        exit 1
    fi
fi

ALYAC_VER="$(alyac --version 2>&1 || true)"
echo -e "${COLOR_GREEN}✓ Compiler: ${ALYAC_VER}${COLOR_RESET}\n"

# Run compiler tests if requested
if [ "$RUN_COMPILER" = "1" ]; then
    SRC_DIR="${ROOT_DIR}/Src/alya"
    if [ -d "$SRC_DIR" ]; then
        echo -e "${COLOR_CYAN}==> Running Compiler Tests in ${SRC_DIR}...${COLOR_RESET}"
        (cd "$SRC_DIR" && cargo test)
        echo -e "${COLOR_GREEN}✓ Compiler tests passed!${COLOR_RESET}\n"
    else
        echo -e "${COLOR_YELLOW}Warning: Compiler source directory not found at ${SRC_DIR}${COLOR_RESET}"
    fi
fi

# Locate packages directory
if [ ! -d "$LIB_DIR" ]; then
    if [ -d "${SCRIPT_DIR}/packages" ]; then
        LIB_DIR="${SCRIPT_DIR}/packages"
    else
        echo -e "${COLOR_RED}Error: Packages directory not found (checked ${LIB_DIR} and ${SCRIPT_DIR}/packages).${COLOR_RESET}"
        echo -e "To clone and test all packages, run:"
        echo -e "  python3 scripts/run_ecosystem_tests.py"
        exit 1
    fi
fi

PASSED_PKGS=()
FAILED_PKGS=()

test_package() {
    local pkg_dir="$1"
    local pkg_name="$(basename "$pkg_dir")"
    local manifest="${pkg_dir}/alya.toml"

    if [ ! -f "$manifest" ]; then
        return
    fi

    echo -e "${COLOR_CYAN}----------------------------------------------------${COLOR_RESET}"
    echo -e "${COLOR_CYAN}📦 Testing Package: Lib/${pkg_name} (${OS_LABEL})${COLOR_RESET}"
    echo -e "${COLOR_CYAN}----------------------------------------------------${COLOR_RESET}"

    pushd "$pkg_dir" > /dev/null
    local pkg_failed=0

    if [ "$CHECK_FMT" = "1" ]; then
        echo -e "${COLOR_YELLOW}--> Checking format: alyac fmt . --check${COLOR_RESET}"
        if ! alyac fmt . --check; then
            pkg_failed=1
        fi
    fi

    if [ "$pkg_failed" -eq 0 ]; then
        if [ -f "alya.lock" ] || grep -q '\[dependencies\]' alya.toml 2>/dev/null; then
            echo "--> Resolving dependencies: alyac install"
            alyac install || true
        fi

        echo "--> Running tests: alyac test"
        if alyac test; then
            PASSED_PKGS+=("$pkg_name")
        else
            pkg_failed=1
            FAILED_PKGS+=("$pkg_name")
        fi
    else
        FAILED_PKGS+=("$pkg_name")
    fi

    popd > /dev/null
}

if [ -n "$TARGET_PKGS" ]; then
    IFS=',' read -ra PKG_ARRAY <<< "$TARGET_PKGS"
    for p in "${PKG_ARRAY[@]}"; do
        p="$(echo "$p" | tr -d '[:space:]')"
        target="${LIB_DIR}/${p}"
        if [ -d "$target" ]; then
            test_package "$target"
        else
            echo -e "${COLOR_YELLOW}Warning: Package '${p}' not found in ${LIB_DIR}${COLOR_RESET}"
        fi
    done
else
    for dir in "${LIB_DIR}"/*; do
        if [ -d "$dir" ]; then
            test_package "$dir"
        fi
    done
fi

echo -e "\n${COLOR_BOLD}${COLOR_CYAN}====================================================${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_CYAN}             TEST SUMMARY (${OS_LABEL})            ${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_CYAN}====================================================${COLOR_RESET}"

if [ ${#PASSED_PKGS[@]} -gt 0 ]; then
    echo -e "\n  ${COLOR_GREEN}Passed Packages (${#PASSED_PKGS[@]}):${COLOR_RESET}"
    for p in "${PASSED_PKGS[@]}"; do
        echo -e "    ${COLOR_GREEN}✓${COLOR_RESET} $p"
    done
fi

if [ ${#FAILED_PKGS[@]} -gt 0 ]; then
    echo -e "\n  ${COLOR_RED}Failed Packages (${#FAILED_PKGS[@]}):${COLOR_RESET}"
    for p in "${FAILED_PKGS[@]}"; do
        echo -e "    ${COLOR_RED}✗${COLOR_RESET} $p"
    done
    echo -e "\n${COLOR_RED}❌ Some package tests failed on ${OS_LABEL}.${COLOR_RESET}\n"
    exit 1
else
    echo -e "\n${COLOR_GREEN}🎉 All ${OS_LABEL} package tests passed successfully!${COLOR_RESET}\n"
    exit 0
fi
