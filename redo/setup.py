#!/usr/bin/env python3
"""
Cross-platform setup script for AI Document Processing Workflow
Automatically detects platform and sets up the environment appropriately
"""
import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def check_git():
    """Check if git is available."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        print("✅ Git is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git not found - please install Git")
        return False

def setup_virtual_environment():
    """Create and activate virtual environment."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    try:
        print("🔄 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install Python dependencies."""
    # Look for requirements.txt in current directory or parent
    req_files = ["requirements.txt", "../requirements.txt"]
    req_file = None
    
    for rf in req_files:
        if Path(rf).exists():
            req_file = rf
            break
    
    if not req_file:
        print("❌ requirements.txt not found")
        return False
    
    try:
        print(f"🔄 Installing dependencies from {req_file}...")
        
        # Get the correct pip path for the virtual environment
        system = platform.system().lower()
        if system == "windows":
            pip_cmd = ["venv\\Scripts\\python", "-m", "pip"]
        else:
            pip_cmd = ["venv/bin/python", "-m", "pip"]
        
        subprocess.run(pip_cmd + ["install", "--upgrade", "pip"], check=True)
        subprocess.run(pip_cmd + ["install", "-r", req_file], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_tesseract():
    """Check if Tesseract is installed."""
    system = platform.system().lower()
    tesseract_paths = {
        "windows": [r"C:\Program Files\Tesseract-OCR\tesseract.exe"],
        "darwin": ["/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract"],
        "linux": ["/usr/bin/tesseract", "/usr/local/bin/tesseract"]
    }
    
    paths_to_check = tesseract_paths.get(system, [])
    
    for path in paths_to_check:
        if Path(path).exists():
            print(f"✅ Tesseract found at: {path}")
            return True
    
    print("❌ Tesseract OCR not found")
    print("📋 Installation instructions:")
    if system == "windows":
        print("   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
    elif system == "darwin":
        print("   macOS: brew install tesseract")
    else:
        print("   Linux: sudo apt-get install tesseract-ocr")
    
    return False

def setup_config_files():
    """Set up configuration files from templates."""
    templates = [
        ("config.json.template", "config.json"),
        ("secrets.toml.template", "secrets.toml")
    ]
    
    for template, target in templates:
        template_path = Path(template)
        target_path = Path(target)
        
        if template_path.exists() and not target_path.exists():
            try:
                shutil.copy2(template_path, target_path)
                print(f"✅ Created {target} from template")
            except Exception as e:
                print(f"❌ Failed to create {target}: {e}")
        elif target_path.exists():
            print(f"✅ {target} already exists")
        else:
            print(f"❌ Template {template} not found")

def create_directories():
    """Create necessary directories."""
    dirs = ["output", "../input"]
    
    for directory in dirs:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {directory}")
            except Exception as e:
                print(f"❌ Failed to create {directory}: {e}")
        else:
            print(f"✅ Directory exists: {directory}")

def main():
    """Main setup function."""
    print("🚀 AI Document Processing Workflow Setup")
    print("=" * 50)
    
    success = True
    
    # Check prerequisites
    if not check_python_version():
        success = False
    
    if not check_git():
        print("   Warning: Git recommended for version control")
    
    # Setup environment
    if not setup_virtual_environment():
        success = False
    
    if not install_dependencies():
        success = False
    
    # Check external dependencies
    if not check_tesseract():
        print("   Warning: Tesseract required for MSG processing")
    
    # Setup project files
    setup_config_files()
    create_directories()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Edit secrets.toml with your API keys")
        print("2. Customize config.json if needed")
        print("3. Place files in ../input/ directory")
        print("4. Run: python main_workflow.py --mode all")
    else:
        print("❌ Setup completed with errors")
        print("   Please resolve the issues above before proceeding")
    
    return success

if __name__ == "__main__":
    main() 