![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2Flegacy%2FVertex+AI+Search&file=vertex_search_setup.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/legacy/Vertex%20AI%20Search/vertex_search_setup.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/legacy/Vertex%2520AI%2520Search/vertex_search_setup.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/legacy/Vertex%2520AI%2520Search/vertex_search_setup.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/legacy/Vertex%2520AI%2520Search/vertex_search_setup.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/legacy/Vertex%2520AI%2520Search/vertex_search_setup.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# /Applied GenAI/Vertex AI Search/vertex_search_setup.md

Following are the steps to create a Vertex AI Search App using Google Cloud Console.

To start with, download the MLB rule books from the URLs listed below and upload them to Google Cloud Storage. Steps to create a bucket in google cloud storage can be found [here](https://cloud.google.com/storage/docs/creating-buckets) and upload files to Google Cloud Storage can be found [here](https://cloud.google.com/storage/docs/uploading-objects)

- [MLB 2022 Rule Book](https://img.mlbstatic.com/mlb-images/image/upload/mlb/hhvryxqioipb87os1puw.pdf)
- [MLB 2023 Rule Book](https://img.mlbstatic.com/mlb-images/image/upload/mlb/wqn5ah4c3qtivwx3jatm.pdf)

<p align="center" width="100%"><center>
    <img align="center" alt="Upload the files to Google Cloud Storage Bucket" src="../../../architectures/notebooks/applied/genai/vertex_ai_search/vertex_search_step_0.png" width="45%">
</center></p>

Once the files the uploaded to Cloud Storage Bucket, search for `Vertex AI Search and Conversation` in the search bar on the top of the console and switch to the page. You will be seeing the landing page as shown below in the screenshot.

<p align="center" width="100%"><center>
    <img align="center" alt="Click on New App Button" src="../../../architectures/notebooks/applied/genai/vertex_ai_search/vertex_search_step_1.png" width="45%">
</center></p>

Click on `New App` and select `Search` as App Type.

<p align="center" width="100%"><center>
    <img align="center" alt="Select Search" src="../../../architectures/notebooks/applied/genai/vertex_ai_search/vertex_search_step_2.png" width="45%">
</center></p>

Under Configuration, make sure to turn on `Enterprise Edition Features` and `Advanced LLM Features`. Also, Enter the `App Name` and select the region as `global`.

<p align="center" width="100%"><center>
    <img align="center" alt="Enter the App Name and Click Continue" src="../../../architectures/notebooks/applied/genai/vertex_ai_search/vertex_search_step_3.png" width="45%">
</center></p>

Next Step is to create a `Data Store`. Click on `Create New Data Store` and Select `Cloud Storage` as Data Source. 

<p align="center" width="100%"><center>
    <img align="center" alt="Select Cloud Storage" src="../../../architectures/notebooks/applied/genai/vertex_ai_search/vertex_search_step_4.png" width="45%">
</center></p>

Browse the Cloud Storage and select the files you have uploaded. 

<p align="center" width="100%"><center>
    <img align="center" alt="Browse to the location in Cloud Storage and select the files" src="../../../architectures/notebooks/applied/genai/vertex_ai_search/vertex_search_step_5.png" width="45%">
</center></p>

After choosing the files, enter the `Data Store` name and click on `Create`.

<p align="center" width="100%"><center>
    <img align="center" alt="Enter the Data Store Name" src="../../../architectures/notebooks/applied/genai/vertex_ai_search/vertex_search_step_6.png" width="45%">
</center></p>

Select the `Data Store` and click on `Create`.

<p align="center" width="100%"><center>
    <img align="center" alt="Click on Create to create the Data Store" src="../../../architectures/notebooks/applied/genai/vertex_ai_search/vertex_search_step_7.png" width="45%">
</center></p>

You will be able to watch the progress in `Data Store` creation as shown below.

<p align="center" width="100%"><center>
    <img align="center" alt="Data Store Creation in Progress" src="../../../architectures/notebooks/applied/genai/vertex_ai_search/vertex_search_step_8.png" width="45%">
</center></p>

After the successful completion of Data Store creation, You will be able to test the search app using the `preview feature` on the left pane.

<p align="center" width="100%"><center>
    <img align="center" alt="Testing in Console using the preview" src="../../../architectures/notebooks/applied/genai/vertex_ai_search/vertex_search_step_9.png" width="45%">
</center></p>