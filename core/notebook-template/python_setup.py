# ==============================================================================
# Python GCP Environment Setup Module
# ==============================================================================
#
# This module provides centralized setup functions for Python-based Google Cloud
# notebooks, including authentication, API enablement, and package management.
#
# Main Functions:
#   - authenticate(): Handles GCP authentication for both Colab and local environments
#   - check_and_enable_apis(): Verifies and enables required Google Cloud APIs
#   - manage_packages(): Installs Python packages from requirements files with validation
#   - setup_environment(): Main orchestrator that runs complete environment setup
#
# Usage:
#   This file is designed to be downloaded and imported dynamically in notebooks:
#
#   import os, urllib.request
#   url = 'https://raw.githubusercontent.com/.../python_setup.py'
#   urllib.request.urlretrieve(url, 'python_setup_local.py')
#   import python_setup_local as python_setup
#   os.remove('python_setup_local.py')
#
#   setup_info = python_setup.setup_environment(
#       PROJECT_ID='your-project-id',
#       REQ_TYPE='ALL',  # or 'PRIMARY' or 'COLAB'
#       REQUIREMENTS_URL='https://path/to/requirements.txt',
#       REQUIRED_APIS=['bigquery.googleapis.com', 'storage.googleapis.com']
#   )
#
# Requirements File Naming Convention:
#   - requirements.txt: Full environment with all dependencies (REQ_TYPE='ALL')
#   - requirements-brief.txt: Primary packages only (REQ_TYPE='PRIMARY')
#   - requirements-colab.txt: Colab-optimized list (REQ_TYPE='COLAB')
#
# Installation Tools:
#   - pip: Standard Python package installer (default, always available)
#   - uv: Modern, fast Python package installer (implemented, requires installation)
#   - poetry: Dependency management tool (implemented, requires poetry environment)
#
# Poetry Optional Dependency Groups:
#   When using INSTALL_TOOL='poetry', you can optionally define POETRY_GROUPS in your
#   notebook to install additional dependency groups from pyproject.toml:
#     POETRY_GROUPS = 'dev'       # Installs main + dev group
#     POETRY_GROUPS = 'dev,test'  # Installs main + multiple groups (comma-separated)
#     POETRY_GROUPS = None        # Installs main dependencies only (default)
#
# Author: statmike
# Repository: https://github.com/statmike/vertex-ai-mlops
# ==============================================================================


def authenticate(PROJECT_ID, REQ_TYPE):
    """
    Authenticate user and set the Google Cloud project.

    Args:
        PROJECT_ID: The desired Google Cloud project ID

    Returns:
        tuple: (authenticated, REQ_TYPE) where authenticated is bool and REQ_TYPE is str
    """
    import subprocess
    authenticated = False
    project_id = None

    print("\n" + "="*50)
    print("AUTHENTICATION")
    print("="*50)

    try:
        from google.colab import auth
        print("Running in Google Colab. Authenticating user...")
        # This triggers the pop-up and sets ADC
        auth.authenticate_user()
        print("✅ Colab user authenticated.")
        authenticated = True
        REQ_TYPE = 'COLAB'
        project_id = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True, check=True).stdout.strip()
    except ImportError:
        print("Checking for existing ADC...")
        try:
            # Check if ADC is configured by trying to get an access token
            result = subprocess.run(
                ['gcloud', 'auth', 'application-default', 'print-access-token'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("✅ Existing ADC found.")
                authenticated = True
                project_id = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True, check=True).stdout.strip()
            else:
                print("❌ ERROR: ADC are not set in this environment.")
                print("   Please run from your local terminal: gcloud auth application-default login")
        except FileNotFoundError:
            print("❌ ERROR: gcloud CLI not found. Please install Google Cloud SDK.")

    if authenticated:
        if project_id == PROJECT_ID:
            print(f"✅ Project is correctly set to '{PROJECT_ID}'.")
        elif not project_id:
            print(f"⚠️ No default project found. Setting project to '{PROJECT_ID}'...")
            try:
                subprocess.run(['gcloud', 'config', 'set', 'project', PROJECT_ID], capture_output=True, text=True, check=True).stdout.strip()
                print(f"✅ Project successfully set to '{PROJECT_ID}'.")
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"❌ ERROR: Failed to set project using gcloud. Please configure it manually.")
        else:
            print(f"⚠️ WARNING: Mismatch detected!")
            print(f"   - Desired Project: '{PROJECT_ID}'")
            print(f"   - Current Project:   '{project_id}'")
            try:
                subprocess.run(['gcloud', 'config', 'set', 'project', PROJECT_ID], capture_output=True, text=True, check=True)
                print(f"✅ Project successfully switched to '{PROJECT_ID}'.")
            except FileNotFoundError:
                print(f"❌ ERROR: Failed to switch project.")
                print(f"   gcloud CLI not found. Please install Google Cloud SDK.")
            except subprocess.CalledProcessError as e:
                print(f"❌ ERROR: Failed to switch project.")
                print(f"   The active user may not have permissions for the desired project '{PROJECT_ID}'.")
                print(f"   Details: {e.stderr}")

    return authenticated, REQ_TYPE

def check_and_enable_apis(PROJECT_ID, REQUIRED_APIS):
    """
    Check and enable required Google Cloud APIs.

    Args:
        PROJECT_ID: The Google Cloud project ID
        REQUIRED_APIS: List of required API service names

    Returns:
        bool: True if successful, False if errors occurred
    """
    import subprocess

    print("\n" + "="*50)
    print("API CHECK & ENABLE")
    print("="*50)

    try:
        enabled_services = subprocess.run(
            ['gcloud', 'services', 'list', '--enabled', f'--project={PROJECT_ID}', '--format=value(config.name)'],
            capture_output=True, text=True, check=True
        ).stdout.strip().splitlines()
        for api in REQUIRED_APIS:
            if api in enabled_services:
                print(f"✅ {api} is already enabled.")
            else:
                print(f"⚠️ {api} is not enabled. Attempting to enable now...")
                subprocess.run(
                    ['gcloud', 'services', 'enable', api, f'--project={PROJECT_ID}'],
                    capture_output=True, check=True # Hides output unless there's an error.
                )
                print(f"✅ Successfully enabled {api}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: A gcloud command failed. Your account may not have the required permissions.")
        print(f"   Details: {e.stderr}")
        return False


def manage_packages(REQUIREMENTS_URL, REQ_TYPE, INSTALL_TOOL='pip'):
    """
    Check and install required Python packages.

    Args:
        REQUIREMENTS_URL: Base URL for requirements.txt file
        REQ_TYPE: Type of requirements (e.g., 'COLAB', 'PRIMARY', 'ALL')
        INSTALL_TOOL: Package installation tool to use ('pip', 'uv', or 'poetry'). Default: 'pip'

    Returns:
        bool or None: True if packages were installed, False if already up to date, None on error
    """
    import sys
    import subprocess
    import urllib.request
    import urllib.error
    import shutil
    import os

    print("\n" + "="*50)
    print("PACKAGE MANAGEMENT")
    print("="*50)
    print(f"Installation Tool: {INSTALL_TOOL}")

    # Helper function to check if running in poetry environment
    def is_running_in_poetry_env():
        """Check if current Python environment is managed by poetry."""
        try:
            result = subprocess.run(['poetry', 'env', 'info', '--path'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                poetry_env_path = result.stdout.strip()
                current_python = sys.executable

                # Check if current Python is within poetry's venv path
                if poetry_env_path and current_python.startswith(poetry_env_path):
                    return True, poetry_env_path
        except Exception:
            pass

        return False, None

    # Adapt URL based on REQ_TYPE
    if REQ_TYPE == 'PRIMARY':
        url = REQUIREMENTS_URL.replace('requirements.txt', 'requirements-brief.txt')
    elif REQ_TYPE == 'COLAB':
        url = REQUIREMENTS_URL.replace('requirements.txt', 'requirements-colab.txt')
    else:  # ALL
        url = REQUIREMENTS_URL

    # Validate the adapted URL exists, with fallback to base URL
    def check_url_exists(test_url):
        """Check if URL is accessible."""
        try:
            urllib.request.urlopen(test_url, timeout=5)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError):
            return False

    # Check if adapted URL exists
    if not check_url_exists(url):
        print(f"⚠️  Requirements file not found at: {url}")

        # Try fallback to base URL if we adapted it
        if url != REQUIREMENTS_URL:
            print(f"   Attempting fallback to base requirements: {REQUIREMENTS_URL}")
            if check_url_exists(REQUIREMENTS_URL):
                url = REQUIREMENTS_URL
                print(f"✅ Using base requirements file.")
            else:
                print(f"❌ ERROR: Base requirements file also not found at: {REQUIREMENTS_URL}")
                print(f"   Please verify the REQUIREMENTS_URL is correct and accessible.")
                return None
        else:
            print(f"❌ ERROR: Requirements file not found at: {REQUIREMENTS_URL}")
            print(f"   Please verify the REQUIREMENTS_URL is correct and accessible.")
            return None

    # Validate INSTALL_TOOL and prepare installation command
    if INSTALL_TOOL not in ['pip', 'uv', 'poetry']:
        print(f"❌ ERROR: Invalid INSTALL_TOOL '{INSTALL_TOOL}'")
        print(f"   Allowed values: 'pip', 'uv', 'poetry'")
        return None

    # Check if the requested tool is available
    if INSTALL_TOOL == 'pip':
        # pip is assumed to be available with Python
        tool_available = True
    elif INSTALL_TOOL == 'poetry':
        tool_path = shutil.which(INSTALL_TOOL)
        tool_available = tool_path is not None

        if not tool_available:
            print(f"❌ ERROR: '{INSTALL_TOOL}' command not found on this system.")
            print(f"   Please install {INSTALL_TOOL} or use INSTALL_TOOL='pip' instead.")
            print(f"   To install {INSTALL_TOOL}:")
            print(f"     - See: https://python-poetry.org/docs/#installation")
            return None
        else:
            print(f"✅ Found {INSTALL_TOOL} at: {tool_path}")

            # Additional check: verify we're running in a poetry environment
            in_poetry_env, poetry_path = is_running_in_poetry_env()
            if not in_poetry_env:
                print(f"❌ ERROR: Poetry is available but current kernel is NOT running in a poetry environment.")
                print(f"   Current Python: {sys.executable}")
                print(f"   To use poetry, please start your notebook within a poetry environment:")
                print(f"     - Run: poetry shell")
                print(f"     - Or: poetry run jupyter lab")
                return None
            else:
                print(f"✅ Running in poetry environment: {poetry_path}")
    else:
        # For other tools like uv
        tool_path = shutil.which(INSTALL_TOOL)
        tool_available = tool_path is not None

        if not tool_available:
            print(f"❌ ERROR: '{INSTALL_TOOL}' command not found on this system.")
            print(f"   Please install {INSTALL_TOOL} or use INSTALL_TOOL='pip' instead.")
            print(f"   To install {INSTALL_TOOL}:")
            if INSTALL_TOOL == 'uv':
                print(f"     - See: https://github.com/astral-sh/uv")
            return None
        else:
            print(f"✅ Found {INSTALL_TOOL} at: {tool_path}")

    # Helper function to find pyproject.toml in current or parent directories
    def find_pyproject_toml(stop_at_dir='vertex-ai-mlops'):
        """
        Search for pyproject.toml in current directory and parent directories.

        Args:
            stop_at_dir: Directory name to stop searching at (default: 'vertex-ai-mlops')

        Returns:
            str or None: Path to pyproject.toml if found, None otherwise
        """
        current_dir = os.path.abspath(os.getcwd())

        while True:
            pyproject_path = os.path.join(current_dir, 'pyproject.toml')

            if os.path.exists(pyproject_path):
                return pyproject_path

            # Check if we've reached the stop directory
            if os.path.basename(current_dir) == stop_at_dir:
                break

            # Move to parent directory
            parent_dir = os.path.dirname(current_dir)

            # Stop if we've reached the root directory
            if parent_dir == current_dir:
                break

            current_dir = parent_dir

        return None

    # Handle different package managers
    if INSTALL_TOOL == 'uv':
        print(f"Checking and installing dependencies from: {url}")
        result = subprocess.run(
            ['uv', 'pip', 'install', '-r', url, '--upgrade'],
            capture_output=True, text=True
        )
        install_log = result.stdout.splitlines() + result.stderr.splitlines()
    elif INSTALL_TOOL == 'poetry':
        # Poetry uses pyproject.toml instead of requirements.txt
        print(f"ℹ️  Poetry mode: Installing from pyproject.toml (REQUIREMENTS_URL ignored)")

        # Search for pyproject.toml in current or parent directories
        pyproject_path = find_pyproject_toml()

        if pyproject_path:
            print(f"✅ Found pyproject.toml at: {pyproject_path}")
            pyproject_dir = os.path.dirname(pyproject_path)

            # Change to the directory containing pyproject.toml for poetry install
            original_dir = os.getcwd()
            os.chdir(pyproject_dir)
            print(f"   Changed working directory to: {pyproject_dir}")
        else:
            # Try to download from URL (replace requirements.txt with pyproject.toml)
            pyproject_url = REQUIREMENTS_URL.replace('requirements.txt', 'pyproject.toml')
            print(f"⚠️  No pyproject.toml found in current or parent directories")
            print(f"   Attempting to download from: {pyproject_url}")

            if check_url_exists(pyproject_url):
                try:
                    urllib.request.urlretrieve(pyproject_url, 'pyproject.toml')
                    print("✅ Downloaded pyproject.toml")
                    pyproject_path = 'pyproject.toml'
                except Exception as e:
                    print(f"❌ ERROR: Failed to download pyproject.toml: {e}")
                    return None
            else:
                print(f"❌ ERROR: No local pyproject.toml and URL not accessible")
                print(f"   Poetry requires a pyproject.toml file to install dependencies")
                return None

        # Check if POETRY_GROUPS is defined in caller's scope
        import inspect
        caller_globals = inspect.currentframe().f_back.f_back.f_globals  # Go up two frames (manage_packages -> setup_environment -> notebook)
        poetry_groups = caller_globals.get('POETRY_GROUPS', None)

        # Build poetry install command with optional groups
        if poetry_groups:
            print(f"ℹ️  Installing with optional group(s): {poetry_groups}")
            install_cmd = ['poetry', 'install', '--with', poetry_groups]
        else:
            install_cmd = ['poetry', 'install']

        # Run poetry install
        print(f"Running poetry install...")
        result = subprocess.run(
            install_cmd,
            capture_output=True, text=True
        )
        install_log = result.stdout.splitlines() + result.stderr.splitlines()

        # Change back to original directory if we changed it
        if pyproject_path and pyproject_path != 'pyproject.toml':
            os.chdir(original_dir)
            print(f"   Restored working directory to: {original_dir}")

    elif INSTALL_TOOL == 'pip':
        print(f"Checking and installing dependencies from: {url}")
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', url, '--upgrade'],
            capture_output=True, text=True
        )
        install_log = result.stdout.splitlines() + result.stderr.splitlines()
    else:
        # This shouldn't happen due to validation above, but just in case
        return None

    # Continue with installation log processing (for pip, uv, and poetry)
    install_log = [line for line in install_log if line.strip() and "WARNING: You are using pip version" not in line]

    # Check for poetry-specific "no changes" message
    if INSTALL_TOOL == 'poetry' and any("No dependencies to install or update" in line for line in install_log):
        install = False
    else:
        # Keywords that indicate package installation activity
        install_action_words = [
            "Successfully installed", # pip specific
            "Downloading", # pip specific
            "Attempting uninstall", # pip specific
            "Uninstalled", "Removed", # uv specific
            "Updated",  # uv specific
            "Installed",  # uv and poetry specific
            "Installing dependencies",  # poetry specific
            "Package operations:",  # poetry specific
        ]
        install = False

        for line in install_log:
            if any(keyword in line for keyword in install_action_words):
                install = True
                break

    if not install:
        print("✅ All packages are already installed and up to date.")
        return False
    else:
        print("\n✅ Installation complete.")
        if REQ_TYPE == 'COLAB':
            print("\n🚨 Restarting kernel to apply changes...")
            print("   After restart, you can continue from the next cell (no need to rerun earlier cells).")
            import IPython
            app = IPython.Application.instance()
            app.kernel.do_shutdown(True)
        else:
            print("\n⚠️  Note: If you experience import errors, restart the kernel manually.")
            print("   After restart, you can continue from the next cell (no need to rerun earlier cells).")
        return True


def setup_environment(PROJECT_ID, REQ_TYPE, REQUIREMENTS_URL, REQUIRED_APIS, INSTALL_TOOL='pip'):
    """
    Main orchestrator function to set up the complete Python GCP environment.

    Args:
        PROJECT_ID: The desired Google Cloud project ID
        REQ_TYPE: Type of requirements (e.g., 'COLAB', 'PRIMARY', 'ALL')
        REQUIREMENTS_URL: Base URL for requirements.txt file (will be adapted based on REQ_TYPE)
        REQUIRED_APIS: List of required API service names
        INSTALL_TOOL: Package installation tool to use ('pip', 'uv', or 'poetry'). Default: 'pip'

    Returns:
        dict: Summary of setup results including PROJECT_ID, PROJECT_NUMBER, and status flags

    Note:
        In Colab, if packages are installed, the kernel will restart and this function
        will not complete. You should re-run this function after restart to complete setup.
    """
    import subprocess

    print("\n" + "="*50)
    print("PYTHON GCP ENVIRONMENT SETUP")
    print("="*50)

    # Step 1: Authenticate
    authenticated, updated_req_type = authenticate(PROJECT_ID, REQ_TYPE)

    if not authenticated:
        print("\n" + "="*50)
        print("SETUP FAILED: Authentication required")
        print("="*50)
        return {'success': False, 'authenticated': False}

    # Step 2: Check and enable APIs
    apis_success = check_and_enable_apis(PROJECT_ID, REQUIRED_APIS)

    # Step 3: Manage packages (may trigger kernel restart in Colab)
    packages_result = manage_packages(REQUIREMENTS_URL, updated_req_type, INSTALL_TOOL)

    # Check if package installation failed
    if packages_result is None:
        print("\n" + "="*50)
        print("SETUP FAILED: Package installation error")
        print("="*50)
        return {
            'success': False,
            'authenticated': authenticated,
            'apis_enabled': apis_success,
            'packages_installed': None,
            'error': 'Package installation failed - requirements URL not accessible'
        }

    # If we reach here, kernel didn't restart (or already restarted and we're running again)
    # Step 4: Get project information
    PROJECT_ID_current = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True, check=True).stdout.strip()
    PROJECT_NUMBER = subprocess.run(['gcloud', 'projects', 'describe', PROJECT_ID_current, '--format=value(projectNumber)'], capture_output=True, text=True, check=True).stdout.strip()

    print("\n" + "="*50)
    print("Google Cloud Project Information")
    print("="*50)
    print(f"PROJECT_ID     = {PROJECT_ID_current}")
    print(f"PROJECT_NUMBER = {PROJECT_NUMBER}")
    print("="*50 + "\n")

    # Overall summary
    print("\n" + "="*50)
    print("SETUP SUMMARY")
    print("="*50)
    print(f"✅ Authentication:    {'Success' if authenticated else 'Failed'}")
    print(f"✅ API Configuration: {'Success' if apis_success else 'Failed'}")
    print(f"✅ Package Install:   {'Installed' if packages_result else 'Already up to date'}")
    print(f"✅ Installation Tool: {INSTALL_TOOL}")
    print(f"✅ Project ID:        {PROJECT_ID_current}")
    print(f"✅ Project Number:    {PROJECT_NUMBER}")
    print("="*50 + "\n")

    return {
        'success': True,
        'authenticated': authenticated,
        'apis_enabled': apis_success,
        'packages_installed': packages_result,
        'INSTALL_TOOL': INSTALL_TOOL,
        'PROJECT_ID': PROJECT_ID_current,
        'PROJECT_NUMBER': PROJECT_NUMBER,
        'REQ_TYPE': updated_req_type
    }



