#!/usr/bin/env python3
"""
Main entry point for the Excel AI workflow processing system.
This script sets up the environment and runs the main workflow.
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Set up the Python path for the project."""
    # Get the directory containing this script (redo folder)
    project_root = Path(__file__).parent
    
    # Add project root and src to Python path
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))
    
    # Change working directory to project root
    os.chdir(project_root)

def main():
    """Main entry point."""
    setup_environment()
    
    # Import and run the main workflow
    from src.workflows.main_workflow import main as workflow_main
    workflow_main()

if __name__ == "__main__":
    main() 