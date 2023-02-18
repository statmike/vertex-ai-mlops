![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2Farchitectures%2Ftracking%2Fsetup%2Fga4&dt=readme.md)

# /architectures/tracking/setup/ga4/readme.md

Setup Google Analytics for tracking document touches in this repository.

>Great care is taken to not use user identifying information.  The goal is understanding document popularity relative the the total contents of the repository and overall.  Google Analytics Measurement Protocol is used to log `page_view` events without user identification or client identification - just a count of views.

## Notebooks and Scripts In This Folder:

Notebooks For Setup and Reporting of GA4 Data:
- [GA4 Setup.ipynb](./GA4%20Setup.ipynb)
    - Full walkthrough of setting up
        - Google Analytics
        - Tracking with Measurement Protocol
        - Exporting GA4 to BigQuery
        - Data Layout in BigQuery
        - Review Data in BigQuery
- [GA4 Reporting.ipynb](./GA4%20Reporting.ipynb)
    - Walkthrough of setting up a scheduled query to prepare GA4 data for reporting

Add/Remove Tracking In Files (`.md` and `.ipynb`):
- [tracking_ga4_add.ipynb](./tracking_ga4_add.ipynb)
    - Use the techniques from [../../tracking_ga4.ipynb](../../tracking_ga4.ipynb) to add the tracking links to all documents of type `.md` and `.ipynb`
- [ga4_list.py](./ga4_list.py)
    - Use this script to list all the files with tracking in this repository
    - These are the files that will be updated by the `ga4_remove.py` script
    - Run this script first as a test (recommended)
- [ga4_remove.py](./ga4_remove.py)
    - Use this script to remove all the tracking in this repository for a local clone
    - run the script with `python ga4_remove.py` in this folder location
    
