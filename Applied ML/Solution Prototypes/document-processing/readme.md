![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FSolution+Prototypes%2Fdocument-processing&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/document-processing/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Document Processing With Generative AI: Parse, Extract, Validate Authenticity, and More
> You are here `vertex-ai-mlops/Applied ML/Solution Prototypes/document-processing/readme.md`

A common scenario for companies is receiving documents, like invoices, with variable formats and needing to extract information into a structured form. Compounding this is the need to verify document authenticity and detect fraud, creating a full-scale document processing challenge.

This prototype focuses on a fast-to-create and easy-to-scale solution for both document extraction and verification, initially without any custom ML. This allows for rapid deployment and validation of the core workflow before investing in more complex, custom models. It establishes a robust foundation for expanding the approach to fraud detection with customized models and other ML-based approaches as needed.

To start, we will establish a core workflow for ingesting documents into Google Cloud services. This workflow will extract information and compare documents to previous ones, assessing the likelihood of anomalies that may indicate potential fraud.

<div align="center">
  <img src="./resources/images/document_processing.png" alt="Document Processing" width="80%"/>
</div>

---

## Environment Setup

This project uses a Python environment.  You can replicate the exact environment with `pyenv` and the `venv` library (included in Python >= 3.3):

```
pyenv install 3.13.3
pyenv local 3.13.3
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## Documents - Generate Sample Documents For This Project

This project requires a set of documents with known values. In this scenario, vendors send invoices to customers for services rendered. The dataset also includes anomalous documents with varying degrees of format changes, which could potentially indicate fraud. These documents were generated using the Gemini family of generative AI models hosted on Vertex AI. To understand how these documents were created, refer to the process outlined in [0-generate-documents.ipynb](./0-generate-documents.ipynb). The resulting files are located in the [./resources/documents](./resources/documents) directory. Each vendor has a dedicated folder containing the following subfolders:

-   `data`: Contains `invoices.jsonl`, which holds the actual invoice data.
-   `template`: Contains a template invoice for the vendor in `.png`, `.html`, and `.pdf` formats.
-   `invoices`: Contains generated invoices that closely follow the vendor's template in `.png` and `.pdf` formats.
-   `fake_invoices`: Contains generated invoices with slight to moderate changes from the vendor's template. These were created for the first five invoices found in the `invoices` folder.

**Workflow**
- [0-generate-documents.ipynb](./0-generate-documents.ipynb)

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

---

## Step 1: Extractor - Create Custom Data Extractors With Document AI

When a document, such as an invoice, arrives, it is often in the form of an image. To make this document useful for processing, essential information must be extracted. In some cases, this might be as simple as identifying the vendor's name to route the document to the appropriate review queue. In other cases, more detailed information is needed, including repeating data like invoice line items and their associated elements, such as SKU, description, price, and quantity. This is where the [Document AI Custom Extractor](https://cloud.google.com/document-ai/docs/custom-extractor-overview) is valuable. In this project, we will leverage the [Custom extractor with generative AI](https://cloud.google.com/document-ai/docs/ce-with-genai) version to ensure a simple and effective process across the variety of invoice formats, which can vary significantly from vendor to vendor.

> Document AI offers a range of parsers for various tasks, including [OCR](https://cloud.google.com/document-ai/docs/enterprise-document-ocr), general form extraction with the [Form Parser](https://cloud.google.com/document-ai/docs/form-parser), and document preparation for generative AI retrieval pipelines using the [Layout Parser](https://cloud.google.com/document-ai/docs/layout-parse-chunk).

Setting up the `Custom extractor with generative AI` is an interactive process with many automated features available directly in the Google Cloud Console. The resulting parser can be accessed via REST, gRPC, and numerous client libraries - [reference](https://cloud.google.com/document-ai/docs/reference). The console-based workflow and client usage with Python are detailed step-by-step in the included workflow [1-custom-extractor.ipynb](./1-custom-extractor.ipynb). This workflow shows how to:
- Create a zero-shot parser with just a schema and a few test documents to evaluate
- Create a few-shot parser with a sample of training documents
- Create a fine-tuned parser with a larger sample of training documents
- Use each parser version to serve online extractions from documents
- Show how to move a custom parser between projects

**Workflow**
- [1-custom-extractor.ipynb](./1-custom-extractor.ipynb)

---

## Step 2: Extraction - Prepare Document Extractions

This section of the workflow applies the custom extractor to the documents. It begins by reviewing methods for processing documents with the Document AI client using the custom parser:

-   **Online Processing of Individual Documents:**
    -   This can be done as documents arrive in real-time, as byte objects, or after they are stored in Google Cloud Storage.
-   **Batch Processing of Multiple Files:**
    -   This is ideal for processing batches of many files already stored in Google Cloud Storage.

Since this workflow requires the documents later for anomaly detection and comparison, the documents are first moved to Google Cloud Storage. As information is extracted from the documents, it needs to be stored. Google Cloud BigQuery manages both the documents and all the extracted information in this workflow. This is enabled by BigQuery's object tables feature, which provides read-only tables over unstructured data in Google Cloud Storage.

This workflow establishes the complete BigQuery setup, including directly processing all documents from a single SQL query using the `ML.PROCESS_DOCUMENT` function. This function provides direct access to the custom extractor created with Document AI.

**Workflow**
- [2-document-extraction.ipynb](./2-document-extraction.ipynb)

---

## Step 3: Embedded Representations: Generating Embeddings for Documents

Now that we have BigQuery tables linking to the documents and their extracted information, we can enhance our understanding of these documents.

One effective way to represent information is by using an **embedding model**. These models are trained to create dense vector representations, known as embeddings. An embedding is essentially a vector of floating-point numbers, such as `[-0.06302902102470398, 0.00928034819662571, 0.014716853387653828, -0.028747491538524628, ...]`. These embeddings are incredibly useful for various tasks, including:
-   **Similarity Search:** Finding and ranking similar content.
-   **Classification:** Categorizing content based on similarity.
-   **Clustering:** Grouping objects with similar attributes.
-   **Anomaly Detection:** Identifying outliers or mismatched objects.
-   **Contextual Sorting:** Ordering content based on its context.
-   **And More:** Embeddings have a wide range of applications.

Google Cloud's Vertex AI platform offers several embedding models as a service, ideal for both text and multimodal data (images, video, audio, and text). Vertex AI simplifies the use of these models through APIs and various client libraries, including Python.
-   [Vertex AI Embeddings APIs Overview](https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings)

BigQuery also integrates these Vertex AI embedding models directly with the `ML.GENERATE_EMBEDDING` function. This allows us to enrich the data in BigQuery with embeddings of the source content stored in Google Cloud Storage, accessible through the object table we created.
-   [BigQuery ML.GENERATE_EMBEDDING function](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-embedding)


**Workflow**
- [3-document-embedding.ipynb](./3-document-embedding.ipynb)

---

## Step 4: Document Similarity With Embeddings

The embedded representation of the documents created in the previous section can be used to calculate a mathematical distance between documents which serves as a similarity measure.  The closer documents are the more similar they are.  This can be done directly within BigQuery with the `VECTOR_SEARCH` function.  This workflow also shows how to use a re-dimensionalization technique, PCA, to represent the embeddings in 2 dimensions for vizualizing the relationships between documents and vendors.

**Workflow**
- [4-document-similarity.ipynb](./4-document-similarity.ipynb)

---

<div align="center">Point of Completed Progress</div>

---

---

## Step 5: Anomaly Detection With Document Similarity

**Workflow**
- [5-document-anomalies.ipynb](./5-document-anomalies.ipynb)

---

## Step 6: Document Comparison For Automated Descriptive Differences

**Workflow**
- [6-document-comparison.ipynb](./6-document-comparison.ipynb)

---

## Step 7: Building An Agent For Fraud Analyst


--- 

ToDo list:
- Create links to next section at the bottom of each workflow
