import click
import os
import re
import datetime
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
EXPERIMENTS_DIR = BASE_DIR / "Experiments"
DOCS_DIR = BASE_DIR / "Documentation"
TEMPLATE_PATH = BASE_DIR / "Research-System" / "Templates" / "experiment_template.md"
INDEX_PATH = DOCS_DIR / "Master_Index.md"

def get_next_experiment_id():
    """Scans experiment directory to determine next ID."""
    if not EXPERIMENTS_DIR.exists():
        return "EXP-001"
    
    existing_dirs = [d.name for d in EXPERIMENTS_DIR.iterdir() if d.is_dir() and d.name.startswith("EXP-")]
    if not existing_dirs:
        return "EXP-001"
    
    ids = []
    for d in existing_dirs:
        match = re.search(r'EXP-(\d+)', d)
        if match:
            ids.append(int(match.group(1)))
    
    if not ids:
        return "EXP-001"
        
    next_id = max(ids) + 1
    return f"EXP-{next_id:03d}"

def update_master_index(exp_id, title, status, created_date):
    """Appends new experiment to the Master Index."""
    # Ensure index exists
    if not INDEX_PATH.exists():
        with open(INDEX_PATH, 'w') as f:
            f.write("# Master Research Index\n\n| ID | Title | Status | Created | Last Updated |\n|----|-------|--------|---------|--------------|\n")

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    line = f"| {exp_id} | {title} | {status} | {created_date} | {today} |\n"
    
    with open(INDEX_PATH, 'a') as f:
        f.write(line)

def update_index_status(exp_id, new_status):
    """Updates status in Master Index."""
    if not INDEX_PATH.exists():
        print("Index file not found.")
        return

    lines = []
    with open(INDEX_PATH, 'r') as f:
        lines = f.readlines()

    with open(INDEX_PATH, 'w') as f:
        for line in lines:
            if f"| {exp_id} |" in line:
                # Regex to replace the status column
                # Structure: | ID | Title | Status | Created | Last Updated |
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 6:
                    parts[3] = new_status
                    parts[5] = datetime.datetime.now().strftime("%Y-%m-%d")
                    line = f"| {parts[1]} | {parts[2]} | {parts[3]} | {parts[4]} | {parts[5]} |\n"
            f.write(line)

@click.group()
def cli():
    """FRESCO Research Management System"""
    pass

@cli.command()
@click.option('--title', prompt='Experiment Title', help='Title of the experiment')
@click.option('--objective', prompt='Objective', help='Goal of the experiment')
def new(title, objective):
    """Create a new experiment."""
    exp_id = get_next_experiment_id()
    safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)
    folder_name = f"{exp_id}_{safe_title}"
    exp_path = EXPERIMENTS_DIR / folder_name
    
    # Create directory
    exp_path.mkdir(parents=True, exist_ok=True)
    
    # Read Template
    with open(TEMPLATE_PATH, 'r') as f:
        content = f.read()
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    status = "Created"
    
    # Fill Template
    filled_content = content.format(
        experiment_id=exp_id,
        title=title,
        status=status,
        date_created=today,
        path=str(exp_path),
        objective=objective
    )
    
    # Write File
    exp_file_path = exp_path / "README.md"
    with open(exp_file_path, 'w') as f:
        f.write(filled_content)
        
    # Update Index
    update_master_index(exp_id, title, status, today)
    
    click.echo(f"Created Experiment {exp_id} at {exp_path}")

@cli.command()
@click.option('--id', prompt='Experiment ID', help='ID of experiment (e.g. EXP-001)')
@click.option('--status', type=click.Choice(['Created', 'Queued', 'Running', 'Completed', 'Failed', 'Analysis']), prompt='New Status')
def status(id, status):
    """Update experiment status."""
    # Find experiment folder
    target_file = None
    for item in EXPERIMENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(id):
            target_file = item / "README.md"
            break
            
    if not target_file or not target_file.exists():
        click.echo(f"Experiment {id} not found.")
        return

    # Update file content
    with open(target_file, 'r') as f:
        content = f.read()
        
    content = re.sub(r'\*\*Status\*\*: .*', f"**Status**: {status}", content)
    
    with open(target_file, 'w') as f:
        f.write(content)
        
    # Update Index
    update_index_status(id, status)
    
    click.echo(f"Updated {id} status to {status}")

@cli.command()
@click.option('--id', prompt='Experiment ID', help='ID of experiment (e.g. EXP-001)')
@click.option('--message', prompt='Log Message', help='Details to log')
def log(id, message):
    """Log an action or result to the experiment file."""
    # Find experiment folder
    target_file = None
    for item in EXPERIMENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(id):
            target_file = item / "README.md"
            break
            
    if not target_file or not target_file.exists():
        click.echo(f"Experiment {id} not found.")
        return

    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"| {today} | Logged | {message} |\n"
    
    lines = []
    with open(target_file, 'r') as f:
        lines = f.readlines()
        
    # Find the table and append
    # Simple heuristic: look for the header and append after the last pipe line following it
    insert_idx = -1
    in_table = False
    for i, line in enumerate(lines):
        if "| Date | Action | Result/Output |" in line:
            in_table = True
        elif in_table and line.strip().startswith("|"):
            insert_idx = i
        elif in_table and not line.strip().startswith("|"):
            in_table = False
            
    if insert_idx != -1:
        lines.insert(insert_idx + 1, log_entry)
    else:
        # Table might be empty or malformed, append to end of file if not found
        lines.append("\n## Execution Log (Appended)\n")
        lines.append("| Date | Action | Result/Output |\n")
        lines.append("|------|--------|---------------|\n")
        lines.append(log_entry)

    with open(target_file, 'w') as f:
        f.writelines(lines)
        
    click.echo(f"Logged to {id}")

if __name__ == '__main__':
    cli()
