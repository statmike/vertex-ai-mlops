
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


def manage_packages(REQUIREMENTS_URLS, REQ_TYPE):
    """
    Check and install required Python packages.

    Args:
        REQUIREMENTS_URLS: Dictionary mapping REQ_TYPE to requirements URLs
        REQ_TYPE: Type of requirements (e.g., 'COLAB', 'LOCAL')

    Returns:
        bool: True if packages were installed, False if already up to date
    """
    import sys
    import subprocess

    print("\n" + "="*50)
    print("PACKAGE MANAGEMENT")
    print("="*50)

    url = REQUIREMENTS_URLS[REQ_TYPE]
    print(f"Checking and installing dependencies from: {url}")
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-r', url, '--upgrade'],
        capture_output=True, text=True
    )
    install_log = result.stdout.splitlines() + result.stderr.splitlines()
    install_log = [line for line in install_log if line.strip() and "WARNING: You are using pip version" not in line]
    install_action_words = ["Successfully installed", "Downloading", "Attempting uninstall"]
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


def setup_environment(PROJECT_ID, REQ_TYPE, REQUIREMENTS_URLS, REQUIRED_APIS):
    """
    Main orchestrator function to set up the complete Python GCP environment.

    Args:
        PROJECT_ID: The desired Google Cloud project ID
        REQ_TYPE: Type of requirements (e.g., 'COLAB', 'PRIMARY', 'ALL')
        REQUIREMENTS_URLS: Dictionary mapping REQ_TYPE to requirements URLs
        REQUIRED_APIS: List of required API service names

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
    packages_installed = manage_packages(REQUIREMENTS_URLS, updated_req_type)

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
    print(f"✅ Package Install:   {'Installed' if packages_installed else 'Already up to date'}")
    print(f"✅ Project ID:        {PROJECT_ID_current}")
    print(f"✅ Project Number:    {PROJECT_NUMBER}")
    print("="*50 + "\n")

    return {
        'success': True,
        'authenticated': authenticated,
        'apis_enabled': apis_success,
        'packages_installed': packages_installed,
        'PROJECT_ID': PROJECT_ID_current,
        'PROJECT_NUMBER': PROJECT_NUMBER,
        'REQ_TYPE': updated_req_type
    }



