![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Farchitectures%2Ftracking%2Fsetup%2Fpixel&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/pixel/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# /architectures/tracking/setup/pixel/readme.md

Setup a custom pixel tracker for the repository with data privacy for users.  Only collect document name and timestamp (and sometimes the http client information when available)!

**Note:** This was developed to replace and migrate away from the GA4 method covered in [../ga4/readme.md](../ga4/readme.md)

## Notebooks and Scripts In This Folder

### Creation And Setup

- [prod-tracking-pixel.ipynb](./prod-tracking-pixel.ipynb)
    - Creates Cloud funtion to respond with tracking pixel
        - Validates that request is from a document in this repository
        - send the document info and timestamp to a pubsub topic
    - Creates Cloud function that writes event to BigQuery table
        - triggered by pubsub topic
        - write received data to a BigQuery table that collect page view events
- upcoming: migrate-ga4-data-to-pixel-data.ipynb
- upcoming: pixel-reporting.ipynb
- upcoming: pixel-forecasting.ipynb

### Implementation

The `https` links for pixel retrieval are added to documents with the header creation process covered in:
- [../../../headers/add_headers.ipynb](../../../headers/add_headers.ipynb)

### Management: List and Remove Pixel Links
List/Remove Pixel Tracking In Files (`.md` and `.ipynb`):
- [pixel_list.py](./pixel_list.py)
    - Use this script to list all the files with tracking in this repository
    - These are the files that will be updated by the `pixel_remove.py` script
    - Run this script first as a test (recommended)
- [pixel_remove.py](./pixel_remove.py)
    - Use this script to remove all the tracking in this repository for a local clone
    - run the script with `python pixel_remove.py` at this folder location within the repository
