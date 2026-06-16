#!/usr/bin/env python
"""
BusinessPilot AI - System Requirements & Environment Validator
Checks dependencies, directory structures, environment variables, and local configurations.
"""
import os
import sys
import tempfile
import importlib.util
from dotenv import load_dotenv

# Load environment
load_dotenv()

def print_header(title):
    print("=" * 60)
    print(f" {title:^58}")
    print("=" * 60)

def print_result(check_name, status, message=""):
    color_code = "\033[92m" if status == "PASS" else "\033[93m" if status == "WARN" else "\033[91m"
    reset_code = "\033[0m"
    print(f"[{color_code}{status}{reset_code}] {check_name:<30} - {message}")

def check_python_version():
    major, minor = sys.version_info.major, sys.version_info.minor
    if major == 3 and minor >= 10:
        print_result("Python Version", "PASS", f"Running Python {major}.{minor}.{sys.version_info.micro}")
        return True
    else:
        print_result("Python Version", "FAIL", f"Required: Python >= 3.10, Current: {major}.{minor}")
        return False

def check_dependencies():
    required_packages = [
        ("streamlit", "streamlit"),
        ("fpdf", "fpdf2"),
        ("pandas", "pandas"),
        ("plotly", "plotly"),
        ("google.genai", "google-genai"),
        ("mcp", "mcp"),
        ("dotenv", "python-dotenv"),
        ("pytest", "pytest")
    ]
    all_ok = True
    for module_name, pip_name in required_packages:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            print_result(f"Package: {pip_name}", "PASS", "Installed")
        else:
            print_result(f"Package: {pip_name}", "FAIL", "Missing from python environment")
            all_ok = False
    return all_ok

def check_directory_structure():
    required_dirs = [
        "data/uploads",
        "data/history",
        "data/reports",
        "logs",
        "agents",
        "orchestrator",
        "mcp_servers",
        "config"
    ]
    all_ok = True
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)
        # Check write permissions
        temp_file_path = os.path.join(directory, ".permissions_check.tmp")
        try:
            with open(temp_file_path, "w") as f:
                f.write("test")
            os.remove(temp_file_path)
            print_result(f"Directory: {directory}", "PASS", "Exists & Writable")
        except Exception as e:
            print_result(f"Directory: {directory}", "FAIL", f"Cannot write to path: {str(e)}")
            all_ok = False
    return all_ok

def check_api_keys():
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        masked_key = gemini_key[:4] + "*" * (len(gemini_key) - 8) + gemini_key[-4:] if len(gemini_key) > 8 else "****"
        print_result("Gemini API Configuration", "PASS", f"Configured ({masked_key})")
    else:
        print_result("Gemini API Configuration", "WARN", "GEMINI_API_KEY missing from environment. running in simulator mock mode.")

def check_smtp_config():
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_user = os.getenv("SMTP_USER")
    if smtp_server and smtp_user:
        print_result("SMTP Email Notification", "PASS", f"Configured for server: {smtp_server}")
    else:
        print_result("SMTP Email Notification", "WARN", "SMTP variables not set in .env. Falling back to stdout simulation alerts.")

def main():
    print_header("BusinessPilot AI Configuration Validation")
    
    python_ok = check_python_version()
    print()
    
    print("--- Checking Installed Python Dependencies ---")
    packages_ok = check_dependencies()
    print()
    
    print("--- Checking Required Workspace Directories ---")
    directories_ok = check_directory_structure()
    print()
    
    print("--- Checking Environment & System Configurations ---")
    check_api_keys()
    check_smtp_config()
    print("=" * 60)
    
    overall_status = python_ok and packages_ok and directories_ok
    if overall_status:
        print("\033[92m[SUCCESS] BusinessPilot AI local environment is fully configured and ready!\033[0m")
        print("Run the dashboard with: \033[1mstreamlit run dashboard/app.py\033[0m")
        sys.exit(0)
    else:
        print("\033[91m[ERROR] System requirements validation failed. Please address issues listed above.\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
