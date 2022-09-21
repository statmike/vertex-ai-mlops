# Scripting
Automation options for setting up Vertex AI with this repository.


## Workbench 
If you have a GCP Project with Vertex AI enabled and Workbench enabled then these command line commands will help automate the create of w a workbench instance and clone this repository into the `home/jupyter` folder:

```
gcloud components update

gcloud auth login

gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
gcloud config set project statmike-mlops-349915

# user managed notebook - working
gcloud notebooks instances create mh-gcloud-nb-test  \
--vm-image-project=deeplearning-platform-release \
--vm-image-family=tf-ent-2-3-cu110-notebooks \
--machine-type=n1-standard-4 \
--network=projects/statmike-mlops-349915/global/networks/default \
--subnet=projects/statmike-mlops-349915/regions/us-central1/subnetworks/default \
--project=statmike-mlops-349915 \
--service-account=1026793852137-compute@developer.gserviceaccount.com \
--location=us-central1-a \
--post-startup-script=https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/scripting/notebook_startup.sh

# managed notebook - in progress
gcloud notebooks runtimes create mh-gcloud-mng-nb-test \
--runtime-access-type=SINGLE_USER \
--runtime-owner=statmike@statmike.altostrat.com \
--machine-type=n1-standard-4 \
--location=us-central1-a \
--post-startup-script=https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/scripting/notebook_startup.sh \
--post-startup-script-behavior=DOWNLOAD_AND_RUN_EVERY_START


```