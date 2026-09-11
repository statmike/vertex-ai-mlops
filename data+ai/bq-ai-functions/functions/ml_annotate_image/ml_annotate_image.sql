-- ML.ANNOTATE_IMAGE — Progressive SQL Examples
-- ============================================
-- Table-valued function that annotates images with the Cloud Vision API
-- through a remote model. One model, eight documented features, selected by
-- the vision_features argument.
--
-- Requires: Cloud Resource connection whose service account holds
--           roles/serviceusage.serviceUsageConsumer,
--           roles/bigquery.connectionUser and roles/storage.objectViewer,
--           plus a remote model with
--           REMOTE_SERVICE_TYPE = 'CLOUD_AI_VISION_V1'
--
-- Input:   an object table over images in Cloud Storage
-- Returns: the object table columns + ml_annotate_image_result (JSON) +
--          ml_annotate_image_status (per-row, empty on success)
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-annotate-image


-- =============================================================================
-- Setup: the object table and the remote model
-- =============================================================================
-- The object table reads the image bytes through the connection, which is why
-- its service account needs roles/storage.objectViewer.
CREATE OR REPLACE EXTERNAL TABLE `PROJECT_ID.DATASET.ml_annotate_image_photos`
  WITH CONNECTION `PROJECT_ID.US.CONNECTION_ID`
  OPTIONS (
    object_metadata = 'SIMPLE',
    uris = ['gs://BUCKET/bq_ai_functions/ml_annotate_image/*']
  );

-- Nothing trains. One model serves every feature — the feature list is an
-- argument to the function, not an option on the model.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.ml_annotate_image_model`
  REMOTE WITH CONNECTION `PROJECT_ID.US.CONNECTION_ID`
  OPTIONS (REMOTE_SERVICE_TYPE = 'CLOUD_AI_VISION_V1');


-- =============================================================================
-- Example 1: LABEL_DETECTION — what is in this picture?
-- =============================================================================
-- label_annotations is an array, so JSON_QUERY_ARRAY + UNNEST gives one row
-- per label. Give the range variable its own name: an UNNEST alias that
-- collides with a SELECT alias resolves to the SELECT alias in QUALIFY.
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  STRING(annotation.description) AS label,
  ROUND(FLOAT64(annotation.score), 3) AS score
FROM ML.ANNOTATE_IMAGE(
  MODEL `PROJECT_ID.DATASET.ml_annotate_image_model`,
  TABLE `PROJECT_ID.DATASET.ml_annotate_image_photos`,
  STRUCT(['LABEL_DETECTION'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.label_annotations)) AS annotation
QUALIFY ROW_NUMBER() OVER (PARTITION BY image ORDER BY FLOAT64(annotation.score) DESC) <= 3
ORDER BY image, score DESC;


-- =============================================================================
-- Example 2: Many features in one call — which keys come back
-- =============================================================================
-- A feature that finds nothing returns no key at all, not an empty array, so
-- code that assumes a key exists breaks on the first image without a logo.
-- crop_hints_annotation arrives even though nothing requested it.
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  LENGTH(TO_JSON_STRING(ml_annotate_image_result)) AS result_bytes,
  ARRAY_TO_STRING(
    ARRAY(SELECT key FROM UNNEST(JSON_KEYS(ml_annotate_image_result, 1)) AS key ORDER BY key),
    ', ') AS keys_returned,
  ml_annotate_image_status
FROM ML.ANNOTATE_IMAGE(
  MODEL `PROJECT_ID.DATASET.ml_annotate_image_model`,
  TABLE `PROJECT_ID.DATASET.ml_annotate_image_photos`,
  STRUCT(['LABEL_DETECTION', 'OBJECT_LOCALIZATION', 'LANDMARK_DETECTION', 'LOGO_DETECTION',
          'TEXT_DETECTION', 'IMAGE_PROPERTIES', 'FACE_DETECTION'] AS vision_features)
)
ORDER BY image;


-- =============================================================================
-- Example 3: OBJECT_LOCALIZATION — named things, with normalized boxes
-- =============================================================================
-- Vertices are fractions of image width and height, clockwise from top left,
-- so they survive resizing. Rows are annotations, not objects: several names
-- can share one box.
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  STRING(object.name) AS object_name,
  ROUND(FLOAT64(object.score), 3) AS score,
  ROUND(FLOAT64(object.bounding_poly.normalized_vertices[0].x), 3) AS x0,
  ROUND(FLOAT64(object.bounding_poly.normalized_vertices[0].y), 3) AS y0,
  ROUND(FLOAT64(object.bounding_poly.normalized_vertices[2].x), 3) AS x1,
  ROUND(FLOAT64(object.bounding_poly.normalized_vertices[2].y), 3) AS y1
FROM ML.ANNOTATE_IMAGE(
  MODEL `PROJECT_ID.DATASET.ml_annotate_image_model`,
  (SELECT * FROM `PROJECT_ID.DATASET.ml_annotate_image_photos` WHERE uri LIKE '%duck_and_truck%'),
  STRUCT(['OBJECT_LOCALIZATION'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.localized_object_annotations)) AS object
ORDER BY score DESC;


-- =============================================================================
-- Example 4: TEXT_DETECTION vs DOCUMENT_TEXT_DETECTION
-- =============================================================================
-- Both fill full_text_annotation.text with the same words. DOCUMENT adds a
-- confidence at every level of the page/block/paragraph/word hierarchy, which
-- is what makes its payload larger for identical text.
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  LENGTH(STRING(ml_annotate_image_result.full_text_annotation.text)) AS characters,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(ml_annotate_image_result.text_annotations)) AS text_annotations,
  LENGTH(TO_JSON_STRING(ml_annotate_image_result)) AS result_bytes
FROM ML.ANNOTATE_IMAGE(
  MODEL `PROJECT_ID.DATASET.ml_annotate_image_model`,
  (SELECT * FROM `PROJECT_ID.DATASET.ml_annotate_image_photos`
   WHERE uri LIKE '%handwritten%' OR uri LIKE '%screen%'),
  STRUCT(['TEXT_DETECTION'] AS vision_features)
)
ORDER BY image;

SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  LENGTH(STRING(ml_annotate_image_result.full_text_annotation.text)) AS characters,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(ml_annotate_image_result.text_annotations)) AS text_annotations,
  LENGTH(TO_JSON_STRING(ml_annotate_image_result)) AS result_bytes
FROM ML.ANNOTATE_IMAGE(
  MODEL `PROJECT_ID.DATASET.ml_annotate_image_model`,
  (SELECT * FROM `PROJECT_ID.DATASET.ml_annotate_image_photos`
   WHERE uri LIKE '%handwritten%' OR uri LIKE '%screen%'),
  STRUCT(['DOCUMENT_TEXT_DETECTION'] AS vision_features)
)
ORDER BY image;


-- =============================================================================
-- Example 5: LANDMARK_DETECTION — coordinates, and the omitted-zero trap
-- =============================================================================
-- Landmarks come back with latitude and longitude. The bounding box here is in
-- absolute pixels, and a zero-valued field is omitted from the JSON entirely:
-- a vertex at the origin is {}, so INT64(vertex.x) is NULL, not 0.
SELECT
  STRING(landmark.description) AS landmark,
  ROUND(FLOAT64(landmark.score), 3) AS score,
  ROUND(FLOAT64(landmark.locations[0].lat_lng.latitude), 5) AS latitude,
  ROUND(FLOAT64(landmark.locations[0].lat_lng.longitude), 5) AS longitude,
  TO_JSON_STRING(landmark.bounding_poly.vertices[0]) AS first_vertex_raw,
  INT64(landmark.bounding_poly.vertices[0].x) AS x_naive,
  IFNULL(INT64(landmark.bounding_poly.vertices[0].x), 0) AS x_coalesced
FROM ML.ANNOTATE_IMAGE(
  MODEL `PROJECT_ID.DATASET.ml_annotate_image_model`,
  (SELECT * FROM `PROJECT_ID.DATASET.ml_annotate_image_photos` WHERE uri LIKE '%eiffel%'),
  STRUCT(['LANDMARK_DETECTION'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.landmark_annotations)) AS landmark
ORDER BY score DESC;


-- =============================================================================
-- Example 6: LOGO_DETECTION and FACE_DETECTION
-- =============================================================================
-- Faces come back as boxes with expression likelihoods on a VERY_UNLIKELY to
-- VERY_LIKELY scale — strings, not numbers. No identity: no name, no ID,
-- nothing to join against. A likelihood is a guess at an expression, and an
-- expression is not an emotion.
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  STRING(annotation.description) AS logo,
  ROUND(FLOAT64(annotation.score), 3) AS logo_score
FROM ML.ANNOTATE_IMAGE(
  MODEL `PROJECT_ID.DATASET.ml_annotate_image_model`,
  (SELECT * FROM `PROJECT_ID.DATASET.ml_annotate_image_photos` WHERE uri LIKE '%logo%'),
  STRUCT(['LOGO_DETECTION'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.logo_annotations)) AS annotation;

SELECT
  ROUND(FLOAT64(face.detection_confidence), 3) AS detection_confidence,
  STRING(face.joy_likelihood) AS joy,
  STRING(face.sorrow_likelihood) AS sorrow,
  STRING(face.anger_likelihood) AS anger,
  STRING(face.surprise_likelihood) AS surprise,
  STRING(face.headwear_likelihood) AS headwear,
  ROUND(FLOAT64(face.roll_angle), 1) AS roll_angle
FROM ML.ANNOTATE_IMAGE(
  MODEL `PROJECT_ID.DATASET.ml_annotate_image_model`,
  (SELECT * FROM `PROJECT_ID.DATASET.ml_annotate_image_photos` WHERE uri LIKE '%face%'),
  STRUCT(['FACE_DETECTION'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.face_annotations)) AS face;


-- =============================================================================
-- Example 7: IMAGE_PROPERTIES — dominant colors
-- =============================================================================
-- score ranks how much a color characterizes the image; pixel_fraction is the
-- share of pixels it covers. They answer different questions and they do not
-- agree — the top-scoring color is often a small part of the picture.
SELECT
  ROUND(FLOAT64(color.score), 4) AS score,
  ROUND(FLOAT64(color.pixel_fraction), 4) AS pixel_fraction,
  IFNULL(INT64(color.color.red), 0) AS red,
  IFNULL(INT64(color.color.green), 0) AS green,
  IFNULL(INT64(color.color.blue), 0) AS blue
FROM ML.ANNOTATE_IMAGE(
  MODEL `PROJECT_ID.DATASET.ml_annotate_image_model`,
  (SELECT * FROM `PROJECT_ID.DATASET.ml_annotate_image_photos` WHERE uri LIKE '%bali%'),
  STRUCT(['IMAGE_PROPERTIES'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(
  annotated.ml_annotate_image_result.image_properties_annotation.dominant_colors.colors)) AS color
ORDER BY score DESC;


-- =============================================================================
-- Example 8: Vision against AI.GENERATE on the same images
-- =============================================================================
-- OBJ.MAKE_REF names the file and the connection, OBJ.FETCH_METADATA resolves
-- it, OBJ.GET_ACCESS_URL hands the model a readable URL. Vision returns
-- taxonomy terms from a fixed vocabulary; the LLM names the specific thing.
-- AI.GENERATE through this connection also needs roles/aiplatform.user.
WITH vision AS (
  SELECT
    REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
    uri,
    ARRAY_TO_STRING(ARRAY(
      SELECT STRING(label.description)
      FROM UNNEST(JSON_QUERY_ARRAY(ml_annotate_image_result.label_annotations)) AS label
      LIMIT 5), ', ') AS vision_labels
  FROM ML.ANNOTATE_IMAGE(
    MODEL `PROJECT_ID.DATASET.ml_annotate_image_model`,
    TABLE `PROJECT_ID.DATASET.ml_annotate_image_photos`,
    STRUCT(['LABEL_DETECTION'] AS vision_features))
)
SELECT
  image,
  vision_labels,
  AI.GENERATE(STRUCT(
    'List the five most prominent labels for this image, comma separated, no other text.' AS prompt,
    [OBJ.GET_ACCESS_URL(
       OBJ.FETCH_METADATA(OBJ.MAKE_REF(uri, 'PROJECT_ID.US.CONNECTION_ID')), 'r')
    ] AS object_ref_runtime
  )).result AS gemini_labels
FROM vision
ORDER BY image;


-- =============================================================================
-- Cleanup
-- =============================================================================
DROP EXTERNAL TABLE IF EXISTS `PROJECT_ID.DATASET.ml_annotate_image_photos`;
DROP MODEL IF EXISTS `PROJECT_ID.DATASET.ml_annotate_image_model`;
