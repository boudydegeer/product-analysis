#!/bin/bash

# archive-plan.sh - Archive completed plan documents
#
# This script moves completed plans from docs/plans/ to docs/plans/archived/
# and updates the index.md to reflect the new location.
#
# Usage:
#   ./scripts/archive-plan.sh plan1.md plan2.md
#   ./scripts/archive-plan.sh --dry-run plan1.md
#   ./scripts/archive-plan.sh -y plan1.md  (skip confirmation)

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLANS_DIR="$PROJECT_ROOT/docs/plans"
ARCHIVE_DIR="$PLANS_DIR/archived"
INDEX_FILE="$PLANS_DIR/index.md"

# Flags
DRY_RUN=false
SKIP_CONFIRMATION=false

# Arrays to track results
ARCHIVED_FILES=()
FAILED_FILES=()

#######################################
# Print colored message
# Arguments:
#   $1: Color code
#   $2: Message
#######################################
print_color() {
    echo -e "${1}${2}${NC}"
}

#######################################
# Print error message and exit
# Arguments:
#   $1: Error message
#######################################
error_exit() {
    print_color "$RED" "ERROR: $1"
    exit 1
}

#######################################
# Print usage information
#######################################
show_help() {
    cat << EOF
${GREEN}archive-plan.sh${NC} - Archive completed plan documents

${BLUE}USAGE:${NC}
    ./scripts/archive-plan.sh [OPTIONS] PLAN_FILE [PLAN_FILE...]

${BLUE}DESCRIPTION:${NC}
    Moves completed plan documents from docs/plans/ to docs/plans/archived/
    and updates the index.md to reflect the new archived location.

${BLUE}OPTIONS:${NC}
    -h, --help          Show this help message
    -y, --yes           Skip confirmation prompts
    -d, --dry-run       Show what would be done without making changes

${BLUE}EXAMPLES:${NC}
    # Archive a single plan
    ./scripts/archive-plan.sh 2026-01-07-product-analysis-platform-mvp.md

    # Archive multiple plans
    ./scripts/archive-plan.sh plan1.md plan2.md plan3.md

    # Archive with auto-confirmation
    ./scripts/archive-plan.sh -y plan1.md

    # Preview changes without archiving
    ./scripts/archive-plan.sh --dry-run plan1.md

${BLUE}NOTES:${NC}
    - Plan files must exist in docs/plans/
    - Plan files must have .md extension
    - Archived plans remain in the "Done" section with "(Archived)" notation
    - Creates docs/plans/archived/ directory if it doesn't exist

EOF
}

#######################################
# Validate prerequisites
#######################################
validate_prerequisites() {
    # Check if plans directory exists
    if [[ ! -d "$PLANS_DIR" ]]; then
        error_exit "Plans directory not found: $PLANS_DIR"
    fi

    # Check if index.md exists
    if [[ ! -f "$INDEX_FILE" ]]; then
        error_exit "Index file not found: $INDEX_FILE"
    fi

    # Check if we have write permissions
    if [[ ! -w "$PLANS_DIR" ]]; then
        error_exit "No write permission for plans directory: $PLANS_DIR"
    fi
}

#######################################
# Validate a plan file
# Arguments:
#   $1: Plan filename
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_plan_file() {
    local filename="$1"
    local filepath="$PLANS_DIR/$filename"

    # Check if filename ends with .md
    if [[ ! "$filename" =~ \.md$ ]]; then
        print_color "$RED" "  ✗ '$filename' is not a .md file"
        return 1
    fi

    # Check if file exists
    if [[ ! -f "$filepath" ]]; then
        print_color "$RED" "  ✗ File not found: $filepath"
        return 1
    fi

    # Check if already archived
    if [[ "$filename" == *"/"* ]] || [[ -f "$ARCHIVE_DIR/$filename" ]]; then
        print_color "$YELLOW" "  ⚠ '$filename' appears to be already archived"
        return 1
    fi

    return 0
}

#######################################
# Update index.md to reflect archived status
# Arguments:
#   $1: Plan filename
#######################################
update_index() {
    local filename="$1"
    local temp_file="$INDEX_FILE.tmp"

    if [[ "$DRY_RUN" == true ]]; then
        print_color "$YELLOW" "  [DRY RUN] Would update index.md for '$filename'"
        return 0
    fi

    # Create a backup
    cp "$INDEX_FILE" "$INDEX_FILE.bak"

    # Update the link path from ./filename.md to ./archived/filename.md
    # Also add (Archived) notation if not already present
    sed -e "s|\(\[.*\]\)(\./$filename)|\1(./archived/$filename)|g" \
        -e "s|\(\[.*\]\)(./archived/$filename)\([^)]*\))|\1(./archived/$filename)|g" \
        "$INDEX_FILE" > "$temp_file"

    # Now add (Archived) notation to the title if not present
    awk -v filename="$filename" '
        /^### \[.*\]\(\.\/archived\// {
            in_archived_section = 1
            line_num = NR
            # Check if line contains the filename and doesnt have (Archived)
            if (index($0, filename) > 0 && index($0, "(Archived)") == 0) {
                # Add (Archived) before the closing bracket
                sub(/\]/, " (Archived)]")
            }
            print
            next
        }
        {
            print
        }
    ' "$temp_file" > "$INDEX_FILE"

    rm -f "$temp_file"

    print_color "$GREEN" "  ✓ Updated index.md"
}

#######################################
# Archive a single plan file
# Arguments:
#   $1: Plan filename
# Returns:
#   0 if successful, 1 if failed
#######################################
archive_plan() {
    local filename="$1"
    local source_path="$PLANS_DIR/$filename"
    local dest_path="$ARCHIVE_DIR/$filename"

    print_color "$BLUE" "\nArchiving: $filename"

    # Validate file
    if ! validate_plan_file "$filename"; then
        return 1
    fi

    # Create archive directory if needed
    if [[ ! -d "$ARCHIVE_DIR" ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            print_color "$YELLOW" "  [DRY RUN] Would create directory: $ARCHIVE_DIR"
        else
            mkdir -p "$ARCHIVE_DIR"
            print_color "$GREEN" "  ✓ Created archive directory"
        fi
    fi

    # Check if destination already exists
    if [[ -f "$dest_path" ]]; then
        print_color "$YELLOW" "  ⚠ File already exists in archive: $dest_path"
        if [[ "$SKIP_CONFIRMATION" == false ]] && [[ "$DRY_RUN" == false ]]; then
            read -p "  Overwrite? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_color "$YELLOW" "  Skipped."
                return 1
            fi
        fi
    fi

    # Move the file
    if [[ "$DRY_RUN" == true ]]; then
        print_color "$YELLOW" "  [DRY RUN] Would move:"
        print_color "$YELLOW" "    FROM: $source_path"
        print_color "$YELLOW" "    TO:   $dest_path"
    else
        mv "$source_path" "$dest_path"
        print_color "$GREEN" "  ✓ Moved file to archive"
    fi

    # Update index.md
    update_index "$filename"

    print_color "$GREEN" "  ✓ Successfully archived '$filename'"
    return 0
}

#######################################
# Main function
#######################################
main() {
    local files_to_archive=()

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -y|--yes)
                SKIP_CONFIRMATION=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -*)
                error_exit "Unknown option: $1\nUse --help for usage information."
                ;;
            *)
                files_to_archive+=("$1")
                shift
                ;;
        esac
    done

    # Check if any files were provided
    if [[ ${#files_to_archive[@]} -eq 0 ]]; then
        error_exit "No plan files specified.\nUse --help for usage information."
    fi

    # Validate prerequisites
    validate_prerequisites

    # Print header
    print_color "$BLUE" "========================================="
    print_color "$BLUE" "  Archive Plan Documents"
    print_color "$BLUE" "========================================="

    if [[ "$DRY_RUN" == true ]]; then
        print_color "$YELLOW" "\n⚠ DRY RUN MODE - No changes will be made\n"
    fi

    # Show summary
    print_color "$BLUE" "\nPlans to archive: ${#files_to_archive[@]}"
    for file in "${files_to_archive[@]}"; do
        echo "  - $file"
    done

    # Confirmation
    if [[ "$SKIP_CONFIRMATION" == false ]] && [[ "$DRY_RUN" == false ]]; then
        echo
        read -p "$(print_color $YELLOW 'Proceed with archiving? (y/N): ')" -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_color "$YELLOW" "Aborted."
            exit 0
        fi
    fi

    # Process each file
    for file in "${files_to_archive[@]}"; do
        if archive_plan "$file"; then
            ARCHIVED_FILES+=("$file")
        else
            FAILED_FILES+=("$file")
        fi
    done

    # Print summary
    print_color "$BLUE" "\n========================================="
    print_color "$BLUE" "  Summary"
    print_color "$BLUE" "========================================="

    if [[ ${#ARCHIVED_FILES[@]} -gt 0 ]]; then
        print_color "$GREEN" "\n✓ Successfully archived (${#ARCHIVED_FILES[@]}):"
        for file in "${ARCHIVED_FILES[@]}"; do
            echo "  - $file"
        done
    fi

    if [[ ${#FAILED_FILES[@]} -gt 0 ]]; then
        print_color "$RED" "\n✗ Failed to archive (${#FAILED_FILES[@]}):"
        for file in "${FAILED_FILES[@]}"; do
            echo "  - $file"
        done
    fi

    if [[ "$DRY_RUN" == false ]] && [[ ${#ARCHIVED_FILES[@]} -gt 0 ]]; then
        print_color "$BLUE" "\nArchived files location:"
        print_color "$BLUE" "  $ARCHIVE_DIR"
        print_color "$YELLOW" "\nNote: A backup of index.md was created at:"
        print_color "$YELLOW" "  $INDEX_FILE.bak"
    fi

    echo

    # Exit with error if any files failed
    if [[ ${#FAILED_FILES[@]} -gt 0 ]]; then
        exit 1
    fi
}

# Run main function
main "$@"
