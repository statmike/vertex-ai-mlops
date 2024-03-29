![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FIDE&file=colab.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/IDE/colab.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Google Colaboratory: Colab
Notebooks, Jupyter notebooks, iPython notebooks .... COLAB

An interesting thing about notebooks is that they are actually  just files, stored with extension `.ipynb`, that contain a JSON representation of what is called a notebook.  If you open one up in a text editor it will look like JSON, or a dictionary of `key:value` pairs that represent the elements of the notebook - [check out the notebook schema here](https://nbformat.readthedocs.io/en/latest/format_description.html). One element is `cells` which is just a list of dictionaries representing cell contents.  One of those keys for a cell is `cell_type` which holds values like `code` or `markdown`.  The actual contents of a cell are stored in the value paired with the key named `source` - it just a list of strings representing each line of the cell.  This means the same notebook file can be portable between many interfaces, like Colab!

So what is Colab then? An executable notebook service from Google Drive. 
- a reader for notebook files with Google Drive storage
- wraps the file like a document with a file management interface specialized for notebooks 
- automatically connects to a free cloud run time (even GPUs!)


## More on Colab
![](https://www.tensorflow.org/images/colab_logo_32px.png)

Colab provides overviews in tutorials with Colabs.  Here is a great place to get started:
- [Welcome To Colaboratory](https://colab.research.google.com)
    - It will bring up a menu where you can immediately navigate to
        - your own notebooks in Drive
        - Create a new notebook - stored in Drive
        - GitHub (public and private repositories)
        - Upload from local computer
        - **Google provided tutorials**


## Opening in Colab
Besides going to [https://colab.sandbox.google.com/](https://colab.sandbox.google.com/) where you are presented a naviation and selection window you can also directly open notebooks in Colab in several ways.
- **From Drive**
    - From Colab you can easily choose to open a notebook stored in Google Drive
    - You can also setup Google Drive associate notebook files with Colab which will change their icon the the neat Colab icon and automatically open them in Colab when you select them.
        - Go to Google Drive
        - Select the Gear icon in the upper right (Settings): select Settings
        - Go to the 'Manage Apps' section
        - Click the link for 'Connect more apps' and search for 'Colaboratory'.  Select and Install.
- **From GitHub using URL**
    - Base URL: `http://colab.research.google.com/github`
    - GitHub Repository Notebook location:
        - The URL looks like: `https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20Forecasting/BQML%20Multivariate%20Forecasting%20with%20ARIMA%2B%20XREG.ipynb`
        - The extention is: `/statmike/vertex-ai-mlops/blob/main/Applied%20Forecasting/BQML%20Multivariate%20Forecasting%20with%20ARIMA%2B%20XREG.ipynb`
    - Combine the Base URL and notebook extension:
        - [http://colab.research.google.com/github/statmike/vertex-ai-mlops/blob/main/Applied%20Forecasting/BQML%20Multivariate%20Forecasting%20with%20ARIMA%2B%20XREG.ipynb](http://colab.research.google.com/github/statmike/vertex-ai-mlops/blob/main/Applied%20Forecasting/BQML%20Multivariate%20Forecasting%20with%20ARIMA%2B%20XREG.ipynb)
    - Use the ![](https://colab.research.google.com/assets/colab-badge.svg) logo for the link
        - `https://colab.research.google.com/assets/colab-badge.svg`
- **From GitHub Gist using URL**
    - Base URL: `http://colab.research.google.com/gist`
    - GitHub Gist Notebook location:
        - The URL looks like: `https://gist.github.com/statmike/6a8dedb32c50829a5d2a4763dfab7754#file-bq-tools-cmek-and-cross-region-move-ipynb`
        - The extention is: `/statmike/6a8dedb32c50829a5d2a4763dfab7754#file-bq-tools-cmek-and-cross-region-move-ipynb`
    - Combine the Base URL and notebook extension:
        - [http://colab.research.google.com/gist/statmike/6a8dedb32c50829a5d2a4763dfab7754#file-bq-tools-cmek-and-cross-region-move-ipynb](http://colab.research.google.com/gist/statmike/6a8dedb32c50829a5d2a4763dfab7754#file-bq-tools-cmek-and-cross-region-move-ipynb)
    - Use the ![](https://colab.research.google.com/assets/colab-badge.svg) logo for the link
        - `https://colab.research.google.com/assets/colab-badge.svg`
- **Chrome Plugin** 
    - Add the plugin: [Open in Colab](https://chrome.google.com/webstore/detail/open-in-colab/iogfkhleblhcpcekbiedikdehleodpjo?hl=en)
    - From any GitHub page with a notebook just press the button from this plugin and the current notebook will load in Colab


## Features & Tips (Just the Highlights)
- Tutorial with one click access like those in the TensorFlow library: [https://www.tensorflow.org/tutorials](https://www.tensorflow.org/tutorials)
- One Click access to demo and tutorials for Vertex AI: [https://github.com/GoogleCloudPlatform/vertex-ai-samples](https://github.com/GoogleCloudPlatform/vertex-ai-samples)
- Hover over a cells run icon to see popup with the execution time
- Run only a portion of a cell by highlighting it and using `Runtime > Run Selection` or pressing `Ctrl + Shift + Enter`
- The Tools Menu
    - Diff Notebooks - Compare any two notebooks
    - Keyboard Shortcuts - configurable!
    - Settings
        - Themes like light, dark and adaptive modes
        - Set a snippet notebook that is always available in the snippet menu
        - Authenticate your GitHub account
        - configure syntax checking and automations like closing qutoes and brackets
- Just press `Ctrl` and click a class name to see its definition
- prototype flask web apps using `flask-ngrok` package
- Tensorboard is already installed for easy access with magics:
> ```
%load_ext tensorboard
%tensorboard --logdir logs
```
- view resources usage like RAM, Disk
- Share the notebook with different levels of access (even set expiration): viewer, editior, commenter
- Add comments to cells and interact with other users, including @ mentions
- mirror a cell in a nested tab for larger working area during debugging
- edit mode for markdown (text) cells that give split view previews
- A one-time use notebook (does not automatically save to drive)
    - Use the URL: [https://colab.research.google.com/notebooks/empty.ipynb](https://colab.research.google.com/notebooks/empty.ipynb)


## Connection / Runtimes
The default runtimes are free and can include access to GPUs and TPUs (`Runtime > Change Runtime Type`).  This comes with limitations that are very practical like
- Idle timeout.  The notebooks runtime will disconnect after a period of no use.  The notebook is preserved along with outputs.
- Maximum lifetime.  The notebooks runtime will not continue indefinitely and will eventually timeout. The notebook contents are preserved along with outputs.  And the notebook can runtime can be started again.
- Accelerator choices are limited.  There are GPU and TPU services available for free use but configuration is limited.

Custom Runtimes are available as well:
- [Local Runtime](https://research.google.com/colaboratory/local-runtimes.html)
    - This could be your personal computer or even a custom environment in on a server, like a Google Comptue Engine Instance)
- [Colab PRO](https://colab.research.google.com/signup)
- [Google Cloud Hosted Virtual Machine](https://research.google.com/colaboratory/marketplace.html)


## Use Colab With A Google Cloud Project

### Authenticate to Google Cloud
From a Colab notebook you can autenticate your Google Cloud login which will allow your notebook to work with Google Cloud using the scope of your permissions.  This is because the Google Cloud CLI tool `gcloud` is installed.  Using the following code in a cell within your notebook will prompt you to login and authenticate.  This process will be needed each time you run your notebook.

```python
from google.colab import auth
auth.authenticate_user()
```

### Set The Current Project
Once you are authenticated you can set your Google Cloud Project with the `gcloud` cli:

```
PROJECT_ID = 'statmike-mlops-349915' # replace with project ID
!gcloud config set project {PROJECT_ID}
```

### Use BigQuery Magic
The BigQuery magics are already setup to use in Colab.  Note that they need the project for the query to be set which can be done by passing the `PROJECT_ID` variable set above - note the use of `$`.

```
%%bigquery --project=$PROJECT_ID
SELECT
    input_column,
    CAST((input_column - AVG(input_column) OVER()) / STDDEV(input_column) OVER() AS FLOAT64) AS manual_column,
    ML.STANDARD_SCALER(input_column) OVER() AS feature_column
FROM
    UNNEST([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) as input_column
ORDER BY input_column
```

### Use Python Client For BigQuery
Now, if you want to use any of the [Python clients for Google Cloud](https://cloud.google.com/python/docs/reference) all you need to do is make sure they are installed and setup them up.  Here are examples for BigQuery:

Install the [BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest#installation) if needed, it is actually pre-installed and updated regularly:
```
!pip install --upgrade google-cloud-bigquery -q -U
```

Setup and use the client to submit a query:
- note: it will automatically set the current project but you can use the parameter `project=` and `location=` to sets the manually

```python
from google.cloud import bigquery
bq = bigquery.Client(project = PROJECT_ID)
```

Run a SQL query and return results to a Pandas dataframe:

```python
query = f"""
    SELECT
        input_column,
        CAST((input_column - AVG(input_column) OVER()) / STDDEV(input_column) OVER() AS FLOAT64) AS manual_column,
        ML.STANDARD_SCALER(input_column) OVER() AS feature_column
    FROM
        UNNEST([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) as input_column
    ORDER BY input_column
"""
bq.query(query = query).to_dataframe()
```

### More ways to Use BigQuery from a Notebook
For more ways to use BigQuery from a notebook see the notebook: [vertex-ai-mlops/03 - BigQuery ML (BQML)/03 - Introduction to BigQuery ML (BQML).ipynb](../03%20-%20BigQuery%20ML%20(BQML)/03%20-%20Introduction%20to%20BigQuery%20ML%20(BQML).ipynb)

### Link From BigQuery Console to Colab
There is a BigQuery [preview feature](https://cloud.google.com/bigquery/docs/explore-data-colab) that offers a direct link to Colab from any query result in the BigQuery Console:

<p align="center" width="100%">
    <center>
    <img src="../architectures/notebooks/Tips/bq_explore_in_colab.png" width = '50%'>
    </center>
</p>

This opens a new Colab notebook with the code to authenticate and setup the BigQuery client.  This even fills in the current project and location information.  It also fills in the job id for the query results you were viewing and recalls those to load to a Pandas dataframe!




