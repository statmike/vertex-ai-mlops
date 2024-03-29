![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+Pre-Trained+APIs&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20Pre-Trained%20APIs/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# /Applied Pre-Trained APIs/readme.md

This series of notebooks will feature Google Cloud Pre-Trained APIs:
- [Media Translation](https://cloud.google.com/translate/media/docs/streaming)
- [Cloud Vision](https://cloud.google.com/vision/docs/features-list)
- [Cloud Video Intelligence AI](https://cloud.google.com/video-intelligence/docs/features)
- [Translation AI](https://cloud.google.com/translate/docs/overview)
- [Cloud Text-to-Speech](https://cloud.google.com/text-to-speech/docs/before-you-begin)
- [Cloud Speech-to-Text](https://cloud.google.com/speech-to-text/docs/concepts)
- [Cloud Natural Language](https://cloud.google.com/natural-language/docs/basics)
- [Cloud Inference API](https://cloud.google.com/inference/docs)
- [Cloud Data Loss Prevention](https://cloud.google.com/dlp/docs/concepts)

## Notebooks
- [api-fun-demo.ipynb](./api-fun-demo.ipynb)
    - a full circle demonstration for most of the Vertex AI based pre-trained APIs

## Pre-Trained APIs
<table style='text-align:center;vertical-align:middle' width="100%" cellpadding="1" cellspacing="0">
    <tr>
        <th colspan='4'>Pre-Trained Models</th>
        <th rowspan='2'>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl/v1/32px.svg">
            <a href="https://cloud.google.com/vertex-ai/docs/beginner/beginners-guide" target="_blank">AutoML</a>
        </th>
    </tr>
    <tr>
        <th>Data Type</th>
        <th>Pre-Trained Model</th>
        <th>Prediction Types</th>
        <th>Related Solutions</th>
    </tr>
    <tr>
        <td rowspan='2'>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/text_snippet/default/40px.svg">
            <br>Text
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/cloud_translation_api/v1/32px.svg">
            <br><a href="https://cloud.google.com/translate/docs/overview" target="_blank">Cloud Translation API</a>
        </td>
        <td>Detect, Translate</td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/text-to-speech/v1/32px.svg">
            <br><a href="https://cloud.google.com/text-to-speech/docs/basics" target="_blank">Cloud Text-to-Speech</a>
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_translation/v1/32px.svg">
            <br><a href="https://cloud.google.com/translate/automl/docs" target="_blank">AutoML Translation</a>
        </td>
    </tr>
            <tr>
                <td>
                   <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/cloud_natural_language_api/v1/32px.svg">
                   <br><a href="https://cloud.google.com/natural-language/docs/quickstarts" target="_blank">Cloud Natural Language API</a>
                </td>
                <td>
                    Entities (Identify and label), Sentiment, Entity Sentiment, Syntax, Content Classification
                </td>
                <td>
                    <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/healthcare_nlp_api/v1/32px.svg">
                    <br><a href="https://cloud.google.com/healthcare-api/docs/how-tos/nlp" target="_blank">Healthceare Natural Language API</a>
                </td>
                <td>
                    <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_natural_language/v1/32px.svg">
                    <br><a href="https://cloud.google.com/vertex-ai/docs/training-overview#text_data" target="_blank">AutoML Text</a>
            </tr>
    <tr>
        <td>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/image/default/40px.svg">
            <br>Image
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/cloud_vision_api/v1/32px.svg">
            <br><a href="https://cloud.google.com/vision/docs/features-list" target="_blank">Cloud Vision API</a>
        </td>
        <td>
            Crop Hint, OCR, Face Detect, Image Properties, Label Detect, Landmark Detect, Logo Detect, Object Localization, Safe Search, Web Detect
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/document_ai/v1/32px.svg">
            <br><a href="https://cloud.google.com/document-ai/docs/processors-list" target="_blank">Document AI</a>
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_vision/v1/32px.svg">
            <br><a href="https://cloud.google.com/vertex-ai/docs/training-overview#image_data" target="_blank">AutoML Image</a>
        </td>
    </tr>
    <tr>
        <td>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/mic/default/40px.svg">
            <br>Audio
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/media_translation_api/v1/32px.svg">
            <br><a href="https://cloud.google.com/media-translation" target="_blank">Cloud Media Translation API</a>
        </td>
        <td>Real-time speech translation</td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/speech-to-text/v1/32px.svg">
            <br><a href="https://cloud.google.com/speech-to-text/docs/basics" target="_blank">Cloud Speech-to-Text</a>
        </td>
        <td></td>
    </tr>
    <tr>
        <td>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/videocam/default/40px.svg">
            <br>Video
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/video_intelligence_api/v1/32px.svg">
            <br><a href="https://cloud.google.com/video-intelligence/docs/quickstarts" target="_blank">Cloud Video Intelligence API</a>
        </td>
        <td>
            Label Detect*, Shot Detect*, Explicit Content Detect*, Speech Transcription, Object Tracking*, Text Detect, Logo Detect, Face Detect, Person Detect, Celebrity Recognition
        </td>
        <td></td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_video_intelligence/v1/32px.svg">
            <br><a href="https://cloud.google.com/vertex-ai/docs/training-overview#video_data" target="_blank">AutoML Video</a>
        </td>
    </tr>
</table>

