#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def setup_environment():
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))
    os.chdir(project_root)

def main():
    setup_environment()
    from src.workflows.main_workflow import main as workflow_main
    workflow_main()

if __name__ == "__main__":
    main()
