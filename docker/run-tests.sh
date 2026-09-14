#!/usr/bin/env bash
set -e

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_BOLD='\033[1m'
COLOR_RESET='\033[0m'

TARGET_DIR="${CARGO_TARGET_DIR:-/root/target}"
ALYA_BIN="${TARGET_DIR}/quick/alyac"

build_compiler() {
    echo -e "${COLOR_CYAN}==> [1/2] Compiling Alya compiler for Linux (quick profile)...${COLOR_RESET}"
    cd /workspace/Src/alya
    cargo build --profile quick
    cp "${ALYA_BIN}" /usr/local/bin/alyac
    echo -e "${COLOR_GREEN}✓ Linux alyac ready: $(/usr/local/bin/alyac --version)${COLOR_RESET}\n"
}

run_compiler_tests() {
    echo -e "${COLOR_CYAN}====================================================${COLOR_RESET}"
    echo -e "${COLOR_CYAN}    Running Alya Compiler Test Suite (cargo test)   ${COLOR_RESET}"
    echo -e "${COLOR_CYAN}====================================================${COLOR_RESET}"
    cd /workspace/Src/alya
    
    if [ "$RUN_FMT" = "1" ]; then
        echo -e "${COLOR_YELLOW}--> Checking rustfmt...${COLOR_RESET}"
        cargo fmt --all -- --check
    fi

    if [ "$RUN_CLIPPY" = "1" ]; then
        echo -e "${COLOR_YELLOW}--> Running clippy...${COLOR_RESET}"
        cargo clippy --all-targets --all-features -- -D warnings
    fi

    cargo test
    echo -e "\n${COLOR_GREEN}✓ All Alya compiler tests passed on Linux!${COLOR_RESET}\n"
}

# Results tracking
PASSED_PKGS=()
FAILED_PKGS=()

test_single_pkg() {
    local pkg_name="$1"
    local pkg_dir="/workspace/Lib/${pkg_name}"

    if [ ! -d "${pkg_dir}" ]; then
        echo -e "${COLOR_RED}✗ Error: Package directory '${pkg_name}' not found in Lib/${COLOR_RESET}"
        FAILED_PKGS+=("${pkg_name} (Directory not found)")
        return 1
    fi

    if [ ! -f "${pkg_dir}/alya.toml" ]; then
        return 0
    fi

    echo -e "${COLOR_CYAN}----------------------------------------------------${COLOR_RESET}"
    echo -e "${COLOR_CYAN}📦 Testing Package: Lib/${pkg_name}${COLOR_RESET}"
    echo -e "${COLOR_CYAN}----------------------------------------------------${COLOR_RESET}"

    cd "${pkg_dir}"

    if [ "$RUN_FMT" = "1" ]; then
        echo "--> Checking formatting: alyac fmt . --check"
        alyac fmt . --check || true
    fi

    # Check dependencies and install if needed
    if [ -f "alya.lock" ] || grep -q '\[dependencies\]' alya.toml 2>/dev/null; then
        echo "--> Resolving dependencies: alyac install"
        alyac install || true
    fi

    echo "--> Running tests: alyac test"
    if alyac test; then
        PASSED_PKGS+=("${pkg_name}")
    else
        echo -e "${COLOR_RED}✗ Tests failed for ${pkg_name}${COLOR_RESET}"
        FAILED_PKGS+=("${pkg_name}")
    fi
}

run_package_tests() {
    echo -e "${COLOR_CYAN}====================================================${COLOR_RESET}"
    echo -e "${COLOR_CYAN}        Running Alya Packages Test Suites           ${COLOR_RESET}"
    echo -e "${COLOR_CYAN}====================================================${COLOR_RESET}"

    if [ -n "$TARGET_PKGS" ]; then
        IFS=',' read -ra PKG_ARRAY <<< "$TARGET_PKGS"
        for pkg in "${PKG_ARRAY[@]}"; do
            # Trim whitespace
            pkg="$(echo -e "${pkg}" | tr -d '[:space:]')"
            if [ -n "$pkg" ]; then
                test_single_pkg "$pkg"
            fi
        done
    else
        # Auto-discover all packages in Lib/
        for dir in /workspace/Lib/*; do
            if [ -d "$dir" ] && [ -f "$dir/alya.toml" ]; then
                pkg_name="$(basename "$dir")"
                test_single_pkg "$pkg_name"
            fi
        done
    fi
}

print_summary() {
    echo -e "\n${COLOR_BOLD}====================================================${COLOR_RESET}"
    echo -e "${COLOR_BOLD}                TEST SUMMARY (LINUX)                ${COLOR_RESET}"
    echo -e "${COLOR_BOLD}====================================================${COLOR_RESET}"

    if [ "$RUN_COMPILER" = "1" ]; then
        echo -e "  Compiler (Cargo): ${COLOR_GREEN}PASSED${COLOR_RESET}"
    fi

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
        echo -e "\n${COLOR_RED}❌ Some tests failed on Linux!${COLOR_RESET}\n"
        exit 1
    else
        echo -e "\n${COLOR_GREEN}🎉 All Linux tests completed successfully!${COLOR_RESET}\n"
        exit 0
    fi
}

# Main routing
build_compiler

if [ "$RUN_COMPILER" = "1" ]; then
    run_compiler_tests
fi

if [ "$RUN_PACKAGES" = "1" ]; then
    run_package_tests
fi

print_summary
