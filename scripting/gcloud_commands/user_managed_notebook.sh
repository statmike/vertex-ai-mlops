##This command creates a user managed notebook instance and clone the github vertexai mlops repository##
gcloud notebooks instances create mh-gcloud-nb-test  \
--vm-image-project=deeplearning-platform-release \
--vm-image-family=<enter_vm_image_family> \
--machine-type=<enter_machine_type> \
--network=projects/<project_id>/global/networks/<vpc_name> \
--subnet=projects/<project_id>/regions/<region>/subnetworks/<subnet_name> \
--project=<project_id> \
--service-account=<enter_service_account_email_id> \
--location=<enter_zone> \
--post-startup-script=https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/scripting/notebook_startup.sh

##Sample Script with Values##
gcloud notebooks instances create gcloud-nb-test  \
--vm-image-project=deeplearning-platform-release \
--vm-image-family=tf-ent-2-3-cu110-notebooks \
--machine-type=n1-standard-4 \
--network=projects/test_project_id/global/networks/default \
--subnet=projects/test_project_id/regions/us-central1/subnetworks/default \
--project=test_project_id \
--service-account=123456789-testsa@developer.gserviceaccount.com \
--location=us-central1-a \
--post-startup-script=https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/scripting/notebook_startup.sh