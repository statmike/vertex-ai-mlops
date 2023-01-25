![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2Farchitectures&dt=readme.md)

# architectures

This folder contains the graphics used throughout the repository and the notebooks that process the graphics.


Sources:
- [architectures](https://docs.google.com/presentation/d/1pylP8PEhRWFEOw8TQeLCIAsT6TcKR6DXtPR37NSHM3U/edit?usp=sharing&resourcekey=0-qCmD6iLzRKUALTCmcB_wLw)
    - A Google Slides Document
    - Exported to PDF and saved here: ./architectures.pdf
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

## Tracking
Two types of tracking data:
- GA4 tracking of repository documents without any identifying information:
    - [./tracking/tracking_ga4.ipynb](./tracking/tracking_ga4.ipynb)
    - This data gets written to BQ each night: vertex-ai-mlops-369716
- GitHub API for Traffic Information
    - [./tracking/tracking_github.ipynb](./tracking/tracking_github.ipynb)
    - This information gets written to BigQuery each night: vertex-ai-mlops-369716
