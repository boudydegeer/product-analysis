#!/usr/bin/env bash

#═══════════════════════════════════════════════════════════════════════════════
# Plan Status Verification Script
#═══════════════════════════════════════════════════════════════════════════════
# Verifies docs/plans/index.md consistency with actual project state
#
# Features:
#   - Auto-fixes obvious issues (statistics, dates, formatting)
#   - Reports issues requiring human decision (stale plans, missing files)
#   - Colored output with summary report
#   - Multiple modes: auto-fix (default), dry-run, report-only
#═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Color codes
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly RESET='\033[0m'

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INDEX_FILE="$PROJECT_ROOT/docs/plans/index.md"
PLANS_DIR="$PROJECT_ROOT/docs/plans"
ARCHIVED_DIR="$PLANS_DIR/archived"

# Counters
checks_passed=0
fixes_made=0
warnings=0
errors=0

# Modes
DRY_RUN=false
REPORT_ONLY=false
VERBOSE=false

# Temp files
INDEX_BACKUP=""
TEMP_INDEX=""

#═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
#═══════════════════════════════════════════════════════════════════════════════

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         Plan Status Verification                           ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
}

print_summary() {
    echo ""
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║ Summary                                                    ║"
    echo "╠════════════════════════════════════════════════════════════╣"
    printf "║ %-54s ║\n" "Checks passed:   $checks_passed"
    printf "║ %-54s ║\n" "Auto-fixes made: $fixes_made"
    printf "║ %-54s ║\n" "Warnings:        $warnings"
    printf "║ %-54s ║\n" "Errors:          $errors"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
}

log_pass() {
    echo -e "${GREEN}[✓]${RESET} $1"
    ((checks_passed++))
}

log_fix() {
    echo -e "${BLUE}[🔧]${RESET} Fixed: $1"
    ((fixes_made++))
}

log_warning() {
    echo -e "${YELLOW}[⚠]${RESET} Warning: $1"
    ((warnings++))
}

log_error() {
    echo -e "${RED}[✗]${RESET} Error: $1"
    ((errors++))
}

log_info() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${CYAN}[ℹ]${RESET} $1"
    fi
}

log_suggestion() {
    echo -e "    ${CYAN}→${RESET} Suggestion: $1"
}

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Verify that docs/plans/index.md is consistent with the actual state of the project.

OPTIONS:
    --dry-run       Show what would be fixed without making changes
    --report-only   Report issues only, no auto-fixes
    --verbose, -v   Show detailed output
    --help, -h      Show this help message

MODES:
    Default:        Auto-fix mode (fixes statistics, dates, formatting)
    --dry-run:      Shows what would be fixed
    --report-only:  Only reports issues, no fixes

EXIT CODES:
    0: All checks passed
    1: Warnings found (no errors)
    2: Errors found

EXAMPLES:
    # Run full verification with auto-fixes
    ./scripts/verify-plan-status.sh

    # Report only, no fixes
    ./scripts/verify-plan-status.sh --report-only

    # Verbose output
    ./scripts/verify-plan-status.sh --verbose

    # Dry-run (show what would be fixed)
    ./scripts/verify-plan-status.sh --dry-run

EOF
}

#═══════════════════════════════════════════════════════════════════════════════
# Cleanup Function
#═══════════════════════════════════════════════════════════════════════════════

cleanup() {
    if [[ -n "$INDEX_BACKUP" && -f "$INDEX_BACKUP" ]]; then
        rm -f "$INDEX_BACKUP"
    fi
    if [[ -n "$TEMP_INDEX" && -f "$TEMP_INDEX" ]]; then
        rm -f "$TEMP_INDEX"
    fi
}

trap cleanup EXIT

#═══════════════════════════════════════════════════════════════════════════════
# Validation Functions
#═══════════════════════════════════════════════════════════════════════════════

check_prerequisites() {
    log_info "Checking prerequisites..."

    if [[ ! -d "$PROJECT_ROOT/.git" ]]; then
        log_error "Not a git repository: $PROJECT_ROOT"
        return 1
    fi

    if [[ ! -f "$INDEX_FILE" ]]; then
        log_error "Index file not found: $INDEX_FILE"
        return 1
    fi

    if [[ ! -d "$PLANS_DIR" ]]; then
        log_error "Plans directory not found: $PLANS_DIR"
        return 1
    fi

    log_pass "Prerequisites OK"
    return 0
}

extract_plan_references() {
    # Extract plan file references from index.md
    # Format: ### [Plan Name](./path/to/plan.md)
    grep -Eo '\]\(\./[^)]+\.md\)' "$INDEX_FILE" | sed 's/](\.\///;s/)//' || true
}

extract_status_from_index() {
    local plan_file="$1"
    # Extract status line for a plan: **Status:** 🟡 In Progress
    grep -A 2 "\](\.\/$plan_file)" "$INDEX_FILE" | grep "^\*\*Status:\*\*" | sed 's/\*\*Status:\*\* //' || true
}

get_actual_plan_files() {
    # Get all .md files in plans directory (excluding index.md and archived)
    find "$PLANS_DIR" -maxdepth 1 -type f -name "*.md" ! -name "index.md" -exec basename {} \; | sort
}

get_archived_plan_files() {
    if [[ -d "$ARCHIVED_DIR" ]]; then
        find "$ARCHIVED_DIR" -maxdepth 1 -type f -name "*.md" -exec basename {} \; | sort
    fi
}

check_last_updated_date() {
    log_info "Checking Last Updated date..."

    local current_date
    current_date=$(date +%Y-%m-%d)

    local index_date
    index_date=$(grep "^\*\*Last Updated:\*\*" "$INDEX_FILE" | sed 's/\*\*Last Updated:\*\* //' || echo "")

    if [[ -z "$index_date" ]]; then
        log_error "Last Updated date not found in index.md"
        return 1
    fi

    if [[ "$index_date" != "$current_date" ]]; then
        if [[ "$REPORT_ONLY" == false ]]; then
            if [[ "$DRY_RUN" == true ]]; then
                log_fix "Would update Last Updated date (was $index_date, would be $current_date)"
            else
                # Create backup
                INDEX_BACKUP=$(mktemp)
                cp "$INDEX_FILE" "$INDEX_BACKUP"

                # Update date
                sed -i.bak "s/^\*\*Last Updated:\*\* .*$/\*\*Last Updated:\*\* $current_date/" "$INDEX_FILE"
                rm -f "${INDEX_FILE}.bak"

                log_fix "Updated Last Updated date (was $index_date, now $current_date)"
            fi
        else
            log_warning "Last Updated date is outdated (is $index_date, should be $current_date)"
        fi
    else
        log_pass "Last Updated date is current"
    fi
}

check_statistics() {
    log_info "Checking statistics..."

    # Count plans by status
    local done_count=0
    local review_count=0
    local progress_count=0
    local backlog_count=0

    # Count from sections
    # Done section: between "## ✅ Done" and next "##"
    done_count=$(awk '/^## ✅ Done/,/^## [^✅]/ {if (/^### \[.*\]\(/) print}' "$INDEX_FILE" | wc -l | xargs)

    # For Review section
    review_count=$(awk '/^## 🟢 For Review/,/^## [^🟢]/ {if (/^### \[.*\]\(/) print}' "$INDEX_FILE" | wc -l | xargs)

    # In Progress section
    progress_count=$(awk '/^## 🟡 In Progress/,/^## [^🟡]/ {if (/^### \[.*\]\(/) print}' "$INDEX_FILE" | wc -l | xargs)

    # Backlog section - count main plans (not modules)
    backlog_count=$(awk '/^## 🔴 Backlog/,/^## [^🔴]/ {if (/^### \[.*\]\(/) print}' "$INDEX_FILE" | wc -l | xargs)

    local total=$((done_count + review_count + progress_count + backlog_count))

    if [[ $total -eq 0 ]]; then
        log_warning "No plans found in index.md"
        return 0
    fi

    # Calculate percentages
    local done_pct=0
    local review_pct=0
    local progress_pct=0
    local backlog_pct=0

    if [[ $total -gt 0 ]]; then
        done_pct=$(awk "BEGIN {printf \"%.0f\", ($done_count / $total) * 100}")
        review_pct=$(awk "BEGIN {printf \"%.0f\", ($review_count / $total) * 100}")
        progress_pct=$(awk "BEGIN {printf \"%.0f\", ($progress_count / $total) * 100}")
        backlog_pct=$(awk "BEGIN {printf \"%.0f\", ($backlog_count / $total) * 100}")
    fi

    log_info "Calculated statistics: Done=$done_count ($done_pct%), Review=$review_count ($review_pct%), Progress=$progress_count ($progress_pct%), Backlog=$backlog_count ($backlog_pct%)"

    # Extract current statistics from table
    local current_done current_review current_progress current_backlog
    current_done=$(grep "| ✅ Done |" "$INDEX_FILE" | awk -F'|' '{print $3}' | xargs || echo "0")
    current_review=$(grep "| 🟢 For Review |" "$INDEX_FILE" | awk -F'|' '{print $3}' | xargs || echo "0")
    current_progress=$(grep "| 🟡 In Progress |" "$INDEX_FILE" | awk -F'|' '{print $3}' | xargs || echo "0")
    current_backlog=$(grep "| 🔴 Backlog |" "$INDEX_FILE" | awk -F'|' '{print $3}' | xargs || echo "0")

    # Check for "modules" or "module" suffix in backlog
    if [[ "$current_backlog" == *"module"* ]]; then
        current_backlog=$(echo "$current_backlog" | grep -o '[0-9]*' | head -1 || echo "0")
        [[ -z "$current_backlog" ]] && current_backlog="0"
    fi

    local current_done_pct current_review_pct current_progress_pct current_backlog_pct
    current_done_pct=$(grep "| ✅ Done |" "$INDEX_FILE" | awk -F'|' '{print $4}' | xargs | sed 's/%//' || echo "0")
    current_review_pct=$(grep "| 🟢 For Review |" "$INDEX_FILE" | awk -F'|' '{print $4}' | xargs | sed 's/%//' || echo "0")
    current_progress_pct=$(grep "| 🟡 In Progress |" "$INDEX_FILE" | awk -F'|' '{print $4}' | xargs | sed 's/%//' || echo "0")
    current_backlog_pct=$(grep "| 🔴 Backlog |" "$INDEX_FILE" | awk -F'|' '{print $4}' | xargs | sed 's/%//' || echo "0")

    # Check if statistics match
    local stats_match=true
    if [[ "$done_count" != "$current_done" ]] || [[ "$done_pct" != "$current_done_pct" ]] ||
       [[ "$review_count" != "$current_review" ]] || [[ "$review_pct" != "$current_review_pct" ]] ||
       [[ "$progress_count" != "$current_progress" ]] || [[ "$progress_pct" != "$current_progress_pct" ]]; then
        stats_match=false
    fi

    if [[ "$stats_match" == false ]]; then
        if [[ "$REPORT_ONLY" == false ]]; then
            if [[ "$DRY_RUN" == true ]]; then
                log_fix "Would recalculate statistics"
                log_info "  Done: $current_done → $done_count ($current_done_pct% → $done_pct%)"
                log_info "  Review: $current_review → $review_count ($current_review_pct% → $review_pct%)"
                log_info "  Progress: $current_progress → $progress_count ($current_progress_pct% → $progress_pct%)"
                log_info "  Backlog: $current_backlog → $backlog_count ($current_backlog_pct% → $backlog_pct%)"
            else
                # Create backup if not already created
                if [[ -z "$INDEX_BACKUP" ]]; then
                    INDEX_BACKUP=$(mktemp)
                    cp "$INDEX_FILE" "$INDEX_BACKUP"
                fi

                # Update statistics table
                TEMP_INDEX=$(mktemp)
                awk -v done="$done_count" -v done_pct="$done_pct" \
                    -v review="$review_count" -v review_pct="$review_pct" \
                    -v progress="$progress_count" -v progress_pct="$progress_pct" \
                    -v backlog="$backlog_count" -v backlog_pct="$backlog_pct" '
                    /^\| ✅ Done \|/ {
                        print "| ✅ Done | " done " | " done_pct "% |"
                        next
                    }
                    /^\| 🟢 For Review \|/ {
                        print "| 🟢 For Review | " review " | " review_pct "% |"
                        next
                    }
                    /^\| 🟡 In Progress \|/ {
                        print "| 🟡 In Progress | " progress " | " progress_pct "% |"
                        next
                    }
                    /^\| 🔴 Backlog \|/ {
                        if (backlog == 1) {
                            print "| 🔴 Backlog | " backlog " module | " backlog_pct "% |"
                        } else {
                            print "| 🔴 Backlog | " backlog " modules | " backlog_pct "% |"
                        }
                        next
                    }
                    {print}
                ' "$INDEX_FILE" > "$TEMP_INDEX"

                mv "$TEMP_INDEX" "$INDEX_FILE"

                log_fix "Recalculated statistics"
            fi
        else
            log_warning "Statistics are incorrect"
            log_info "  Done: $current_done → should be $done_count ($current_done_pct% → $done_pct%)"
            log_info "  Review: $current_review → should be $review_count ($current_review_pct% → $review_pct%)"
            log_info "  Progress: $current_progress → should be $progress_count ($current_progress_pct% → $progress_pct%)"
            log_info "  Backlog: $current_backlog → should be $backlog_count ($current_backlog_pct% → $backlog_pct%)"
        fi
    else
        log_pass "Statistics are correct"
    fi
}

check_file_existence() {
    log_info "Checking plan file existence..."

    local missing_files=()
    local plan_refs
    plan_refs=$(extract_plan_references)

    if [[ -z "$plan_refs" ]]; then
        log_warning "No plan references found in index.md"
        return 0
    fi

    while IFS= read -r plan_file; do
        if [[ -n "$plan_file" ]]; then
            # Check in main plans dir
            if [[ -f "$PLANS_DIR/$plan_file" ]]; then
                continue
            fi
            # Check in archived dir
            if [[ -d "$ARCHIVED_DIR" && -f "$ARCHIVED_DIR/$plan_file" ]]; then
                continue
            fi
            missing_files+=("$plan_file")
        fi
    done <<< "$plan_refs"

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        for file in "${missing_files[@]}"; do
            log_error "Plan file referenced but not found: $file"
        done
    else
        log_pass "All referenced plan files exist"
    fi
}

check_orphaned_files() {
    log_info "Checking for orphaned plan files..."

    local orphaned=()
    local actual_files
    actual_files=$(get_actual_plan_files)

    while IFS= read -r actual_file; do
        if [[ -n "$actual_file" ]]; then
            # Check if file is referenced in index
            if ! grep -q "$actual_file" "$INDEX_FILE"; then
                orphaned+=("$actual_file")
            fi
        fi
    done <<< "$actual_files"

    if [[ ${#orphaned[@]} -gt 0 ]]; then
        for file in "${orphaned[@]}"; do
            log_warning "Plan file exists but not referenced in index.md: $file"
            log_suggestion "Add this plan to index.md or move to archived/"
        done
    else
        log_pass "No orphaned plan files found"
    fi
}

check_stale_plans() {
    log_info "Checking for stale plans..."

    local plan_refs
    plan_refs=$(extract_plan_references)

    local current_date_ts
    current_date_ts=$(date +%s)
    local thirty_days_ago=$((current_date_ts - 30*24*60*60))
    local seven_days_ago=$((current_date_ts - 7*24*60*60))

    while IFS= read -r plan_file; do
        if [[ -z "$plan_file" ]]; then
            continue
        fi

        local full_path="$PLANS_DIR/$plan_file"
        if [[ ! -f "$full_path" ]]; then
            continue
        fi

        # Get plan name
        local plan_name
        plan_name=$(grep "\](\.\/$plan_file)" "$INDEX_FILE" | sed 's/^### \[\(.*\)\](.*)/\1/' || echo "$plan_file")

        # Get status
        local status
        status=$(extract_status_from_index "$plan_file")

        # Check for "In Progress" plans without recent commits
        if [[ "$status" == *"🟡"* || "$status" == *"In Progress"* ]]; then
            # Get last commit touching this plan file
            local last_commit_ts
            last_commit_ts=$(git log -1 --format="%ct" -- "$full_path" 2>/dev/null || echo "0")

            if [[ "$last_commit_ts" != "0" && "$last_commit_ts" -lt "$seven_days_ago" ]]; then
                local days_ago=$(( (current_date_ts - last_commit_ts) / 86400 ))
                log_warning "Plan \"$plan_name\" marked In Progress but no commits in $days_ago days"
                log_suggestion "Consider updating status to Blocked, For Review, or Done"
            fi

            # Check if plan has been in progress for >30 days
            local file_date
            file_date=$(echo "$plan_file" | grep -Eo '^[0-9]{4}-[0-9]{2}-[0-9]{2}' || echo "")

            if [[ -n "$file_date" ]]; then
                local file_date_ts
                file_date_ts=$(date -j -f "%Y-%m-%d" "$file_date" +%s 2>/dev/null || echo "0")

                if [[ "$file_date_ts" != "0" && "$file_date_ts" -lt "$thirty_days_ago" ]]; then
                    local days_old=$(( (current_date_ts - file_date_ts) / 86400 ))
                    log_warning "Plan \"$plan_name\" has been In Progress for $days_old days"
                    log_suggestion "Review progress and update status or break into smaller tasks"
                fi
            fi
        fi

        # Check for "Ready" (backlog) plans that are old
        if [[ "$status" == *"🔴"* || "$status" == *"Backlog"* ]]; then
            local file_date
            file_date=$(echo "$plan_file" | grep -Eo '^[0-9]{4}-[0-9]{2}-[0-9]{2}' || echo "")

            if [[ -n "$file_date" ]]; then
                local file_date_ts
                file_date_ts=$(date -j -f "%Y-%m-%d" "$file_date" +%s 2>/dev/null || echo "0")

                if [[ "$file_date_ts" != "0" && "$file_date_ts" -lt "$thirty_days_ago" ]]; then
                    local days_old=$(( (current_date_ts - file_date_ts) / 86400 ))
                    log_warning "Plan \"$plan_name\" has been in Backlog for $days_old days"
                    log_suggestion "Start implementation or archive if no longer relevant"
                fi
            fi
        fi
    done <<< "$plan_refs"
}

check_status_consistency() {
    log_info "Checking status consistency..."

    local inconsistencies=()
    local plan_refs
    plan_refs=$(extract_plan_references)

    while IFS= read -r plan_file; do
        if [[ -z "$plan_file" ]]; then
            continue
        fi

        local plan_name
        plan_name=$(grep "\](\.\/$plan_file)" "$INDEX_FILE" | sed 's/^### \[\(.*\)\](.*)/\1/' || echo "$plan_file")

        # Get the section this plan is in
        local section
        section=$(awk -v plan="$plan_file" '
            /^## / {current_section = $0}
            $0 ~ plan {print current_section; exit}
        ' "$INDEX_FILE")

        # Get the status line
        local status
        status=$(extract_status_from_index "$plan_file")

        # Check consistency
        local mismatch=false
        if [[ "$section" == *"✅ Done"* && "$status" != *"✅"* ]]; then
            mismatch=true
        elif [[ "$section" == *"🟢 For Review"* && "$status" != *"🟢"* ]]; then
            mismatch=true
        elif [[ "$section" == *"🟡 In Progress"* && "$status" != *"🟡"* ]]; then
            mismatch=true
        elif [[ "$section" == *"🔴 Backlog"* && "$status" != *"🔴"* ]]; then
            mismatch=true
        fi

        if [[ "$mismatch" == true ]]; then
            log_warning "Status mismatch for \"$plan_name\""
            log_info "  Section: $section"
            log_info "  Status line: $status"
            log_suggestion "Move plan to correct section or update status emoji"
        fi
    done <<< "$plan_refs"

    if [[ "$mismatch" != true ]]; then
        log_pass "All plan statuses are consistent with their sections"
    fi
}

#═══════════════════════════════════════════════════════════════════════════════
# Main Function
#═══════════════════════════════════════════════════════════════════════════════

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --report-only)
                REPORT_ONLY=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 2
                ;;
        esac
    done

    print_header

    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${YELLOW}Running in DRY-RUN mode (no changes will be made)${RESET}\n"
    elif [[ "$REPORT_ONLY" == true ]]; then
        echo -e "${YELLOW}Running in REPORT-ONLY mode (no auto-fixes)${RESET}\n"
    fi

    # Run checks
    if ! check_prerequisites; then
        print_summary
        exit 2
    fi

    check_last_updated_date || true
    check_statistics || true
    check_file_existence || true
    check_orphaned_files || true
    check_stale_plans || true
    check_status_consistency || true

    # Print summary
    print_summary

    # Determine exit code
    if [[ $errors -gt 0 ]]; then
        exit 2
    elif [[ $warnings -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"
