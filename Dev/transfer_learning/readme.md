![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FDev%2Ftransfer_learning&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Dev/transfer_learning/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Transfer Learning

## Vision
- train, test, val images
    - real, and synth sets
    - where to get altered/synthetic sets?
        - vae
        - diffusion
        - gan
- train, tune, classify
    - imagenet, none, test+val
    - imagenet, synth, synth
    - imagenet, synth, real
    - imagenet, ratio, ratio
    
# Goals
- Classify with imagenet
- finetune and classify with imagenet base
- generate synth data: vae
- generate synth data: diffusion
- generate synth data: gan
- finetune and classify with synth
- finetune with synth, classify with real
- finetune ratio, classify ratio
