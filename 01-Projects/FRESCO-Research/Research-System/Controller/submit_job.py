import sys
import random
import time

def submit_job(experiment_id, script_path):
    """
    Placeholder for job submission logic.
    In the future, this will call `sbatch` or similar.
    """
    print(f"Preparing to submit job for {experiment_id}...")
    print(f"Script: {script_path}")
    
    # Simulate submission delay
    time.sleep(1)
    
    # Generate mock Job ID
    job_id = random.randint(100000, 999999)
    print(f"Job submitted successfully. Job ID: {job_id}")
    
    return job_id

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python submit_job.py <EXP_ID> <SCRIPT_PATH>")
        sys.exit(1)
        
    exp_id = sys.argv[1]
    script = sys.argv[2]
    
    submit_job(exp_id, script)
