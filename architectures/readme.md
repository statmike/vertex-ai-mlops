![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2Farchitectures&dt=readme.md)

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
