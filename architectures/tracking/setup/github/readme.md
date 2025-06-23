![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Farchitectures%2Ftracking%2Fsetup%2Fgithub&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/github/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/github/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/github/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/github/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/architectures/tracking/setup/github/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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