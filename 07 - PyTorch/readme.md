![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2F07+-+PyTorch&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/07%20-%20PyTorch/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# /07 - PyTorch/readme.md
**This series is in development**

This series of notebooks highlights the use of Vertex AI for machine learning workflows with [PyTorch](https://pytorch.org/).


## Hosting YOLO Models On Vertex AI Endpoints

YOLO Models are popular for Vision AI.  Hosting them involves more than serving predictions from a trained model.

The **inputs** are images that need to be preprocessed to conform to the prediction inputs. These preprocessing steps include:
- Resize to fit within model input frame while preserving aspect ratio
- Letterbox to pad any areas need to make the image the expected size
- Convert images to data - a matrix of Width x Height x Color Channels
- Reorder color channels to match model: some file format are BGR and others are RGB for example
- Transpose the order of elements to match the model input: Color x Width x Height
- Normalize inputs - atleast scale from [0, 255] to [0, 1]

The **output** is a list of detections.  For every anchor point (typically more than 25k) there is a vector with the center point, size, confidence, and a score for each of the trained class levels.  The desired final output is usually the original image with bounding boxes drawn around any object detected with specified level of confidence.  The post-processing of the output into this image requires:
- Filter to only detections meeting a specified confidence threshold
- Detect the highest predicted class score and identify class. Further filter to minimum class score threshold.
- Convert detection coordinates from [center(x, y), width, height] to [lower_left(x, y), upper_right(x, y)]
- Apply non-maximum suppression to remove duplicate object detections with specified overlap threshold
- Annotate the final list of detections with labeled bounding boxes on the image

Where do the pre and post processing happen?  All on the client?  All on the endpoint?  A combination of client and endpoint? Below we examine a solutions that can support all of these options.

Vertex AI Endpoints can host NVIDIA Triton inference server.  This is an open-source inference server that can:
- support multiple ML framework - simoultaneously!
- multiple models - and model versions!
- has a framework for ensemble chains or pipelines that is easy to specify
- runs on CPU and/or GPU
- managed dynamic batching built-in

This notebook is a workshop in utilizing Vertex AI Endpoints with NVIDIA Triton inference server to host a YOLO model with multiple ensembles for different types of pre/post processors. 
- [YOLOv5 On Vertex AI Endpoints With NVIDIA Triton Server](./YOLOv5%20On%20Vertex%20AI%20Endpoints%20With%20NVIDIA%20Triton%20Server.ipynb)
