![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fconcept-bq%2Fagent_bq_forecast%2Fdeploy&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/concept-bq/agent_bq_forecast/deploy/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/concept-bq/agent_bq_forecast/deploy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/concept-bq/agent_bq_forecast/deploy/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/concept-bq/agent_bq_forecast/deploy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/concept-bq/agent_bq_forecast/deploy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
</table><br/><br/>

---
# Agent Deployment Guide

This folder contains everything needed to deploy and manage this agent on Vertex AI Agent Engine and Gemini Enterprise.

## Quick Start

To deploy this agent, run the notebooks in this order:

1. **[deploy-vertex-ai-agent-engine.ipynb](./deploy-vertex-ai-agent-engine.ipynb)** - Deploy the agent to Vertex AI Agent Engine
2. **[use-vertex-ai-agent-engine.ipynb](./use-vertex-ai-agent-engine.ipynb)** - Test and interact with the deployed agent
3. **[register-adk-on-agent-engine-with-gemini-enterprise.ipynb](./register-adk-on-agent-engine-with-gemini-enterprise.ipynb)** - Register with Gemini Enterprise (optional)

## Files in This Folder

- **deployment.json** - Stores deployment metadata (resource IDs, timestamps)
- **deploy-vertex-ai-agent-engine.ipynb** - Main deployment notebook
- **use-vertex-ai-agent-engine.ipynb** - Usage and testing notebook
- **register-adk-on-agent-engine-with-gemini-enterprise.ipynb** - Gemini Enterprise registration

## Prerequisites

Before deploying, ensure you have:

1. **Google Cloud Project Setup**
   - Active GCP project with billing enabled
   - Vertex AI API enabled
   - Agent Engine API enabled

2. **Authentication**
   - Authenticated with `gcloud auth login`
   - Application default credentials configured

3. **Required Permissions**
   - `roles/aiplatform.user` or `roles/aiplatform.admin`
   - `roles/storage.objectAdmin` (for GCS staging)
   - Additional permissions based on agent's tools (e.g., BigQuery, etc.)

4. **Project Configuration**
   - Main folder `.env` file configured with:
     - `GOOGLE_CLOUD_PROJECT`
     - `GOOGLE_CLOUD_LOCATION`
     - `GOOGLE_CLOUD_STORAGE_BUCKET`

5. **Python Environment**
   - Python 3.13+
   - Project dependencies installed (see main folder `requirements.txt`)

## Deployment Process

### Step 1: Deploy to Vertex AI Agent Engine

Open and run **deploy-vertex-ai-agent-engine.ipynb**:

- **Local Testing** - Test the agent locally before deployment
- **Deployment** - Create or update the deployment on Vertex AI
- **Metadata Storage** - Saves deployment info to `deployment.json`
- **Permissions** - Configure IAM roles for the agent's service account

**What happens:**
- Agent code is packaged and uploaded to GCS
- Reasoning Engine resource is created in Vertex AI
- Resource ID is saved to `deployment.json`

### Step 2: Test the Deployment

Open and run **use-vertex-ai-agent-engine.ipynb**:

- **SDK Usage** - Interact with the deployed agent using Python SDK
- **REST API** - Examples of direct REST API calls
- **Session Management** - Create, list, and delete sessions
- **Conversation History** - View agent interaction logs

**Customize:**
- Update test queries to match your agent's capabilities
- Test different user scenarios
- Verify agent responses and behavior

### Step 3: Register with Gemini Enterprise (Optional)

Open and run **register-adk-on-agent-engine-with-gemini-enterprise.ipynb**:

- **App Configuration** - Set your Gemini Enterprise app ID
- **Registration** - Register the agent with Gemini Enterprise
- **Metadata Update** - Saves registration info to `deployment.json`

**Requirements:**
- Gemini Enterprise must be enabled in your project
- You need a Gemini Enterprise app ID

## Configuration

### Auto-Configuration

The notebooks automatically configure themselves based on their location:

```
agent_convo_api/
├── deploy/               ← Notebooks run from here
│   ├── deploy-vertex-ai-agent-engine.ipynb
│   └── ...
├── agent.py             ← Agent code (imported from ../agent.py)
└── ...

project_root/
├── .env                 ← Project config (loaded from ../../.env)
├── requirements.txt     ← Dependencies (used from ../../requirements.txt)
└── ...
```

The notebooks automatically:
- Detect the agent name from the folder structure
- Load project configuration from the main `.env`
- Import the agent from `../agent.py`
- Use the shared `requirements.txt`

### Manual Configuration

If you need to customize deployment settings, you can modify:

**In deploy-vertex-ai-agent-engine.ipynb:**
- `agent_gcs_path` - Where artifacts are staged in GCS
- IAM roles and permissions for the service account
- Test queries and scenarios

**In register-adk-on-agent-engine-with-gemini-enterprise.ipynb:**
- `APP_ID` - Your Gemini Enterprise app ID (required)
- `LOCATION` - Typically "global" for Gemini Enterprise

## Deployment Metadata

The `deployment.json` file stores:

```json
{
  "resource_id": "projects/.../reasoningEngines/...",
  "deployed_at": "2025-01-15T10:30:00",
  "display_name": "agent_name",
  "description": "Agent description",
  "gemini_enterprise_agent_id": "projects/.../agents/...",
  "registered_at": "2025-01-15T11:00:00"
}
```

This file is used by the notebooks to:
- Detect existing deployments
- Avoid duplicate deployments
- Connect to the deployed agent
- Track registration status

**Do not edit this file manually** - it's automatically managed by the notebooks.

## Updating a Deployment

To update an existing deployment with code changes:

1. Make changes to your agent code in `../agent.py` or tool files
2. Open **deploy-vertex-ai-agent-engine.ipynb**
3. Find the "Update Existing Deployment" section
4. Uncomment and run the update cell

The update will:
- Re-package your agent code
- Upload to GCS
- Update the Vertex AI resource
- Preserve the same resource ID

## Permissions Management

The deployed agent runs as a service account:
```
service-{PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com
```

**Default permissions:**
- `roles/aiplatform.reasoningEngineServiceAgent` (automatically granted)
- Includes GCS access for staging and artifacts

**Additional permissions** may be needed based on your agent's tools:

| Tool Type | Required Roles |
|-----------|---------------|
| BigQuery | `roles/bigquery.jobUser`<br>`roles/bigquery.dataViewer` |
| Conversational Analytics API | `roles/geminidataanalytics.dataAgentStatelessUser`<br>`roles/cloudaicompanion.user` |
| Secret Manager | `roles/secretmanager.secretAccessor` |
| Cloud Storage | Usually covered by default role |

Add permissions in the deploy notebook's "Manage Deployed App Permissions" section.

## Troubleshooting

### Common Issues

**1. Agent not found during deployment**
- Ensure you're running the notebook from the `deploy/` folder
- Check that `../agent.py` exists and has a `root_agent` defined

**2. Permission errors**
- Verify you have necessary GCP IAM roles
- Check that APIs are enabled (Vertex AI, Agent Engine)
- Review service account permissions

**3. Import errors**
- Ensure all dependencies are installed
- Check that you're using the project's Python environment
- Verify paths in the auto-configuration cells

**4. Deployment.json not found**
- Run deploy notebook before use/register notebooks
- Check that deployment completed successfully

**5. Gemini Enterprise registration fails**
- Verify Gemini Enterprise is enabled
- Check that APP_ID is correct
- Ensure you have permissions to register agents

### Getting Help

For detailed deployment documentation, see:
- [Main Deployment Guide](../../readme.md#deployment) - Project-wide deployment info
- [Vertex AI Agent Engine Docs](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- [ADK Deployment Docs](https://google.github.io/adk-docs/deploy/)

## Copying to New Agents

To deploy a different agent in this project:

1. Create the agent's deployment folder:
   ```bash
   mkdir -p path/to/new_agent/deploy
   ```

2. Copy the deployment notebooks:
   ```bash
   cp agent_convo_api/deploy/*.ipynb path/to/new_agent/deploy/
   ```

3. Copy the deployment.json template:
   ```bash
   cp agent_convo_api/deploy/deployment.json path/to/new_agent/deploy/
   ```

4. (Optional) Copy this readme and customize:
   ```bash
   cp agent_convo_api/deploy/readme.md path/to/new_agent/deploy/
   ```

5. Run the notebooks from the new agent's deploy folder

The notebooks will automatically:
- Detect the new agent's name
- Import the correct agent code
- Create a new deployment
- Store metadata in the new location

**No code changes required!** The templates are fully agent-agnostic.

## Clean Up

To delete the deployment:

1. Open **deploy-vertex-ai-agent-engine.ipynb**
2. Find the "Delete Deployed Agent" section
3. Set `delete_app = True`
4. Run the cell

This will:
- Delete the Vertex AI Agent Engine resource
- Clear the deployment metadata
- Preserve the agent code (no local files deleted)

**Note:** This does NOT delete the Gemini Enterprise registration. You'll need to remove that separately through the Gemini Enterprise console if needed.
