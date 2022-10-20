# Scripting
Automation options for setting up Vertex AI with this repository.


## Using gcloud command to create an user managed notebook in Vertex AI

If you have a GCP Project with Vertex AI enabled and Workbench enabled then these command line commands will help automate the create of user managed workbench instance and clone this repository into the `home/jupyter` folder:

There are two different ways through which we can execute the gcloud commands:

1. Using **Cloud Shell** in the Google Cloud Console
   - login to https://console.cloud.google.com and make sure that you are logged in as admin
   - Open Cloud Shell from the top right corner in the console 
   - Run the following command `gcloud auth login` and follow the prompts to authorize the cloud shell ( here is the link to learn more about cloud shell - https://cloud.google.com/shell/docs/run-gcloud-commands)
   - Navigate to enable api on the hamburger menu (https://cloud.google.com/endpoints/docs/openapi/enable-api) 
   - Enable the **Vertex AI API** (if you have not already)
   - Make sure that you have the service account, vpc network and subnet information
   - Copy the content of `gcloud_commands/user_managed_notebook.sh` and paste it in a text editor so that you can plug in the information by replacing the placeholder in the `gcloud_commands/user_managed_notebook.sh`
   - Paste the command in cloud shell and execute the command
2. Using **gcloud sdk** installed in local terminal
   - As a pre-requisite, please make sure that you have enabled the vertex ai api and have the vpc, subnet and service account information available for plugging in to the gcloud command
   - Install gcloud sdk by following the steps in the document mentioned in the link (https://cloud.google.com/sdk/docs/install)
   - Open the terminal/command prompt and follow the steps mentioned in the link (https://cloud.google.com/sdk/docs/initializing) to initialize, authorize and configure **gcloud cli** and connect to Google Cloud services
   - Copy the content of `gcloud_commands/user_managed_notebook.sh` and paste it in a text editor so that you can plug in the information by replacing the placeholder in the `gcloud_commands/user_managed_notebook.sh`
   - Paste the command in cloud shell and execute the command