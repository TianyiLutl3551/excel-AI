#!/usr/bin/env python3
"""
One-click setup script for AI Document Processing Workflow
Run this after downloading from GitHub: python setup.py
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def print_header():
    """Print setup header"""
    print("🚀 AI Document Processing Workflow - Setup")
    print("=" * 50)
    print("Setting up your environment automatically...")
    print("")

def create_directories():
    """Create necessary directories"""
    dirs = [
        "data/input",
        "data/output", 
        "log"
    ]
    
    print("📁 Creating directories...")
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {dir_path}")
    
    # Create .gitkeep files to preserve empty folders
    gitkeep_files = [
        "data/input/.gitkeep",
        "data/output/.gitkeep",
        "log/.gitkeep"
    ]
    
    for gitkeep in gitkeep_files:
        Path(gitkeep).touch()
    
    print("   ✅ Added .gitkeep files to preserve folder structure")

def setup_virtual_environment():
    """Create and setup virtual environment"""
    print("\n🐍 Setting up Python virtual environment...")
    
    if not Path("venv").exists():
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("   ✅ Virtual environment created")
        except subprocess.CalledProcessError:
            print("   ❌ Failed to create virtual environment")
            return False
    else:
        print("   ✅ Virtual environment already exists")
    
    # Get pip command based on OS
    if platform.system() == "Windows":
        pip_cmd = str(Path("venv/Scripts/pip.exe"))
        activate_cmd = "venv\\Scripts\\activate"
    else:
        pip_cmd = str(Path("venv/bin/pip"))
        activate_cmd = "source venv/bin/activate"
    
    print(f"   💡 To activate later: {activate_cmd}")
    
    # Install requirements
    print("\n📦 Installing dependencies...")
    if Path("requirements.txt").exists():
        try:
            subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
            subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
            print("   ✅ All dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Some packages failed to install. Error: {e}")
            print("   💡 You may need to run manually: pip install -r requirements.txt")
            return False
    else:
        print("   ❌ requirements.txt not found")
        return False

def setup_config():
    """Setup configuration files"""
    print("\n⚙️  Setting up configuration files...")
    
    # Setup config.json
    config_template = Path("config/config.json.template")
    config_file = Path("config/config.json")
    
    if not config_file.exists():
        if config_template.exists():
            shutil.copy(config_template, config_file)
            print("   ✅ config.json created from template")
        else:
            print("   ⚠️  config.json.template not found")
    else:
        print("   ✅ config.json already exists")
    
    # Setup secrets.toml
    secrets_template = Path("config/secrets.toml.template")
    secrets_file = Path("config/secrets.toml")
    
    if not secrets_file.exists():
        if secrets_template.exists():
            shutil.copy(secrets_template, secrets_file)
            print("   ✅ secrets.toml created from template")
            print("   ⚠️  IMPORTANT: You must edit config/secrets.toml with your API keys!")
        else:
            print("   ⚠️  secrets.toml.template not found")
    else:
        print("   ✅ secrets.toml already exists")

def check_tesseract():
    """Check if Tesseract is installed"""
    print("\n🔍 Checking Tesseract OCR installation...")
    
    tesseract_paths = {
        "Windows": [
            "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            "C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe"
        ],
        "Darwin": [
            "/opt/homebrew/bin/tesseract",
            "/usr/local/bin/tesseract"
        ],
        "Linux": [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract"
        ]
    }
    
    system = platform.system()
    found = False
    
    # Check common paths
    if system in tesseract_paths:
        for path in tesseract_paths[system]:
            if Path(path).exists():
                print(f"   ✅ Tesseract found at: {path}")
                found = True
                break
    
    # Check if tesseract is in PATH
    if not found:
        try:
            result = subprocess.run(["tesseract", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Tesseract found in system PATH")
                found = True
        except FileNotFoundError:
            pass
    
    if not found:
        print("   ⚠️  Tesseract OCR not found. Please install it:")
        if system == "Windows":
            print("      📥 Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        elif system == "Darwin":
            print("      🍺 Run: brew install tesseract")
        else:
            print("      📦 Run: sudo apt-get install tesseract-ocr")
        return False
    
    return True

def check_api_keys():
    """Check if API keys are configured"""
    print("\n🔑 Checking API key configuration...")
    
    secrets_file = Path("config/secrets.toml")
    if secrets_file.exists():
        content = secrets_file.read_text()
        
        # Check for placeholder values
        if "YOUR_OPENAI_API_KEY_HERE" in content:
            print("   ⚠️  OpenAI API key not configured")
            return False
        elif "YOUR_AZURE_ENDPOINT_HERE" in content or "YOUR_AZURE_KEY_HERE" in content:
            print("   ⚠️  Azure API credentials not configured")
            return False
        else:
            print("   ✅ API keys appear to be configured")
            return True
    else:
        print("   ❌ secrets.toml not found")
        return False

def print_next_steps(api_keys_configured, tesseract_found):
    """Print next steps for the user"""
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    
    print("\n📋 Next steps:")
    
    if not api_keys_configured:
        print("1. ⚠️  REQUIRED: Edit config/secrets.toml with your API keys:")
        print("   - OpenAI API key (get from: https://platform.openai.com/api-keys)")
        print("   - Azure Document Intelligence endpoint and key")
    
    if not tesseract_found:
        print("2. ⚠️  REQUIRED: Install Tesseract OCR (see instructions above)")
    
    print("3. 📁 Put your input files (.msg, .xlsx) in: data/input/")
    print("4. 🚀 Run the workflow:")
    print("   python main.py --mode all")
    
    print("\n💡 Additional commands:")
    print("   python main.py --mode range 20240501 20240501  # Process specific date")
    print("   python concat_tables.py                         # Combine table results")
    print("   python concat_highlights.py                     # Combine highlights")
    
    print("\n✨ You're ready to process documents!")

def main():
    """Main setup function"""
    print_header()
    
    # Run setup steps
    create_directories()
    venv_success = setup_virtual_environment()
    setup_config()
    tesseract_found = check_tesseract()
    api_keys_configured = check_api_keys()
    
    # Print results
    print_next_steps(api_keys_configured, tesseract_found)
    
    # Final status
    if venv_success and tesseract_found and api_keys_configured:
        print("\n🎯 Status: READY TO RUN! 🚀")
    else:
        print("\n⚠️  Status: Please complete the steps above before running")

if __name__ == "__main__":
    main() 