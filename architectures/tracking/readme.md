![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2Farchitectures%2Ftracking&dt=readme.md)

# tracking

This folder contains workbooks that setup tracking of the repositories files.  Great care is taken to not use user identifying information.  The goal is understanding document popularity relative the the total contents of the repository and overall.  Google Analytics Measurement Protocol is used to log `page_view` events without user identification or client identification - just a count of views.  GitHub traffic is used to understand the repositories usage at GitHub.com.  This measures post-conversion (already discovered at GitHub.com) and usage frequency.


**Notebooks**
- [tracking_github.ipynb](./tracking_github.ipynb)
    - How to Use GitHub API to retrieve traffic and statistics information
    - Save information to BigQuery
    - Automate the daily collection of this information with Pub/Sub, Secret Manager, Cloud Functions, Cloud Scheduler
- [tracking_ga4.ipynb](./tracking_ga4.ipynb)
    - Explore ways of tracking document usage in the repository without collecting user information
- [tracking_ga4_add.ipynb](./tracking_ga4_add.ipynb)
    - Use the technique from `tracking_ga4.ipynb` to add the tracking link to all documents of type `.md` and `.ipynb`