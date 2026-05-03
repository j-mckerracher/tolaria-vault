### **Core Components of a Submission Script**

A SLURM submission script has three main parts:

1. **Shebang (Interpreter Directive)**: The first line of the script, which tells the operating system what interpreter to use to execute the script.
    
2. **SBATCH Directives**: Lines starting with `#SBATCH` that specify job requirements to SLURM.
    
3. **Job Commands**: The actual commands that will be executed when the job runs.
    

---

### **1. Shebang**

The very first line of your script should be the shebang. For a standard bash script, this will be:

```bash
#!/bin/bash
```

This ensures that your script is executed using the bash shell.

---

### **2. SBATCH Directives**

These are special comments that SLURM reads to configure your job. They should be placed at the top of your script, right after the shebang.

**Common and Important Directives:**

- **`#SBATCH --job-name=<job_name>`**: Give your job a descriptive name.
    
- **`#SBATCH --output=<filename>`**: Specify a file to which standard output should be written. You can use wildcards like `%j` to insert the job ID into the filename.
    
- **`#SBATCH --error=<filename>`**: Specify a file for standard error. It's often convenient to send both output and error to the same file.
    
- **`#SBATCH --ntasks=<n>`**: Number of tasks (processes) to launch (e.g., 1).
    
- **`#SBATCH --gpus-per-task=<n>`**: Number of GPUs per task (e.g., 1).
    
- **`#SBATCH --cpus-per-task=<n>`**: CPU cores per task (e.g., 4).
    
- **`#SBATCH --mem=<size>`**: Memory per job (e.g., 50G).
    
- **`#SBATCH --time=<HH:MM:SS>`**: The maximum wall time for your job.
    
- **`#SBATCH --partition=<partition>`**: GPU partition on Gilbreth (e.g., a30, a100-40gb, v100).
    
- **`#SBATCH --account=<your_account>`**: Your group account (find with `slist`).
    
- **`#SBATCH --qos=<qos>`**: Job QoS (e.g., standby or normal).
    

---

### **3. Job Commands**

This is the main body of your script, where you put the commands you want to execute. This section typically involves:

- **Loading Modules**: Use `module load` to load any software modules your job needs. It's good practice to start with `module purge` to ensure a clean environment.
    
- **Navigating to the Working Directory**: `cd $SLURM_SUBMIT_DIR` is a useful command to change to the directory from which you submitted the job.
    
- **Executing Your Program**: This is the main command that runs your application, for example, `python my_script.py`.
    

---

### **SLURM Environment Variables**

When your job runs, SLURM sets a number of useful environment variables that you can use in your script:

- **`$SLURM_JOBID`**: The unique ID of your job.
    
- **`$SLURM_SUBMIT_DIR`**: The directory where the `sbatch` command was run.
    
- **`$SLURM_JOB_NODELIST`**: A list of the nodes allocated to your job.
    
- **`$SLURM_SUBMIT_HOST`**: The hostname of the machine from which the job was submitted.
    

You can use these variables to make your scripts more dynamic and for logging purposes.

---

### **Complete Example Script**

Here is a template that puts all these pieces together:

```bash
#!/bin/bash

#==============================================================================
#                        SLURM SBATCH DIRECTIVES
#==============================================================================
#
#SBATCH --job-name=MyLLMJob
#SBATCH --output=my_job_%j.out
#SBATCH --error=my_job_%j.err
# Resources
#SBATCH --ntasks=1
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=50G
# Placement and policy (Gilbreth)
#SBATCH --partition=a30
#SBATCH --account=<your_account>
#SBATCH --qos=standby
#SBATCH --time=01:00:00

#==============================================================================
#                        JOB COMMANDS
#==============================================================================

# Print some useful information
echo "Job ID: $SLURM_JOBID"
echo "Running on nodes: $SLURM_JOB_NODELIST"
echo "Submitted from: $SLURM_SUBMIT_HOST"
echo "Submit directory: $SLURM_SUBMIT_DIR"

# Change to the submission directory
cd $SLURM_SUBMIT_DIR

# Load necessary modules
module purge
module load anaconda

# Activate your conda environment
conda activate my-llm-env

# Execute your Python script
python ./my_llm_application.py --input data.txt

echo "Job finished successfully."
```