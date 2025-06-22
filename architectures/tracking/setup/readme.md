![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Farchitectures%2Ftracking%2Fsetup&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures%2Ftracking%2Fsetup/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures%2Ftracking%2Fsetup/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures%2Ftracking%2Fsetup/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures%2Ftracking%2Fsetup/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# /architectures/tracking/setup/readme.md

This folder contains the notebooks used to setup GCP services to read from APIs, schedule, ETL data for reporting and other automations for this processing.

>Great care is taken to not use user identifying information.  The goal is understanding document popularity relative the the total contents of the repository and overall.  Google Analytics Measurement Protocol is used to log `page_view` events without user identification or client identification - just a count of views.

## Direction
The setup of tracking involves 2 parts:
- 1. **data source setup**: retrieving each source into its own BigQuery dataset as a series of tables with inputs from the sources.  Jobs are designed, mostly with cloud functions, to populate these tables initially and then incrementally.
- 2. **data preparation**: setting up scheduled ETL jobs to transform each source into reporting tables in a single BigQuery dataset called `reporting`

## Sources
Each data source has a subfolder of notebooks specific to their setup:
- [/ga4](./ga4/readme.md)
    - include notebook that adds the tracking to each `.md` and `.ipynb` files in this repository
    - includes a script that will remove all the tracking from `.md` and `.ipynb` files in this repository
    - includes notebooks that:
        - walkthrough setting up Google Analytics Exports to BigQuery
        - walkthrough ETL process to prepare this data for reporting
    - decomissioning this for custom tracking - see pixel below:
- [/pixel](./pixel/readme.md)
    - create cloud function for custom pixel tracking with data privacy
    - migrate GA4 trackinng data to the custom tracker
    - update reporting to utilize the custom pixel tracking
- [/github](./github/readme.md)
    - includes notebooks that:
        - show examples of reading from API and preparing the data for storage in BigQuery
        - Build initial BigQuery tables of information
        - Build incremental updates for BigQuery tables
        - Automate/Schedule the incremental updates
        - Walkthrough and schedule the ETL process to prepare this data for reporting
- [/youtube](./youtube/readme.md)
    - includes notebooks that:
        - show examples of reading from API and preparing the data for storage in BigQuery
        - Build initial BigQuery tables of information
        - Build incremental updates for BigQuery tables
        - Automate/Schedule the incremental updates
        - Walkthrough and schedule the ETL process to prepare this data for reporting
- [/joins](./joins/readme.md)
    - includes notebooks that:
        - Walkthrough and schedule the ETL process to combine data from multiple sources for reporting

## Overview of Data Pipeline

| Overview |
:-------------------------:
![](../../overview/tracking_overview.png)


| Detail of Data Pipeline |
:-------------------------:
![](../../overview/tracking_detail.png)


## Notes
- These notebooks are designed to run in the project `vertex-ai-mlops-369716`
- recommendation is logging into that account with chrome, visit this repository on GitHub, click the open in colab links within the notebooks
    - my process - need a better way for editing Colab and saving back to GitHub:
        - Update local machines clone of repository
        - open repository in finder
        - drag a copy of the notebooks to Google Drive of the account running them
        - open notebooks in Colab, edit, save
        - download notebooks from Google Drive
        - drag from download to JupyterLab Explorer and overwrite previous version
        - commit changes
        - push to GitHub
        - update local clone by pulling changes
        - delete old copy in Google Drive
        

---
## TODO
- [IP] Add GitHub Traffic and Engagement
- [ ] Add YouTube measurement
    - [ ] link associated notebooks
- [ ] move GA4 BQ Schedule Job to Cloud Function (daily)
- [ ] move GitHub Comming BQ Scheduled Job to Cloud Function (daily)