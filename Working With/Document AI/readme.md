![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FWorking+With%2FDocument+AI&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Working%20With/Document%20AI/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# vertex-ai-mlops/Working With/Document AI/readme.md

Working With [DocumentAI](https://cloud.google.com/document-ai/docs/overview) to extract information from documents as part of ML focused workflows.

## How does it work?

Document AI is an API where you interact with processors to extract information from documents.

You enable the API, create an instance of a processor in your project, send in document(s), receive back JSON with the extracted information:

<p align="center" width="100%"><center>
    <img src="../../architectures/architectures/images/working with/documentai/readme/high_level.png">
</center></p>

## Details

**Documents**
- [Document Types](https://cloud.google.com/document-ai/docs/file-types) like pdf, gif, tiff, jpeg, pn, gmp, webp
    - [More detail on supported document types](https://cloud.google.com/document-ai/docs/enterprise-document-ocr#supported_file_formats).

**Clients**
- Clients For Processing: [list of clients](https://cloud.google.com/document-ai/docs/libraries), [REST](https://cloud.google.com/document-ai/docs/reference/rest), [RPC](https://cloud.google.com/document-ai/docs/reference/rpc)
    - [Online](https://cloud.google.com/document-ai/docs/send-request#online-process)
        - Sync and Async Clients available
    - [Batch](https://cloud.google.com/document-ai/docs/send-request#batch-process)
        - Sync and Async Clients available

**Processors**

<table style='text-align:left;vertical-align:middle;border:1px solid black' width="90%" cellpadding="1" cellspacing="0">
    <caption>Processors</caption>
<!--.....................................................................................................................................................................-->
    <col>
    <col>
    <col>
    <colgroup span="8"></colgroup>
    <col>
<!--.....................................................................................................................................................................-->
    <thead>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <th rowspan="2" scope="col">Processor</th>
            <th rowspan="2" scope="col">Parser</th>
            <th rowspan="2" scope="col">Description</th>
            <th colspan="8" scope="colgroup">Extractions</th>
            <th rowspan="2" scope="col">Notes</th>
        </tr>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <th scope="col">Block</th>
            <th scope="col">Paragraph</th>
            <th scope="col">Line</th>
            <th scope="col">Token</th>
            <th scope="col">Symbol</th>
            <th scope="col">Tables</th>
            <th scope="col">Form Fields</th>
            <th scope="col">Entities</th>
        </tr>
    </thead>
    <tbody>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td rowspan="4" scope="rowgroup"><a href = "https://cloud.google.com/document-ai/docs/processors-list#general_processors" target="_blank">General</a></td>
            <td><a href = "https://cloud.google.com/document-ai/docs/enterprise-document-ocr" target="_blank">OCR</a></td>
            <td>Print and handwriting with language detection</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>No</td>
            <td>No</td>
            <td><a href = "https://cloud.google.com/document-ai/docs/process-documents-ocr#image-quality_analysis" target="_blank">Quality Scores</a></td>
            <td>
                <ul>
                <li><a href = "https://cloud.google.com/document-ai/docs/process-documents-ocr#enable-configurations" target="_blank">Configurations</a></li>
                <li><a href = "https://cloud.google.com/document-ai/docs/process-documents-ocr#ocr_add_ons" target="_blank">Add Ons</a></li>
                </ul>
            </td>
        </tr>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td><a href = "https://cloud.google.com/document-ai/docs/form-parser" target="_blank">Form</a></td>
            <td>OCR +</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>No</td>
            <td>Yes</td>
            <td>Yes</td>
            <td><a href = "https://cloud.google.com/document-ai/docs/form-parser#data-extraction_features" target = "_blank">Generic Entities</a></td>
            <td></td>
        </tr>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td><a href = "https://cloud.google.com/document-ai/docs/processors-list#processor_doc-quality-processor" target="_blank">Document Quality</a></td>
            <td>Assess Document Quality</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>No</td>
            <td>No</td>
            <td>No</td>
            <td>Quality Scores</td>
            <td></td>
        </tr>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td><a href = "https://cloud.google.com/document-ai/docs/processors-list#processor_doc-splitter" target="_blank">Document Splitter</a></td>
            <td>Detect document splits</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>No</td>
            <td>No</td>
            <td>No</td>
            <td>Document Splits</td>
            <td></td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td rowspan="2" scope="rowgroup"><a href = "https://cloud.google.com/document-ai/docs/processors-list#specialized_processors" target="_blank">Specialized</a></td>
            <td><a href = "https://cloud.google.com/document-ai/docs/processors-list#processor_invoice-processor" target="_blank">Invoice</a></td>
            <td></td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>No</td>
            <td>No</td>
            <td>No</td>
            <td>
                Pre-trained
                <BR><a href="https://cloud.google.com/document-ai/docs/workbench/uptrain-processor" target="_blank">Uptrained</a>
            </td>
            <td></td>
        </tr>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td><a href = "https://cloud.google.com/document-ai/docs/processors-list#specialized_processors" target="_blank">Many More</a></td>
            <td rowspan="1" colspan="8" style='text-align:left;vertical-align:middle'>
                <b>Identity Parsers:</b> US Passport, US Driver License, France Passport, France Driver License, ...
                <br><b>Lending Parsers:</b> Mortgage, Lending, Pay Slip, 1003, 1040, 1099-DIV, 1099-INT, Bank Statement, ...
                <br><b>Procurement Parsers:</b> Invoice, Expense, Ultility, ...
                <br><b>Contract Parser</b>
            </td>
            <td>Pre-trained<BR>Uptrained</td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td rowspan="4" scope="rowgroup"><a href = "https://cloud.google.com/document-ai/docs/processors-list#custom_processors" target="_blank">Custom</a></td>
            <td><a href = "https://cloud.google.com/document-ai/docs/processors-list#processor_cde" target="_blank">Document Extractor</a></td>
            <td></td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>No</td>
            <td>No</td>
            <td>No</td>
            <td>Custom</td>
            <td><a href="https://cloud.google.com/document-ai/docs/workbench/build-custom-processor" target="_blank">Documentation Tutorial</a></td>
        </tr>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td><a href = "https://cloud.google.com/document-ai/docs/processors-list#processor_CUSTOM_CLASSIFICATION_PROCESSOR" target="_blank">Document Classifier</a></td>
            <td></td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>No</td>
            <td>No</td>
            <td>No</td>
            <td>Custom</td>
            <td><a href="https://cloud.google.com/document-ai/docs/workbench/build-custom-classification-processor" target="_blank">Documentation Tutorial</a></td>
        </tr>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td><a href = "https://cloud.google.com/document-ai/docs/processors-list#processor_CUSTOM_SPLITTING_PROCESSOR" target="_blank">Document Splitter</a></td>
            <td></td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>No</td>
            <td>No</td>
            <td>No</td>
            <td>Custom</td>
            <td><a href="https://cloud.google.com/document-ai/docs/workbench/build-custom-splitter-processor" target="_blank">Documentation Tutorial</a></td>
        </tr>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td><a href = "https://cloud.google.com/document-ai/docs/processors-list#processor_SUMMARIZER" target="_blank">Summarizer</a></td>
            <td></td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>Yes</td>
            <td>No</td>
            <td>No</td>
            <td>No</td>
            <td>Summary</td>
            <td><a href="https://cloud.google.com/document-ai/docs/workbench/build-summarizer-processor" target="_blank">Documentation Tutorial</a></td>
        </tr>
<!--.....................................................................................................................................................................-->
    </tbody>
</table>

---
## Notebook Workflows

**Processing Details**
- [Document AI - Process Documents](./Document%20AI%20-%20Process%20Documents.ipynb)
    - How to process 1 or many documents
    - Examples of Batch and Online Processing
    - Async Processing
    - Storing results in GCS and/or BigQuery
    - Recalling results from GCS and/or BigQuery
- [Document AI - Process Responses](./Document%20AI%20-%20Process%20Responses.ipynb)
    - Extracting elements from the JSON in Python or in BigQuery with SQL
    - Treating elements like geographies for advanced extraction techniques
- [Document AI - BigQuery Response Processing](./Document%20AI%20-%20BigQuery%20Response%20Processing.ipynb)
    - A deeper workflow for storing response in BigQuery and using SQL to extract parts of the response
    - Advanced techniques like using geospatial functions for clustering tokens to create custom groupings on pages
- [Document AI - From BigQuery](./Document%20AI%20-%20From%20BigQuery.ipynb)
    - Process using BigQuery ML With ML.PROCESS_DOCUMENT function
    - Given a table of GCS URI's for documents this function processes and returns responses from Document AI
    - Uses Online Processing and has the same limits for page size
    - This workflow covers processing document and responses - all from BigQuery
    - Only entities are returned from the Document AI responses - not pages

**Parser/Processor Examples**
- [Document AI - Process Responses](./Document%20AI%20-%20Process%20Responses.ipynb)
    - OCR parser with:
        - Symbol configuration
        - Image Quality scores
        - Style info (font types, sizes, and more) Add On
- [Document AI Processors - OCR Parser With Math Type](./Document%20AI%20Processors%20-%20OCR%20Parser%20With%20Math%20Type.ipynb)
    - OCR parser with Symbol Configuration and Math OCR Add On
    - Detect Math Type and extract to LaTeX
- [Document AI Processors - Form Parser](./Document%20AI%20Processors%20-%20Form%20Parser.ipynb)
    - OCR (without Add Ons and Symbol configuration)
    - Form Fields
    - Tables
    - General Entities
- [Document AI Processors - Document Summarizer](./Document%20AI%20Processors%20-%20Document%20Summarizer.ipynb)
    - Get a full document summary produced by generative AI
- Specialized Processors:
    - [Document AI Processors - Invoice Parser](./Document%20AI%20Processors%20-%20Invoice%20Parser.ipynb)
        - OCR (without Add ons and Symbol configuration)
        - Invoice specific entities detected

---
## Inputs & Outputs

The following table breaks down the input and output locations by the type of processing.  This uses the [Python Client for Document AI](https://cloud.google.com/python/docs/reference/documentai/latest) for examples:

<table style='text-align:center;vertical-align:middle;border:1px solid black' width="90%" cellpadding="1" cellspacing="0">
    <caption>Inputs & Outputs</caption>
    <col>
    <col>
    <col>
<!--..........................................................................................-->
    <thead>
        <tr>
            <th scope="col" style="width:20%">
                Processing Mode
            </th>
            <th scope="col" style="width:40%">
                Inputs
            </th>
            <th scope="col" style="width:40%">
                Outputs
            </th>
        </tr>
    </thead>
    <tbody>
<!--..........................................................................................-->
        <tr>
            <td>
                Online<br>(Single Document Per Request)
            </td>
            <td>
                <table>
                    <tr style='text-align:center'>
                        <td>One of:</td>
                    </tr>
                    <tr style='text-align:left'>
                        <td>Document in GCS:</td>
                    </tr>
                    <tr style='text-align:left'>
                        <td>
                        <pre>
response = doc_ai.process_document(
    request = documentai.types.ProcessRequest(
        <b>inline_document</b> = documentai.types.Document(
            uri = 'gs://bucket/path/to/object.ext'
        )
    )
)
                        </pre>
                        </td>
                    </tr>
                    <tr style='text-align:left'>
                        <td>Document as bytes</td>
                    </tr>
                    <tr style='text-align:left'>
                        <td>
                        <pre>
response = doc_ai.process_document(
    request = documentai.types.ProcessRequest(
        # provide a bytes object
        <b>raw_document</b> = documentai.types.RawDocument(
            content = 
        )
    )
)
                        </pre>
                        </td>
                    </tr>
                    <tr style='text-align:left'>
                        <td>Document in GCS</td>
                    </tr>
                    <tr style='text-align:left'>
                        <td>
                        <pre>
response = doc_ai.process_document(
    request = documentai.types.ProcessRequest(
        # provide GCS URI as string
        <b>gcs_document</b> = documentai.types.GcsDocument(
            gcs_uri = 'gs://bucket/path/to/object'
        )
    )
)
                        </pre>
                        </td>
                    </tr>
                </table>
            </td>
            <td  style='text-align:left'>
                The response is an object containing the document response.
                <br><pre>type(response) is documentai.types.ProcessResponse()</pre>
                <br><br>This has a parameter with the document:
                <br><pre>type(response.document) is documentai.types.Document()</pre>
                <br><br>The document object contains parameters with document components, like:
                <ul>
                    <li>response.document.text is a string with full text of the document</li>
                    <li>response.document.pages is a list of documentai.types.Document.Pagee objects</li>
                    <li>response.document.entities is a list of documentai.types.Document.Entity objects</li>
                </ul>
                <br>The document object contains method for converting to Python objects:
                <ul>
                    <li>response.document.to_dict() for dictionary</li>
                    <li>response.document.to_json() for JSON</li>
                </ul>
            </td>
        </tr>
<!--..........................................................................................-->
        <tr>
            <td>
                Batch<br>(Multiple Documents Per Request)
            </td>
            <td>
                <table>
                    <tr style='text-align:center'>
                        <td>One of:</td>
                    </tr>
                    <tr style='text-align:left'>
                        <td>List of documents in GCS:</td>
                    </tr>
                    <tr style='text-align:left'>
                        <td>
                <pre>
doc_ai.batch_process_documents(
    request = documentai.types.BatchProcessRequest(
        <b>input_documents</b> = documentai.types.BatchDOcumentsInputConfig(
            # provide a list of document objects that each have parameter gcs_uri = GCS URI as string
            <b>gcs_documents</b> = documentai.types.GcsDocuments(
                gcs_uri = [documentai.types.GcsDocument(gcs_uri = ), ...]
            )
        )
    )
)
                </pre>
                        </td>
                    </tr>
                    <tr style='text-align:left'>
                        <td>All documents with GCS prefix:</td>
                    </tr>
                    <tr style='text-align:left'>
                        <td>
                            <pre>
doc_ai.batch_process_documents(
    request = documentai.types.BatchProcessRequest(
        <b>input_documents</b> = documentai.types.BatchDocumentsInputConfig(
            # provide a GCS URI (prefix) as string
            <b>gcs_prefix</b> = documentai.types.GcsPrefix(
                gcs_uri_prefix = 
            )
        )
    )
)
                            </pre>
                        </td>
                    </tr>
                </table>
            </td>
            <td style='text-align:left'>
                The batch processing job includes a parameter for configuring the output location of JSON files in GCS.<br><br>
                <pre>
doc_ai.batch_process_documents(
    request = documentai.BatchProcessRequest(
       <b>document_output_config</b> = documentai.types.DocumentOutputConfig(
            <b>gcs_output_config</b> = documentai.types.GcsOutputConfig(
                gcs_uri = 'gs://bucket/path/to/output', # the output JSON will writen to this directory
                field_mask = , # optional: fields to include in output
                sharding_config = # optional: sharding config for output
            )
        )
    )
)
                </pre>
            </td>
        </tr>     
<!--..........................................................................................-->
    </tbody>
</table>

---
## Understanding Responses

The response is a JSON structure that contains all the extracted information.  

- Handling responses: [Reference](https://cloud.google.com/document-ai/docs/handle-response)
- Example output: [Reference](https://cloud.google.com/document-ai/docs/output)


<table style='text-align:left;vertical-align:middle;border:1px solid black' width="90%" cellpadding="1" cellspacing="0">
    <caption>Responses</caption>
<!--.....................................................................................................................................................................-->
    <col>
    <col>
<!--.....................................................................................................................................................................-->
    <thead>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <th scope="col">Element</th>
            <th scope="col">Structure</th>
        </tr>
    </thead>
    <tbody>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document</td>
            <td>
                <pre>
<b>document</b>
    - uri: string
    - mimeType: string
    - text: string
    - pages: list
        - pageNumber: int
        - dimension:
            - width: float
            - height: float
            - unit: string
        - layout: 
            - textAnchor
                - textSegments: list
                    - startIndex: string
                    - endIndex: float
            - boundingPoly
                - vertices: list
                    - x: int
                    - y: int
                - normalizedVertices: list
                    - x: float
                    - y: float
            - orientation: string
        - detectedLanguages: list
            - languageCode: string
        <b>- blocks: list
        - paragraphs: list
        - lines: list
        - tokens: list
        - symbols: list
        - tables: list
        - formFields: list
        - image: list
        - imageQualityScores:
        - visualElements: list
    - entities: list</b>
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:pages:blocks</td>
            <td>
                <pre>
<b>- blocks: list</b>
    - layout:
        - textAnchor:
            - textSegments: list
                - startIndex: string
                - endIndex: string
        - confidence: float
        - boundingPoly:
            - vertices: list
                - x: int
                - y: int
            - normalizedVertices: list
                - x: float
                - y: float
        - orientation: string    
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:pages:paragraphs</td>
            <td>
                <pre>
<b>- paragraphs: list</b>
    - layout:
        - textAnchor:
            - textSegments: list
                - startIndex: string
                - endIndex: string
        - confidence: float
        - boundingPoly:
            - vertices: list
                - x: int
                - y: int
            - normalizedVertices: list
                - x: float
                - y: float
        - orientation: string    
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:pages:lines</td>
            <td>
                <pre>
<b>- lines: list</b>
    - layout:
        - textAnchor:
            - textSegments: list
                - startIndex: string
                - endIndex: string
        - confidence: float
        - boundingPoly:
            - vertices: list
                - x: int
                - y: int
            - normalizedVertices: list
                - x: float
                - y: float
        - orientation: string
        - detectedLanguages: list
            - languageCode: string  
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:pages:tokens</td>
            <td>
                <pre>
<b>- tokens: list</b>
    - layout:
        - textAnchor:
            - textSegments: list
                - startIndex: string
                - endIndex: string
        - confidence: float
        - boundingPoly:
            - vertices: list
                - x: int
                - y: int
            - normalizedVertices: list
                - x: float
                - y: float
        - orientation: string
        - detectedBreak: 
            - type: string
        - detectedLanguages: list
            - languageCode: string   
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:pages:tokens
                <ul>
                    <li>Add On: Font Style detection for OCR Parser</li>
                </ul>
            </td>
            <td>
                <pre>
<b>- tokens: list</b>
    - layout:   
        - styleInfo:
            - fontSize: int
            - pixelFontSize: int
            - fontType: string
            - bold: bool
            - fontWeight: int
            - textColor:
                - red: float
                - green: float
                - blue: float
            - backgroundColor:
                -red: float
                - green: float
                - blue: float
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:pages:symbols
                <ul>
                    <li>OCR Parser Includes Symbols (characters, spaces)</li>
                </ul>
            </td>
            <td>
                <pre>
<b>- symbols: list</b>
    - layout:
        - textAnchor:
            - textSegments: list
                - startIndex: string
                - endIndex: string
        - confidence: float
        - boundingPoly:
            - normalizedVertices: list
                - x: float
                - y: float
        - orientation: string     
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:pages:tables
                <ul>
                    <li>Form Parser Includes Table Parsing</li>
                </ul>
            </td>
            <td>
                <pre>
<b>- tables: list</b>
    - layout:
        - textAnchor:
            - textSegments: list
                - startIndex: string
                - endIndex: string
        - confidence: float
        - boundingPoly:
            - vertices: list
                - x: int
                - y: int
            - normalizedVertices: list
                - x: float
                - y: float
        - orientation: string
        - headerRows: list
            - cells: list
                - layout:
                    - textAnchor:
                        - textSegments: list
                            - startIndex: string
                            - endIndex: string
                    - confidence: float
                    - boundingPoly:
                        - normalizedVertices: list
                            - x: float
                            - y: float
                    - orientation: string
                - rowSpan: int
                - colSpan: int
        - bodyRows: list
            - cells: list
                - layout:
                    - textAnchor:
                        - textSegments: list
                            - startIndex: string
                            - endIndex: string
                    - confidence: float
                    - boundingPoly:
                        - normalizedVertices: list
                            - x: float
                            - y: float
                    - orientation: string
                - rowSpan: int
                - colSpan: int    
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:pages:formFields
                <ul>
                    <li>Form Parser Includes Form Field Detection</li>
                </ul>
            </td>
            <td>
                <pre>
    - fieldName:
        - textAnchor:
            - textSegments: list
                - startIndex: string
                - endIndex: string
            - content
        - confidence: float
        - boundingPoly:
            - normalizedVertices: list
                - x: float
                - y: float
        - orientation: string
    - fieldValue:
        - textAnchor:
            - textSegments: list
                - startIndex: string
                - endIndex: string
            - content: string
        - confidence: float
        - boundingPoly:
            - normalizedVertices: list
                - x: float
                - y: float
        - orientation: string     
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>
                Document:pages:visualElements
                <ul>
                    <li>Add On: Checkbox Extraction With OCR Parser</li>
                    <li>Add On: Math Text With OCR Parser</li>
                </ul>
            </td>
            <td>
                <pre>
- visualElements: list 
    - layout:
        - confidence: float
        - boundingPoly:
            - vertices:
                - x: int
                - y: int
            - normalizedVertices:
                - x: float
                - y: float
        - type: string like ["unfilled_checkbox", "filled_checkbox", "math_formula"]
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>
                Document:pages:image
                <ul>
                    <li>All Parsers Includes Base64 encoding of page images: image</li>
                </ul>
            </td>
            <td>
                <pre>
- image: 
    - content: base64 string
    - mimeType: string
    - width: int
    - height: int
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>
                Document:pages:imageQualityScores
                <ul>
                    <li>OCR Parser Includes Quality score: imageQualityScores</li>
                </ul>
            </td>
            <td>
                <pre>
- imageQualityScores:
    - qualityScore: float
    - detectedDefects: list
        - type: string
        - confidence: float
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:entities
                <ul>
                    <li>OCR Parser Includes type: quality_score</li>
                    <li>Intelligent Document Quality Parser Includes tyes: quality_score</li>
                </ul>
            </td>
            <td>
                <pre>
- entities: list
    <b>- type: "quality_score"</b>
    - confidence: float
    - pageAnchor:
        - pageRefs: list
            - page: string
    - properties: list
        - type: string = "quality/defect_[document_cutoff, glare, text_cutoff]"
        - confidence: float
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:entities
                <ul>
                    <li>Form Parser Has Generic Entity Detection</li>
                </ul>
            </td>
            <td>
                <pre>
- entities: list
    <b>- type: "generic_entities"</b>
        - pageAnchor:
            -pageRefs: list
                - 
        - properties: list
            - textAnchor:
                - textSegments: list
                    - startIndex: string
                    - endIndex: string
            - type: string
            - mentionText: string
            - confidence: string
            - pageAnchor:
                - pageRefs: list
                    - boundingPoly: 
                        - normalizedVertices: list
                            - x: float
                            - y: float
            - id: string
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:entities
                <ul>
                    <li>Summarizer Parser</li>
                </ul>
            </td>
            <td>
                <pre>
- entities: list
    <b>- type: "summary"</b>
    - mentionText: string
    - normalizedValue:
        - text: string
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:entities
                <ul>
                    <li>Custom Document Splitter</li>
                    <li>Document Splitter</li>
                </ul>
            </td>
            <td>
                <pre>
- entities: list
    - textAnchor:
        - textSegments: list
            - startIndex: string
            - endIndex: string
    - type: string
    - confidence: float
    - pageAnchor:
        - pageRefs: list
            - page: string
            - confidence: float
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:entities
                <ul>
                    <li>Custom Document Classifier</li>
                </ul>
            </td>
            <td>
                <pre>
- entities: list
    - type: string
    - confidence: float
    - id: string
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:entities
                <ul>
                    <li>Custom Document Extractor</li>
                </ul>
            </td>
            <td>
                <pre>
- entities: list
    - textAnchor:
        - textSegments: list
            - startIndex: string
            - endIndex: string
        - content: string
        - type: string
        - mentionText: string
        - confidence: float
        - pageAnchor:
            - pageRefs: list
                - boundingPoly:
                    - normalizedVertices: list
                        - x: float
                        - y: float
        - id: string
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:entities
                <ul>
                    <li>Specialized Parsers Include Entities</li>
                </ul>
            </td>
            <td>
                <pre>
- entities: list
    - textAnchor:
        - textSegments: list
            - startIndex: string
            - endIndex: string
        - content: string # may be missing - see properties
    - type: string
    - mentionText: string
    - confidence: float
    - pageAnchor:
        - pageRefs: list
            - boundingPoly:
                - normalizedVertices: list
                    - x: float
                    - y: float
    - id: string
    - normalizedValue: # if textAnchor:content is not missing
        - text: string
        - dateValue:
            - year: int
            - month: int
            - day: int
    - properties: list # if textAnchor:content is missing
        - textAnchor:
            - textSegments: list
                - startIndex: string
                - endIndex: string
            - content: string
        - type: string
        - mentionText: string
        - confidence: float
        - pageAnchor:
            - pageRefs: list
                - boundingPoly:
                    - normalizedVertices: list
                        - x: float
                        - y: float
        - id: string
        - normalizedValue:
            - text: string
            - moneyValue:
                - currencyCode: string
                - units: string 
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
    </tbody>
</table>

