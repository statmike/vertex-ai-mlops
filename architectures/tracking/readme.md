![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2Farchitectures%2Ftracking&dt=readme.md)

# /architectures/tracking/readme.md

This folder contains workbooks that setup tracking of the repositories files.  Great care is taken to not use user identifying information.  The goal is understanding document popularity relative the the total contents of the repository and overall.  Google Analytics Measurement Protocol is used to log `page_view` events without user identification or client identification - just a count of views.  GitHub traffic and metrics are used to understand the repositories usage at GitHub.com.  This measures post-conversion (already discovered at GitHub.com) and usage frequency.  Some notebooks also have YouTube videos for walkthroughs and the YouTube measurement API is used to understand popularity and engagement of this content.


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
    
    
    
---
## TODO
- remove or move each exploration notebook to the respective setup folder
    - [ ] tracking_ga4.ipynb - move (ready)
    - [ ] tracking_github.ipynb - move after lifecycle finishes and cloud function removed
    - [ ] tracking_youtube.ipynb - delete after contents moves