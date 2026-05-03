#!/bin/bash
# update_status.sh - Updates experiment status in README and Master Index
# Usage: ./update_status.sh EXP-XXX "Status"

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Paths
EXPERIMENTS_DIR="$PROJECT_ROOT/Experiments"
INDEX_PATH="$PROJECT_ROOT/Documentation/Master_Index.md"

# Valid statuses
VALID_STATUSES="Created Queued Running Completed Failed Analysis Published"

# Arguments
EXP_ID="$1"
NEW_STATUS="$2"

if [ -z "$EXP_ID" ] || [ -z "$NEW_STATUS" ]; then
    echo "Usage: $0 EXP-XXX \"Status\""
    echo "Valid statuses: $VALID_STATUSES"
    exit 1
fi

# Validate status
if ! echo "$VALID_STATUSES" | grep -qw "$NEW_STATUS"; then
    echo "Error: Invalid status '$NEW_STATUS'"
    echo "Valid statuses: $VALID_STATUSES"
    exit 1
fi

TODAY=$(date +%Y-%m-%d)
NOW=$(date +"%Y-%m-%d %H:%M:%S")

# Find experiment directory
EXP_DIR=""
for dir in "$EXPERIMENTS_DIR"/${EXP_ID}*/; do
    if [ -d "$dir" ]; then
        EXP_DIR="$dir"
        break
    fi
done

if [ -z "$EXP_DIR" ] || [ ! -d "$EXP_DIR" ]; then
    echo "Error: Experiment $EXP_ID not found in $EXPERIMENTS_DIR"
    exit 1
fi

README_PATH="${EXP_DIR}README.md"

if [ ! -f "$README_PATH" ]; then
    echo "Error: README.md not found at $README_PATH"
    exit 1
fi

# Update status in README
sed -i "s/^\*\*Status\*\*: .*/\*\*Status\*\*: $NEW_STATUS/" "$README_PATH"

# Update Last Updated in README
sed -i "s/^\*\*Last Updated\*\*: .*/\*\*Last Updated\*\*: $TODAY/" "$README_PATH"

# Add execution log entry
# Find the execution log table and add entry after last row
if grep -q "## Execution Log" "$README_PATH"; then
    # Find line number of last table row before next section
    # This is a simplified approach - adds to end of file if table structure is unclear
    LOG_ENTRY="| $NOW | Status Update | Changed to $NEW_STATUS |"
    
    # Try to insert after the last table row in Execution Log section
    # Using awk for more reliable insertion
    awk -v entry="$LOG_ENTRY" '
        /## Execution Log/ { in_log=1 }
        in_log && /^## / && !/## Execution Log/ { 
            print entry
            in_log=0 
        }
        in_log && /^\|.*\|$/ { last_table_line=NR }
        { lines[NR]=$0 }
        END {
            for(i=1; i<=NR; i++) {
                print lines[i]
                if(i == last_table_line) print entry
            }
        }
    ' "$README_PATH" > "${README_PATH}.tmp" && mv "${README_PATH}.tmp" "$README_PATH"
fi

# Update Master Index
if [ -f "$INDEX_PATH" ]; then
    # Update the status column for this experiment
    # Format: | ID | Title | Status | Path | Created | Last Updated |
    sed -i "s/^\(| $EXP_ID |[^|]*|\)[^|]*\(|[^|]*|[^|]*|\)[^|]*|/\1 $NEW_STATUS \2 $TODAY |/" "$INDEX_PATH"
    echo "✓ Updated Master Index"
fi

echo "✓ Updated $EXP_ID status to: $NEW_STATUS"
echo "  README: $README_PATH"
