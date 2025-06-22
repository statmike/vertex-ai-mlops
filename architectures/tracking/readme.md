![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Farchitectures%2Ftracking&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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