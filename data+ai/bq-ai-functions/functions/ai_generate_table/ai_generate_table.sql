-- AI.GENERATE_TABLE — Progressive SQL Examples
-- ==============================================
-- Table-valued function that generates structured output from a user-defined schema.
-- Requires a remote Gemini model (CREATE MODEL) and an output_schema.
--
-- Returns: input columns + schema columns + full_response, status
-- Multimodal: Supports documents, images, and video via ObjectRef (see examples 7-8)
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-table


-- =============================================================================
-- Example 1: Simple structured output
-- =============================================================================
SELECT prompt, category, sentiment, confidence
FROM AI.GENERATE_TABLE(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT 'Analyze: Great product, love it!' AS prompt),
  STRUCT('category STRING, sentiment STRING, confidence FLOAT64' AS output_schema)
);


-- =============================================================================
-- Example 2: Multiple rows with schema
-- =============================================================================
SELECT review, sentiment, confidence
FROM AI.GENERATE_TABLE(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT CONCAT('Analyze this review: ', review) AS prompt, review
   FROM UNNEST(['Amazing quality!', 'Terrible, broke instantly.', 'It was okay.']) AS review),
  STRUCT('sentiment STRING, confidence FLOAT64' AS output_schema)
);


-- =============================================================================
-- Example 3: Schema with field descriptions
-- =============================================================================
SELECT city, country, population_millions, continent, famous_landmark
FROM AI.GENERATE_TABLE(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT CONCAT('Give me facts about: ', city) AS prompt, city
   FROM UNNEST(['Tokyo', 'Paris', 'Nairobi']) AS city),
  STRUCT(
    'country STRING OPTIONS(description = "Country name"),
     population_millions FLOAT64 OPTIONS(description = "City population in millions"),
     continent STRING OPTIONS(description = "Continent"),
     famous_landmark STRING OPTIONS(description = "Most famous landmark")' AS output_schema
  )
);


-- =============================================================================
-- Example 4: Generating sample data
-- AI.GENERATE_TABLE produces one output row per input row.
-- To generate multiple items, provide multiple input rows.
-- =============================================================================
SELECT product_name, category, price_usd, rating, in_stock
FROM AI.GENERATE_TABLE(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT CONCAT('Generate a realistic e-commerce product in the ', cat, ' category.') AS prompt
   FROM UNNEST(['Electronics', 'Clothing', 'Home & Kitchen', 'Sports', 'Books']) AS cat),
  STRUCT(
    'product_name STRING, category STRING, price_usd FLOAT64, rating FLOAT64, in_stock BOOL' AS output_schema
  )
);


-- =============================================================================
-- Example 5: Entity extraction
-- =============================================================================
SELECT text, person_name, organization, location, date_mentioned
FROM AI.GENERATE_TABLE(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT text,
   CONCAT('Extract entities from this text: ', text) AS prompt
   FROM UNNEST([
     'Tim Cook announced new Apple products at the Cupertino event on March 15, 2025.',
     'Satya Nadella presented Microsoft''s AI strategy at Build conference in Seattle.'
   ]) AS text),
  STRUCT('person_name STRING, organization STRING, location STRING, date_mentioned STRING' AS output_schema)
);


-- =============================================================================
-- Example 7: Extract structured data from a document with ObjectRef
-- =============================================================================
-- Pass a document via ObjectRef in the prompt column. The STRUCT prompt
-- contains both text and object_ref_runtime fields.
--
-- Requires: Cloud resource connection with roles/storage.objectViewer
SELECT vendor_name, invoice_number, total_amount, currency, invoice_date, line_item_count
FROM AI.GENERATE_TABLE(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT STRUCT(
    'Extract the key fields from this invoice.' AS prompt,
    [OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF(
          'gs://BUCKET/path/to/invoice.pdf',
          'PROJECT_ID.LOCATION.CONNECTION_ID'
        )
      ), 'r'
    )] AS object_ref_runtime
  ) AS prompt),
  STRUCT('vendor_name STRING, invoice_number STRING, total_amount FLOAT64, currency STRING, invoice_date STRING, line_item_count INT64' AS output_schema)
);


-- =============================================================================
-- Example 8: Process multiple documents with detailed extraction
-- =============================================================================
-- Process different document types with a richer schema including arrays.
SELECT uri, document_type, vendor_or_store, total_amount, date, line_items
FROM AI.GENERATE_TABLE(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT
    uri,
    STRUCT(
      'Identify the document type and extract all details.' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            uri,
            'PROJECT_ID.LOCATION.CONNECTION_ID'
          )
        ), 'r'
      )] AS object_ref_runtime
    ) AS prompt
   FROM UNNEST([
     'gs://BUCKET/path/to/invoice.pdf',
     'gs://BUCKET/path/to/receipt.pdf'
   ]) AS uri),
  STRUCT('document_type STRING, vendor_or_store STRING, total_amount FLOAT64, date STRING, line_items ARRAY<STRING>' AS output_schema)
);
