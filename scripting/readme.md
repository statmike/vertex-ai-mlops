![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fscripting&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/scripting/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/scripting/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/scripting/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/scripting/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/scripting/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# /scripting/readme.md
Automation options for setting up Vertex AI with this repository.

## Using gcloud command to create an user managed notebook in Vertex AI

If you have a GCP Project with Vertex AI enabled and Workbench enabled then these command line commands will help automate the create of user managed workbench instance and clone this repository into the `home/jupyter` folder:

**This command creates a user managed notebook instance and clone the github vertexai mlops repository**

`gcloud notebooks instances create mh-gcloud-nb-test  \
--vm-image-project=deeplearning-platform-release \
--vm-image-family=<enter_vm_image_family> \
--machine-type=<enter_machine_type> \
--network=projects/<project_id>/global/networks/<vpc_name> \
--subnet=projects/<project_id>/regions/<region>/subnetworks/<subnet_name> \
--project=<project_id> \
--service-account=<enter_service_account_email_id> \
--location=<enter_zone> \
--post-startup-script=https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/scripting/notebook_startup.sh`

**Sample Script with Values**

`gcloud notebooks instances create gcloud-nb-test  \
--vm-image-project=deeplearning-platform-release \
--vm-image-family=tf-ent-2-3-cu110-notebooks \
--machine-type=n1-standard-4 \
--network=projects/test_project_id/global/networks/default \
--subnet=projects/test_project_id/regions/us-central1/subnetworks/default \
--project=test_project_id \
--service-account=123456789-testsa@developer.gserviceaccount.com \
--location=us-central1-a \
--post-startup-script=https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/scripting/notebook_startup.sh`

There are two different ways through which we can execute the gcloud commands:

1. Using **Cloud Shell** in the Google Cloud Console
   - login to https://console.cloud.google.com and make sure that you are logged in as admin
   - Open Cloud Shell from the top right corner in the console 
   - Run the following command `gcloud auth login` and follow the prompts to authorize the cloud shell ( here is the link to learn more about cloud shell - https://cloud.google.com/shell/docs/run-gcloud-commands)
   - Navigate to enable api on the hamburger menu (https://cloud.google.com/endpoints/docs/openapi/enable-api) 
   - Enable the **Vertex AI API** (if you have not already)
   - Make sure that you have the service account, vpc network and subnet information
   - Replace the placeholder in the above mentioned sample command
   - Paste the command in cloud shell and execute the command
2. Using **gcloud sdk** installed in local terminal
   - As a pre-requisite, please make sure that you have enabled the vertex ai api and have the vpc, subnet and service account information available for plugging in to the gcloud command
   - Install gcloud sdk by following the steps in the document mentioned in the link (https://cloud.google.com/sdk/docs/install)
   - Open the terminal/command prompt and follow the steps mentioned in the link (https://cloud.google.com/sdk/docs/initializing) to initialize, authorize and configure **gcloud cli** and connect to Google Cloud services
   - Replace the placeholder in the above mentioned sample command
   - Paste the command in cloud shell and execute the command

> Note: Please do not change the values of following attributes in the **sample script**. Those values were set to make sure that the notebooks in the git repo mentioned in the post start up script runs without any issues.
> - vm-image-project
> - vm-image-family
> - machine-type
> - post-startup-script