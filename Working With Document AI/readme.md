![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2FWorking+With+Document+AI&dt=readme.md)

# /Working With Document AI/readme.md

Working With [DocumentAI](https://cloud.google.com/document-ai/docs/overview) to extract information from documents as part of ML focused workflows.

## How does it work?

Document AI is an API where you interact with processors to extract information from documents.

You enable the API, create an instance of a processor in your project, send in document(s), receive back JSON with the extracted information:

<p align="center" width="100%"><center>
    <img src="../architectures/architectures/images/working%20with/documentai/readme/high_level.png">
</center></p>

**Documents**
- [Document Types](https://cloud.google.com/document-ai/docs/file-types) like pdf, gif, tiff, jpeg, pn, gmp, webp

**Clients**
- Clients For Processing: [list of clients](https://cloud.google.com/document-ai/docs/libraries), [REST](https://cloud.google.com/document-ai/docs/reference/rest), [RPC](https://cloud.google.com/document-ai/docs/reference/rpc)
    - [Online](https://cloud.google.com/document-ai/docs/send-request#online-process)
        - Sync and Async Client available
    - [Batch](https://cloud.google.com/document-ai/docs/send-request#batch-process)
        - Sync and Async Client available

**Processors**
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

```
document
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
            - blocks: list
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
            - paragraphs: list
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
            - lines: list
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
            - tokens: list
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
###### FORM & SPECIALTY PARSERS INCLUDE #########################################################
            - tables: list
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
###### FORM & SPECIALTY PARSER INCLUDE #########################################################
            - formFields: list
                - fieldName:
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
                - fieldValue:
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
###### SPECIALTY & CUSTOM PARSER INCLUDE #########################################################
            - entities: list
                - fieldName:
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
                - fieldValue:
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
###### ALL PARSER INCLUDE #########################################################
            - image: 
                - content: base64 string
                - mimeType: string
                - width: int
                - height: int
                
```





Automation
- triggering document parsing on document creation

BigQuery For working with parsing results
- Extract parts of documents
- Create chunks of content for use in application
- Add Embedding using Vertex AI Generative AI

Projects
- Creating a table of contents using font sizes!