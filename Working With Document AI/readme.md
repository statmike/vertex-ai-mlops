![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2FWorking+With+Document+AI&dt=readme.md)

# vertex-ai-mlops/Working With Document AI/readme.md

Working With [DocumentAI](https://cloud.google.com/document-ai/docs/overview) to extract information from documents as part of ML focused workflows.

## How does it work?

Document AI is an API where you interact with processors to extract information from documents.

You enable the API, create an instance of a processor in your project, send in document(s), receive back JSON with the extracted information:

<p align="center" width="100%"><center>
    <img src="../architectures/architectures/images/working with/documentai/readme/high_level.png">
</center></p>

## Details

**Documents**
- [Document Types](https://cloud.google.com/document-ai/docs/file-types) like pdf, gif, tiff, jpeg, pn, gmp, webp

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
            <td>Quality Scores</td>
            <td></td>
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
            <td>No</td>
            <td>Generic Entities</td>
            <td></td>
        </tr>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td><a href = "https://cloud.google.com/document-ai/docs/processors-list#processor_doc-quality-processor" target="_blank">Document Quality</a></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td><a href = "https://cloud.google.com/document-ai/docs/processors-list#processor_doc-splitter" target="_blank">Document Splitter</a></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
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
            <td>Invoice</td>
            <td></td>
        </tr>
        <tr style='text-align:center;vertical-align:middle;border:1px solid black'>
            <td><a href = "https://cloud.google.com/document-ai/docs/processors-list#specialized_processors" target="_blank">Many More</a></td>
            <td rowspan="1" colspan="10">
                <b>Identity Parsers:</b> US Passport, US Driver License, France Passport, France Driver License, ...
                <br><b>Lending Parsers:</b> Mortgage, Lending, Pay Slip, 1003, 1040, 1099-DIV, 1099-INT, Bank Statement, ...
                <br><b>Procurement Parsers:</b> Invoice, Expense, Ultility, ...
                <br><b>Contract Parser</b>
            </td>
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
            <td></td>
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
            <td></td>
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
            <td></td>
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
            <td></td>
        </tr>
<!--.....................................................................................................................................................................-->
    </tbody>
</table>

- General Processors
    - [OCR Parser](https://cloud.google.com/document-ai/docs/enterprise-document-ocr)
        - print and handwriting with language detection (including hints)
        - detection regions: page, block, paragraph, line, word, symbol
        - also, math OCR to latex, checkbox with status, font style detection
    - [Form Parser](https://cloud.google.com/document-ai/docs/form-parser)
        - OCR
        - key-value pairs including custom logic
        - generic entities: email, phone, url, date_time, address, person, organization, quantity, price, id, page_number
        - tables
        - checkboxes
    - [Document Quality](https://cloud.google.com/document-ai/docs/processors-list#processor_doc-quality-processor)
        - OCR
        - Quality score between [0, 1] including quality reason if the score is < 0.5 (blurry, dark, faint, noisy, text too small
    - [Document Splitter](https://cloud.google.com/document-ai/docs/processors-list#processor_doc-splitter)
        - OCR
        - splitting, suggest page location for indicating new files
- [Specialized Processors](https://cloud.google.com/document-ai/docs/processors-list#specialized_processors)
    - Example: [Invoice Parser](https://cloud.google.com/document-ai/docs/processors-list#processor_invoice-processor)
        - OCR
        - [Fields](https://cloud.google.com/document-ai/docs/fields#processor_invoice-processor)
        - [Enriched Entity](https://cloud.google.com/document-ai/docs/ekg-enrichment#processor_invoice-processor)
        - [Uptrain Parser](https://cloud.google.com/document-ai/docs/workbench/uptrain-processor) With Your Documents
            - Better Accuracy
            - Custom Fields
    - So, Many, More!
        - Contract Parser
        - Identity Parsers: US Passport, US Driver License, France Passport, France Driver License, ...
        - Lending Parsers: Mortgage, Lending, Pay Slip, 1003, 1040, 1099-DIV, 1099-INT, Bank Statement, ...
        - Procurement Parsers: Invoice, Expense, Ultility, ...
- [Custom Processors](https://cloud.google.com/document-ai/docs/processors-list#custom_processors)
    - [Custom Document Extractor](https://cloud.google.com/document-ai/docs/processors-list#processor_cde)
        - OCR
        - Entity Extraction, Including Generative AI for extraction
        - [Documentation Tutorial](https://cloud.google.com/document-ai/docs/workbench/build-custom-processor)
    - [Custom Document Classifier](https://cloud.google.com/document-ai/docs/processors-list#processor_CUSTOM_CLASSIFICATION_PROCESSOR)
        - OCR
        - Classsification
        - [Documentation Tutorial](https://cloud.google.com/document-ai/docs/workbench/build-custom-classification-processor)
    - [Customer Document Splitter](https://cloud.google.com/document-ai/docs/processors-list#processor_CUSTOM_SPLITTING_PROCESSOR)
        - OCR
        - Classsification
        - Splitting
        - [Documentation Tutorial](https://cloud.google.com/document-ai/docs/workbench/build-custom-splitter-processor)
    - [Summarizer](https://cloud.google.com/document-ai/docs/processors-list#processor_SUMMARIZER)
        - Summarize
        - [Documentation Tutorial](https://cloud.google.com/document-ai/docs/workbench/build-summarizer-processor)

---
## Notebook Workflows

- Document AI - Process Documents
- Document AI - Process Responses
- Document AI - Automation

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
    - entities: list</b>
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:pages:layout:blocks</td>
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
            <td>Document:pages:layout:paragraphs</td>
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
            <td>Document:pages:layout:lines</td>
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
            <td>Document:pages:layout:tokens</td>
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
            <td>Document:pages:layout:symbols</td>
            <td>
                <pre>
<b># OCR Parser has Symbols (characters):</b>
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
            <td>Document:pages:layout:tables</td>
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
            <td>Document:pages:layout:formFields</td>
            <td>
                <pre>
<b>- formFields: list</b>
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
            <td>Document:entities</td>
            <td>
                <pre>
<b># OCR Parser Has Quality Scores: </b>
- entities: list
    <b>- type: "quality_score"</b>
    - confidence: float
    - pageAnchor:
        - pageRefs: list
            - page: string
    - properties: list
        - type: string = "quality/defect_[document_cutoff, glare, text_cutoff]"
        - confidence: float
<BR><b># Form Parser Has Generic Entities:</b>
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
<BR><b># Summarizer (Custom):</b>
- entities: list
    <b>- type: "summary"</b>
    - mentionText: string
    - normalizedValue:
        - text: string
<BR><b># Custom Document Splitter:</b>
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
<BR><b># Custom Document Classifier:</b>
- entities: list
    - type: string
    - confidence: float
    - id: string
<BR><b># Custom Document Extractor:</b>
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
<BR><b># Specialized Parsers: specific entities, including nesting:</b>
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
        <tr style='text-align:left;vertical-align:middle;border:1px solid black'>
            <td>Document:pages:layout:image</td>
            <td>
                <pre>
- image: 
    - content: base64 string
    - mimeType: string
    - width: int
    - height: int
<BR><b># Included With OCR:</b>
- imageQualityScores:
    - qualityScore: float
    - detectedDefects: list
        - type: string
        - confidence: float
                </pre>
            </td>
        </tr>
<!--.....................................................................................................................................................................-->
    </tbody>
</table>








Automation
- triggering document parsing on document creation

BigQuery For working with parsing results
- Extract parts of documents
- Create chunks of content for use in application
- Add Embedding using Vertex AI Generative AI

Projects
- Creating a table of contents using font sizes!