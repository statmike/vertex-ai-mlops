![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fscripting&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/scripting/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

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