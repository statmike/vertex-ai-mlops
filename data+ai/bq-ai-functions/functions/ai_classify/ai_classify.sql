-- AI.CLASSIFY — Progressive SQL Examples
-- ========================================
-- Managed scalar function for classification into user-defined categories.
-- Returns STRING (single-label) or ARRAY<STRING> (multi-label).
-- BigQuery auto-optimizes classification prompts.
--
-- Returns: STRING or ARRAY<STRING> — NULL on error
-- Multimodal: Supports documents, images, and video via ObjectRef (see examples 5-6)
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-classify


-- =============================================================================
-- Example 1: Simple classification
-- =============================================================================
SELECT
  review,
  AI.CLASSIFY(
    review,
    ['positive', 'negative', 'neutral']
  ) AS sentiment
FROM UNNEST([
  'Amazing product, exceeded expectations!',
  'Terrible quality, fell apart immediately.',
  'It works as expected. Nothing special.'
]) AS review;


-- =============================================================================
-- Example 2: Categories with descriptions
-- =============================================================================
SELECT
  ticket,
  AI.CLASSIFY(
    ticket,
    [('billing', 'Issues with charges, invoices, or payments'),
     ('technical', 'Product bugs, errors, or how-to questions'),
     ('shipping', 'Delivery, tracking, or logistics issues'),
     ('other', 'Anything not matching above')]
  ) AS category
FROM UNNEST([
  'I was charged twice for my subscription.',
  'The app crashes when I try to upload files.',
  'My package has been in transit for 3 weeks.',
  'Can I get a gift card for my friend?'
]) AS ticket;


-- =============================================================================
-- Example 3: Multi-label classification
-- =============================================================================
SELECT
  article,
  AI.CLASSIFY(
    article,
    ['technology', 'business', 'science', 'politics', 'health'],
    output_mode => 'multi'
  ) AS categories
FROM UNNEST([
  'New AI regulations proposed by the EU could reshape the tech industry.',
  'Scientists develop cheaper solar panels that boost clean energy stocks.',
  'Study shows regular exercise reduces risk of cognitive decline.'
]) AS article;


-- =============================================================================
-- Example 4: Single-label with array output
-- =============================================================================
SELECT
  email,
  AI.CLASSIFY(
    email,
    ['spam', 'promotional', 'personal', 'work'],
    output_mode => 'single'
  ) AS category
FROM UNNEST([
  'You have won a million dollars! Click here NOW!',
  'Sale: 50% off all items this weekend only.',
  'Hey, are we still meeting for dinner tonight?',
  'Please review the Q3 budget spreadsheet by Friday.'
]) AS email;


-- =============================================================================
-- Example 5: Classify a document with ObjectRef
-- =============================================================================
-- Create an object table, then use EXTERNAL_OBJECT_TRANSFORM to get a signed
-- ref that AI.CLASSIFY can read directly.
--
-- Requires: Object table with Cloud resource connection

-- CREATE OR REPLACE EXTERNAL TABLE `PROJECT_ID.DATASET.ai_classify_docs`
-- WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_ID`
-- OPTIONS (
--   object_metadata = 'SIMPLE',
--   uris = ['gs://BUCKET/path/to/documents/*.pdf']
-- );

SELECT
  uri,
  AI.CLASSIFY(
    docs.ref,
    ['invoice', 'receipt', 'contract', 'report']
  ) AS document_type
FROM
  EXTERNAL_OBJECT_TRANSFORM(TABLE `PROJECT_ID.DATASET.ai_classify_docs`,
                            ['SIGNED_URL']) AS docs;


-- =============================================================================
-- Example 6: Classify documents with category descriptions
-- =============================================================================
-- Add descriptions to guide the model when distinguishing between similar
-- document types.
SELECT
  uri,
  AI.CLASSIFY(
    docs.ref,
    [('invoice', 'A bill for goods or services with line items, totals, and payment terms'),
     ('receipt', 'A proof of purchase showing items bought and amount paid'),
     ('contract', 'A legal agreement between parties with terms and conditions'),
     ('report', 'An analytical document with findings, data, or recommendations')]
  ) AS document_type
FROM
  EXTERNAL_OBJECT_TRANSFORM(TABLE `PROJECT_ID.DATASET.ai_classify_docs`,
                            ['SIGNED_URL']) AS docs;
