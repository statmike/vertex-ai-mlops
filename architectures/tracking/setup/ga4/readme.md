![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Farchitectures%2Ftracking%2Fsetup%2Fga4&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/ga4/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/ga4/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/ga4/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/ga4/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/ga4/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# /architectures/tracking/setup/ga4/readme.md

> **NOTE:** This approach is being removed (March 2024).  The replacement is a custom pixel tracker whose development is completely open and covered in this repository.  Check out [../pixel/readme.md](../pixel/readme.md).

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
    - Walkthrough of
        - exploring the tables
        - setting up an initial table
        - create a query to incrementally update the table
        - setting up a scheduled query to run the incremental update
- [GA4 Forecasting.ipynb](./GA4%20Forecasting.ipynb)
    - Add forecast data to the reporting table created by `GA4 Reporting.ipynb`
    - This alters the table and scheduled query from the `GA4 Reporting.ipynb` notebook
    - Adds rows to the table for forecasting 2 weeks out
    - Schedules a weekly, Mon at 3AM EST, job that update the forecast for the current week and the next week but preserves the forecast from last week
    - Included in dashboard this will show an expected target value for the current week while it accumulates throughout the week.
    - Forecast is done a the daily level
    - Row in the reporting table are separated by column `row_type` which has values 'forecast' and 'actual'

Add/Remove Tracking In Files (`.md` and `.ipynb`):
- [ga4_add.ipynb](./ga4_add.ipynb)
    - Use the techniques from [../../tracking_ga4.ipynb](../../tracking_ga4.ipynb) to add the tracking links to all documents of type `.md` and `.ipynb`
- [ga4_list.py](./ga4_list.py)
    - Use this script to list all the files with tracking in this repository
    - These are the files that will be updated by the `ga4_remove.py` script
    - Run this script first as a test (recommended)
- [ga4_remove.py](./ga4_remove.py)
    - Use this script to remove all the tracking in this repository for a local clone
    - run the script with `python ga4_remove.py` in this folder location
    
