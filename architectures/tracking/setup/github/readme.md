![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2Farchitectures%2Ftracking%2Fsetup%2Fgithub&dt=readme.md)

# /architectures/tracking/setup/github/readme.md

Setup the data reads from the GitHub API
- use: https://docs.github.com/en/rest?apiVersion=2022-11-28

## Notebooks For Gathering and Processing Information:
Commits:
- [GitHub Metrics - 1 - Commits - Initial Creation](./GitHub%20Metrics%20-%201%20-%20Commits%20-%20Initial%20Creation.ipynb)
    - Building the tables `commits` and `commits_files` in the BigQuery dataset `github_metrics`
- [GitHub Metrics - 2 - Commits - Reporting Scheduled Query](./GitHub%20Metrics%20-%202%20-%20Commits%20-%20Reporting%20Scheduled%20Query.ipynb)
- [GitHub Metrics - 3 - Commits - Incremental Update Cloud Function](./GitHub%20Metrics%20-%203%20-%20Commits%20-%20Incremental%20Update%20Cloud%20Function.ipynb)
    - Create Cloud Function that automates the incremental updates for the stage 1 and 2 notebooks above

Traffic:
- [GitHub Metrics - 1 - Traffic - Initial Creation](./GitHub%20Metrics%20-%201%20-%20Traffic%20-%20Initial%20Creation.ipynb)
    - Building the tables `traffic_clones`, `traffic_popular_paths`, `traffic_popular_referrers`, `traffic_views`, `stargazers`, `forks`, `subscribers` in BigQuery dataset `github_metrics`
- [GitHub Metrics - 2 - Traffic - Reporting Scheduled Query](./GitHub%20Metrics%20-%202%20-%20Traffic%20-%20Reporting%20Scheduled%20Query.ipynb)
- [GitHub Metrics - 3 - Traffic - Incremental Update Cloud Function](./GitHub%20Metrics%20-%203%20-%20Traffic%20-%20Incremental%20Update%20Cloud%20Function.ipynb)
    - Create Cloud Function that automates the incremental updates for the stage 1 and 2 notebooks above