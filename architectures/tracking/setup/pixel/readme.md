![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Farchitectures%2Ftracking%2Fsetup%2Fpixel&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/pixel/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/pixel/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/pixel/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/pixel/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/pixel/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
