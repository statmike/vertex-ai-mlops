# Document Processing With Generative AI: Parse, Extract, Validate Authenticity, and More
> You are here `vertex-ai-mlops/Applied ML/Solution Prototypes/document-processing/readme.md`

A common scenario for companies is receiving documents, like invoices, with variable formats and needing to extract information into a structured form. Compounding this is the need to verify document authenticity and detect fraud, creating a full-scale document processing challenge.

This prototype focuses on a fast-to-create and easy-to-scale solution for both document extraction and verification, initially without any custom ML. This allows for rapid deployment and validation of the core workflow before investing in more complex, custom models. It establishes a robust foundation for expanding the approach to fraud detection with customized models and other ML-based approaches as needed.

To start, we will establish a core workflow for ingesting documents into Google Cloud services. This workflow will extract information and compare documents to previous ones, assessing the likelihood of anomalies that may indicate potential fraud.

<div align="center">
  <img src="./resources/images/document_processing.png" alt="Document Processing" width="80%"/>
</div>

## Environment Setup

This project uses a Python environment.  You can replicate the exact environment with `pyenv` and the `venv` library (included in Python >= 3.3):

```
pyenv install 3.13.3
pyenv local 3.13.3
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Documents - Generate Sample Documents For This Project

This project requires a set of documents with known values. In this scenario, vendors send invoices to customers for services rendered. The dataset also includes anomalous documents with varying degrees of format changes, which could potentially indicate fraud. These documents were generated using the Gemini family of generative AI models hosted on Vertex AI. To understand how these documents were created, refer to the process outlined in [0-generate-documents.ipynb](./0-generate-documents.ipynb). The resulting files are located in the [./resources/documents](./resources/documents) directory. Each vendor has a dedicated folder containing the following subfolders:

-   `data`: Contains `invoices.jsonl`, which holds the actual invoice data.
-   `template`: Contains a template invoice for the vendor in `.png`, `.html`, and `.pdf` formats.
-   `invoices`: Contains generated invoices that closely follow the vendor's template in `.png` and `.pdf` formats.
-   `fake_invoices`: Contains generated invoices with slight to moderate changes from the vendor's template. These were created for the first five invoices found in the `invoices` folder.

The table below show documents for one of the vendors.  
- On the left side are real documents.  Notice the consistency in formatting as you scroll down.
- On the right side are anomalous documents. Notice the changes in layout, fonts, sizes, and colors.

<table>
    <thead>
        <tr>
            <th style="text-align: center;">Compare</th>
            <th style="text-align: center;">Real Invoices</th>
            <th style="text-align: center;">Anomalous Invoices</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Invoice 0</td>
            <td><img src="./resources/documents/vendor_0/invoices/vendor_0_invoice_0.png" alt="Invoice 0 (Real)" style="border: 3px solid green;"></td>
            <td><img src="./resources/documents/vendor_0/fake_invoices/vendor_0_invoice_0.png" alt="Invoice 0 (Anomalous)" style="border: 3px solid red;"></td>
        </tr>
        <tr>
            <td>Invoice 1</td>
            <td><img src="./resources/documents/vendor_0/invoices/vendor_0_invoice_1.png" alt="Invoice 1 (Real)" style="border: 3px solid green;"></td>
            <td><img src="./resources/documents/vendor_0/fake_invoices/vendor_0_invoice_1.png" alt="Invoice 1 (Anomalous)" style="border: 3px solid red;"></td>
        </tr>
        <tr>
            <td>Invoice 2</td>
            <td><img src="./resources/documents/vendor_0/invoices/vendor_0_invoice_2.png" alt="Invoice 2 (Real)" style="border: 3px solid green;"></td>
            <td><img src="./resources/documents/vendor_0/fake_invoices/vendor_0_invoice_2.png" alt="Invoice 2 (Anomalous)" style="border: 3px solid red;"></td>
        </tr>
        <tr>
            <td>Invoice 3</td>
            <td><img src="./resources/documents/vendor_0/invoices/vendor_0_invoice_3.png" alt="Invoice 3 (Real)" style="border: 3px solid green;"></td>
            <td><img src="./resources/documents/vendor_0/fake_invoices/vendor_0_invoice_3.png" alt="Invoice 3 (Anomalous)" style="border: 3px solid red;"></td>
        </tr>
        <tr>
            <td>Invoice 4</td>
            <td><img src="./resources/documents/vendor_0/invoices/vendor_0_invoice_4.png" alt="Invoice 4 (Real)" style="border: 3px solid green;"></td>
            <td><img src="./resources/documents/vendor_0/fake_invoices/vendor_0_invoice_4.png" alt="Invoice 4 (Anomalous)" style="border: 3px solid red;"></td>
        </tr>
        <tr>
            <td>Invoice 5</td>
            <td><img src="./resources/documents/vendor_0/invoices/vendor_0_invoice_5.png" alt="Invoice 4 (Real)" style="border: 3px solid green;"></td>
            <td><img src="./resources/documents/vendor_0/fake_invoices/vendor_0_invoice_5.png" alt="Invoice 4 (Anomalous)" style="border: 3px solid red;"></td>
        </tr>
        <tr>
            <td>Invoice 6</td>
            <td><img src="./resources/documents/vendor_0/invoices/vendor_0_invoice_6.png" alt="Invoice 4 (Real)" style="border: 3px solid green;"></td>
            <td><img src="./resources/documents/vendor_0/fake_invoices/vendor_0_invoice_6.png" alt="Invoice 4 (Anomalous)" style="border: 3px solid red;"></td>
        </tr>
        <tr>
            <td>Invoice 7</td>
            <td><img src="./resources/documents/vendor_0/invoices/vendor_0_invoice_7.png" alt="Invoice 4 (Real)" style="border: 3px solid green;"></td>
            <td><img src="./resources/documents/vendor_0/fake_invoices/vendor_0_invoice_7.png" alt="Invoice 4 (Anomalous)" style="border: 3px solid red;"></td>
        </tr>
        <tr>
            <td>Invoice 8</td>
            <td><img src="./resources/documents/vendor_0/invoices/vendor_0_invoice_8.png" alt="Invoice 4 (Real)" style="border: 3px solid green;"></td>
            <td><img src="./resources/documents/vendor_0/fake_invoices/vendor_0_invoice_8.png" alt="Invoice 4 (Anomalous)" style="border: 3px solid red;"></td>
        </tr>
        <tr>
            <td>Invoice 9</td>
            <td><img src="./resources/documents/vendor_0/invoices/vendor_0_invoice_9.png" alt="Invoice 4 (Real)" style="border: 3px solid green;"></td>
            <td><img src="./resources/documents/vendor_0/fake_invoices/vendor_0_invoice_9.png" alt="Invoice 4 (Anomalous)" style="border: 3px solid red;"></td>
        </tr>
        <tr>
            <td>Invoice 10</td>
            <td><img src="./resources/documents/vendor_0/invoices/vendor_0_invoice_10.png" alt="Invoice 4 (Real)" style="border: 3px solid green;"></td>
            <td><img src="./resources/documents/vendor_0/fake_invoices/vendor_0_invoice_10.png" alt="Invoice 4 (Anomalous)" style="border: 3px solid red;"></td>
        </tr>
    </tbody>
</table>

## Extractor - Create Custom Data Extractors With Document AI

When a document, such as an invoice, arrives, it is often in the form of an image. To make this document useful for processing, essential information must be extracted. In some cases, this might be as simple as identifying the vendor's name to route the document to the appropriate review queue. In other cases, more detailed information is needed, including repeating data like invoice line items and their associated elements, such as SKU, description, price, and quantity. This is where the [Document AI Custom Extractor](https://cloud.google.com/document-ai/docs/custom-extractor-overview) is valuable. In this project, we will leverage the [Custom extractor with generative AI](https://cloud.google.com/document-ai/docs/ce-with-genai) version to ensure a simple and effective process across the variety of invoice formats, which can vary significantly from vendor to vendor.

> Document AI offers a range of parsers for various tasks, including [OCR](https://cloud.google.com/document-ai/docs/enterprise-document-ocr), general form extraction with the [Form Parser](https://cloud.google.com/document-ai/docs/form-parser), and document preparation for generative AI retrieval pipelines using the [Layout Parser](https://cloud.google.com/document-ai/docs/layout-parse-chunk).

Setting up the `Custom extractor with generative AI` is an interactive process with many automated features available directly in the Google Cloud Console. The resulting parser can be accessed via REST, gRPC, and numerous client libraries - [reference](https://cloud.google.com/document-ai/docs/reference). The console-based workflow and client usage with Python are detailed step-by-step in the included workflow [1-custom-extractor.ipynb](./1-custom-extractor.ipynb). This workflow shows how to:
- Create a zero-shot parser with just a schema and a few test documents to evaluate
- Create a few-shot parser with a sample of training documents
- Create a fine-tuned parser with a larger sample of training documents
- Use each parser version to serve online extractions from documents
- Show how to move a custom parser between projects

---

<div align="center">Point of Progress</div>

---

## Extraction - Prepare Document Extractions
[2-document-extraction.ipynb](./2-document-extraction.ipynb)

## Embedded Representation - Generate Embedding For Documents
[3-document-embedding.ipynb](./3-document-embedding.ipynb)

## Document Similarity With Embeddings
[4-document-similarity.ipynb](./4-document-similarity.ipynb)

## Anomaly Detection With Document Similarity
[5-document-anomalies.ipynb](./5-document-anomalies.ipynb)

## Document Comparison For Automated Descriptive Differences
[6-document-comparison.ipynb](./6-document-comparison.ipynb)

## Building An Agent For Fraud Analyst



