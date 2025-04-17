# Document Processing
> You are here `vertex-ai-mlops/Applied ML/Solution Prototypes/document-processing/readme.md`

A common scenario for companies is receiving documents, like invoices, with variable formats and needing to extract information into a structured form. Compounding this is the need to verify document authenticity and detect fraud, creating a full-scale document processing challenge.

This prototype focuses on a fast-to-create and easy-to-scale solution for both document extraction and verification, initially without any custom ML. This allows for rapid deployment and validation of the core workflow before investing in more complex, custom models. It establishes a robust foundation for expanding the approach to fraud detection with customized models and other ML-based approaches as needed.

To start, we will establish a core workflow for ingesting documents into Google Cloud services. This workflow will extract information and compare documents to previous ones, assessing the likelihood of anomalies that may indicate potential fraud.

<div align="center">
  <img src="./resources/images/document_processing.png" alt="Document Processing" width="600"/>
</div>
