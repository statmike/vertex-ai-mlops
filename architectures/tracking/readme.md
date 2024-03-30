![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Farchitectures%2Ftracking&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# /architectures/tracking/readme.md

This folder contains workbooks that setup tracking of the repositories files.  Great care is taken to not use user identifying information.  The goal is understanding document popularity relative the the total contents of the repository and overall.  ~~Google Analytics Measurement Protocol~~ Custom tracking is used to log page view events without user or location identification - just a count of views.  GitHub traffic and metrics are used to understand the repositories usage at GitHub.com.  This measures post-conversion (already discovered at GitHub.com) and usage frequency.  Some notebooks also have YouTube videos for walkthroughs and the YouTube measurement API is used to understand popularity and engagement of this content.


## Environment Setup

**The actual environment setup for collection and reporting is documented in the [/setup](./setup/readme.md) Folder**

It contains the notebooks used to setup the environment, read data from APIs on schedules, and ETL the data for reporting.


## Notebooks In This Folder Explore The Data Sources
- [tracking_github.ipynb](./tracking_github.ipynb)
    - How to Use GitHub API to retrieve traffic and statistics information
    - Save information to BigQuery
    - Automate the daily collection of this raw information with Pub/Sub, Secret Manager, Cloud Functions, Cloud Scheduler
- [tracking_ga4.ipynb](./tracking_ga4.ipynb)
    - Explore ways of tracking document usage in the repository without collecting user information
- [tracking_youtube.ipynb](./tracking_youtube.ipynb)
    - Explore ways of tracking document usage in the repository without collecting user information
- custom pixel tracking with [/pixel/developing-tracking-pixel.ipynb](./pixel/developing-tracking-pixel.ipynb)
    - Explore implementing a completely custom pixel tracking application with Cloud Functions, Cloud Run, PubSub, and BigQuery
    
---
## TODO
- remove or move each exploration notebook to the respective setup folder
    - [ ] tracking_ga4.ipynb - move (ready)
    - [ ] tracking_github.ipynb - move after lifecycle finishes and cloud function removed
    - [ ] tracking_youtube.ipynb - delete after contents moves