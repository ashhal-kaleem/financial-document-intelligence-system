"""Run both retrieval and answer evaluations end-to-end."""
import subprocess
import sys
from pathlib import Path

def main():
    print("Starting Financial RAG Evaluation Suite...\n")
    
    retrieval_script = Path("scripts/evaluate_retrieval.py")
    answers_script = Path("scripts/evaluate_answers.py")
    
    if not retrieval_script.exists() or not answers_script.exists():
        print("Error: Evaluation scripts not found.")
        sys.exit(1)
        
    print(f"Running {retrieval_script}...")
    try:
        subprocess.run([sys.executable, str(retrieval_script)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running retrieval evaluation: {e}")
        sys.exit(1)
        
    print(f"\nRunning {answers_script}...")
    try:
        subprocess.run([sys.executable, str(answers_script)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running answer evaluation: {e}")
        sys.exit(1)
        
    print("\nEvaluation suite completed successfully.")

if __name__ == "__main__":
    main()
