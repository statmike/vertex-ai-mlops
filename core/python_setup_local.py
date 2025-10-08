
def authenticate(PROJECT_ID):
    """
    Authenticate user and set the Google Cloud project.

    Args:
        PROJECT_ID: The desired Google Cloud project ID

    Returns:
        tuple: (authenticated, REQ_TYPE) where authenticated is bool and REQ_TYPE is str
    """
    import subprocess
    authenticated = False
    REQ_TYPE = 'LOCAL'

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
        import google.auth
        import google.auth.exceptions
        try:
            credentials, project_id = google.auth.default()
            print("✅ Existing ADC found.")
            authenticated = True
        except google.auth.exceptions.DefaultCredentialsError:
            print("❌ ERROR: ADC are not set in this environment.")
            print("   Please run from your local terminal: gcloud auth application-default login")

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
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
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
    """
    import subprocess

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
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: A gcloud command failed. Your account may not have the required permissions.")
        print(f"   Details: {e.stderr}")


def manage_packages(REQUIREMENTS_URLS, REQ_TYPE):
    """
    Check and install required Python packages.

    Args:
        REQUIREMENTS_URLS: Dictionary mapping REQ_TYPE to requirements URLs
        REQ_TYPE: Type of requirements (e.g., 'COLAB', 'LOCAL')
    """
    import sys
    import subprocess

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
    else:
        print("\n✅ Installation complete.")
        print("\n🚨 Restarting kernel to apply changes...")
        import IPython
        app = IPython.Application.instance()
        app.kernel.do_shutdown(True)


def get_project_info():
    """
    Get and display Google Cloud project information.

    Returns:
        tuple: (PROJECT_ID, PROJECT_NUMBER)
    """
    import subprocess

    PROJECT_ID = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True, check=True).stdout.strip()
    PROJECT_NUMBER = subprocess.run(['gcloud', 'projects', 'describe', PROJECT_ID, '--format=value(projectNumber)'], capture_output=True, text=True, check=True).stdout.strip()

    print("\n" + "="*50)
    print("Google Cloud Project Information")
    print("="*50)
    print(f"PROJECT_ID     = {PROJECT_ID}")
    print(f"PROJECT_NUMBER = {PROJECT_NUMBER}")
    print("="*50 + "\n")

    return PROJECT_ID, PROJECT_NUMBER

