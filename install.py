"""
Installation script for the Jira Agent.
This script helps install the correct dependencies and test the setup.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} failed with error: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} is not compatible. Python 3.8+ required.")
        return False

def install_dependencies():
    """Install the required dependencies."""
    print("\n📦 Installing dependencies...")
    
    # Uninstall old phi version if it exists
    print("🧹 Cleaning up old phi installation...")
    run_command("pip uninstall phi -y", "Uninstall old phi")
    
    # Install requirements
    success = run_command("pip install -r requirements.txt", "Install requirements")
    return success

def create_env_template():
    """Create a template .env file if it doesn't exist."""
    env_file = Path(".env")
    if not env_file.exists():
        print("\n📝 Creating .env template...")
        template = """# Jira Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# Azure OpenAI Configuration
azure_openai_api_version=2024-02-15-preview
azure_openai_model_name_4o_mini=your-model-name
azure_openai_4o_mini_key=your-azure-key
azure_openai_4o_mini_url=https://your-resource.openai.azure.com
azure_embedding_key_3=your-embedding-key
azure_embedding_version=2023-05-15
azure_embedding_model_3=text-embedding-3-large
"""
        with open(".env", "w") as f:
            f.write(template)
        print("✅ .env template created")
        return True
    else:
        print("✅ .env file already exists")
        return True

def test_installation():
    """Test the installation by running quick_test.py."""
    print("\n🧪 Testing installation...")
    success = run_command("python quick_test.py", "Run installation test")
    return success

def main():
    """Main installation process."""
    print("🚀 Jira Agent Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Installation failed. Please check the error messages above.")
        return
    
    # Create .env template
    if not create_env_template():
        print("\n❌ Failed to create .env template.")
        return
    
    # Test installation
    if not test_installation():
        print("\n❌ Installation test failed. Please check the error messages above.")
        return
    
    print("\n🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update the .env file with your Jira and Azure OpenAI credentials")
    print("2. Run: python quick_test.py")
    print("3. Try: python example_usage.py interactive")
    print("\n💡 For help, run: python example_usage.py interactive")

if __name__ == "__main__":
    main()
