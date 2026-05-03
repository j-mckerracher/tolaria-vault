#!/bin/bash
# create_experiment.sh - Creates a new experiment from template
# Usage: ./create_experiment.sh "Title" "Objective" "PATH-X"

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Paths
EXPERIMENTS_DIR="$PROJECT_ROOT/Experiments"
TEMPLATE_PATH="$PROJECT_ROOT/Research-System/Templates/experiment_template.md"
INDEX_PATH="$PROJECT_ROOT/Documentation/Master_Index.md"

# Arguments
TITLE="$1"
OBJECTIVE="$2"
RESEARCH_PATH="${3:-}"

if [ -z "$TITLE" ] || [ -z "$OBJECTIVE" ]; then
    echo "Usage: $0 \"Title\" \"Objective\" [\"PATH-X\"]"
    echo "Example: $0 \"CPU Usage Analysis\" \"Analyze CPU patterns in Anvil\" \"PATH-A\""
    exit 1
fi

# Create experiments directory if needed
mkdir -p "$EXPERIMENTS_DIR"

# Determine next experiment ID
get_next_id() {
    local max_id=0
    if [ -d "$EXPERIMENTS_DIR" ]; then
        for dir in "$EXPERIMENTS_DIR"/EXP-*/; do
            if [ -d "$dir" ]; then
                dirname=$(basename "$dir")
                num=$(echo "$dirname" | grep -oP 'EXP-\K\d+' | head -1)
                if [ -n "$num" ]; then
                    # Force base-10 parsing (avoid leading-zero octal issues, e.g., 010 -> 8)
                    num=$((10#$num))
                    if [ "$num" -gt "$max_id" ]; then
                        max_id=$num
                    fi
                fi
            fi
        done
    fi
    printf "EXP-%03d" $((max_id + 1))
}

EXP_ID=$(get_next_id)
TODAY=$(date +%Y-%m-%d)

# Create safe folder name
SAFE_TITLE=$(echo "$TITLE" | tr -cs 'a-zA-Z0-9_-' '_' | sed 's/_$//')
FOLDER_NAME="${EXP_ID}_${SAFE_TITLE}"
EXP_PATH="$EXPERIMENTS_DIR/$FOLDER_NAME"

# Create experiment directory and subdirectories
mkdir -p "$EXP_PATH/results/figures"
mkdir -p "$EXP_PATH/logs"
mkdir -p "$EXP_PATH/scripts"

# Copy and fill template
if [ -f "$TEMPLATE_PATH" ]; then
    # Escape values for sed replacement (handles /, &, |, and backslashes)
    esc_sed_repl() { printf '%s' "$1" | sed -e 's/[\\|&]/\\&/g'; }

    TITLE_ESC=$(esc_sed_repl "$TITLE")
    OBJECTIVE_ESC=$(esc_sed_repl "$OBJECTIVE")
    RESEARCH_PATH_ESC=$(esc_sed_repl "${RESEARCH_PATH:-TBD}")
    EXP_PATH_ESC=$(esc_sed_repl "$EXP_PATH")

    sed -e "s|{experiment_id}|$EXP_ID|g" \
        -e "s|{title}|$TITLE_ESC|g" \
        -e "s|{status}|Created|g" \
        -e "s|{date_created}|$TODAY|g" \
        -e "s|{date_updated}|$TODAY|g" \
        -e "s|{research_path}|$RESEARCH_PATH_ESC|g" \
        -e "s|{directory_path}|$EXP_PATH_ESC|g" \
        -e "s|{objective}|$OBJECTIVE_ESC|g" \
        "$TEMPLATE_PATH" > "$EXP_PATH/README.md"
else
    echo "Warning: Template not found at $TEMPLATE_PATH"
    cat > "$EXP_PATH/README.md" << EOF
# Experiment: $EXP_ID - $TITLE

**Status**: Created  
**Date Created**: $TODAY  
**Last Updated**: $TODAY  
**Research Path**: ${RESEARCH_PATH:-TBD}  

## Objective

$OBJECTIVE
EOF
fi

# Update Master Index
if [ -f "$INDEX_PATH" ]; then
    # Check if header exists, if not create basic structure
    if ! grep -q "^|.*ID.*|" "$INDEX_PATH"; then
        echo "" >> "$INDEX_PATH"
        echo "| ID | Title | Status | Path | Created | Last Updated |" >> "$INDEX_PATH"
        echo "|----|-------|--------|------|---------|--------------|" >> "$INDEX_PATH"
    fi
    # Add new row
    echo "| $EXP_ID | $TITLE | Created | ${RESEARCH_PATH:-TBD} | $TODAY | $TODAY |" >> "$INDEX_PATH"
else
    echo "Warning: Master Index not found at $INDEX_PATH"
fi

echo "✓ Created experiment $EXP_ID"
echo "  Location: $EXP_PATH"
echo "  README: $EXP_PATH/README.md"
echo ""
echo "Next steps:"
echo "  1. Edit README.md to fill in methodology and data specification"
echo "  2. Add experiment to Research Plan under $RESEARCH_PATH"
echo "  3. Create job script in scripts/ directory"
