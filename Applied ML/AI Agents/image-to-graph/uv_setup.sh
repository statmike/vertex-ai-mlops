#!/bin/bash
# uv_setup.sh

PYTHON_VERSION="3.13.3"

# 1. Initialize with a specific Python version (skip if already initialized)
# This downloads the version if you don't have it but it will recognize pyenv versions installed as well.
if [ ! -f pyproject.toml ]; then
    uv init --python "$PYTHON_VERSION" --no-readme
    rm -f main.py hello.py
fi

# 2. Add your core stack
uv add google-adk google-genai pydantic pillow python-dotenv

# 3. Sync the environment (creates .venv)
uv sync

# 4. Automate the Jupyter Kernel setup using the project folder name
PROJECT_NAME=$(basename "$PWD")
uv run python -m ipykernel install --user --name="$PROJECT_NAME" --display-name "Python ($PROJECT_NAME)"

# 5. Create the initial requirements.txt for Docker compatibility
uv export --format requirements-txt --output-file requirements.txt

echo "Project '$PROJECT_NAME' is ready with Python $PYTHON_VERSION and Jupyter kernel installed."

# ---
# Ongoing Usage:
#
# Add new packages:
#   uv add <package-name>
#
# Update requirements.txt after adding packages:
#   uv export --format requirements-txt --output-file requirements.txt
#
# Update Python version:
#   uv python pin <version>
#   uv sync
