##This gcloud command is work in progress for creating managed notebooks##
gcloud notebooks runtimes create mh-gcloud-mng-nb-test \
--runtime-access-type=SINGLE_USER \
--runtime-owner=<owner_email_id> \
--machine-type=<enter_machine_type> \
--location=<enter_region> \
--post-startup-script=<google_cloud_storage_location> \
--post-startup-script-behavior=DOWNLOAD_AND_RUN_EVERY_START


## --post-startup-script-behavior attribute is not working at this point
## --post-startup-script location must be google cloud storage location