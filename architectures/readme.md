![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Farchitectures&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/architectures/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# /architectures/readme.md

This folder contains the graphics used throughout the repository and the notebooks that process the graphics.

## Sources:
- [architectures](https://docs.google.com/presentation/d/1pylP8PEhRWFEOw8TQeLCIAsT6TcKR6DXtPR37NSHM3U/edit?usp=sharing&resourcekey=0-qCmD6iLzRKUALTCmcB_wLw)
    - A Google Slides Document
    - Exported to PDF and saved here: `./architectures.pdf`
        - File > Download > PDF
    - Process `architectures.pdf`:
        - open `Create Images.ipynb`
        - under mapping, manually update list to match the order inside the pdf
        - empty the folders:
            - ./slides
            - ./thumbnails/plain
            - ./thumbnails/playbutton
            - ./thumbnails/prepared
        - run cells, it will automatically exclude the first slide
- [vertex-ai-mlops](https://drive.google.com/file/d/1j6faffFliqXf51VV0J3Lh38ADRvunqUu/view?usp=sharing&resourcekey=0-R2gI3ClMXO_rrOEP7MVDog)
    - A Lucid Chart Document
    - Images are expored (file > export > png > select all) to PNG and saved in ./overview/

## Layout
- Folders:
    - `/notebooks` - contains screenshots specific to individual notebooks throughout repository
    - `/overview` - contains exported from Lucid Chart (mentioned above)
    - `/slides` - hold screenshots slides processed from the `architecutres.pdf` file, done by the notebook [Create Images.ipynb](./Create%20Images.ipynb)
    - `/thumbnails` - processed slides from `/slides` that are prepared for use as thumbnails, done by the notebook [Create Images.ipynb](./Create%20Images.ipynb)
- Notebooks:
    - [Create Images.ipynb](./Create%20Images.ipynb) - processes the `./architectures.pdf` file into the folders `./slides` and `./thumbnails`
    - [markdown_info.md](./markdown_info.md) - a collection of hyperlinks used throughout this repository
    - [markdown_tables.md](./markdown_tables.md) - development space for the markdown tables used in the repositories main `readme.md`




## TRACKING

The folder [./tracking](./tracking/readme.md) contains all the explorations and setup used for tracking data from YouTube, GitHub, and Google Analytics.
