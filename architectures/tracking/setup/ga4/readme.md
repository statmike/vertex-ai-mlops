# /architectures/tracking/setup/ga4/readme.md

Setup Google Analytics for tracking document touches in this repository.

>Great care is taken to not use user identifying information.  The goal is understanding document popularity relative the the total contents of the repository and overall.  Google Analytics Measurement Protocol is used to log `page_view` events without user identification or client identification - just a count of views.

## Notebooks and Scripts In This Folder:

- [tracking_ga4_add.ipynb](./tracking_ga4_add.ipynb)
    - Use the techniques from [../../tracking_ga4.ipynb](../../tracking_ga4.ipynb) to add the tracking links to all documents of type `.md` and `.ipynb`
- [ga4_remove.py](./ga4_remove.py)
    - Use this script to remove all the tracking in this repository for a local clone
    - run the script with `python ga4_remove.py` in this folder location