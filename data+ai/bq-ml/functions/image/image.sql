-- Image Preprocessing — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- Four model-free scalar functions that turn image BYTES into the numeric
-- STRUCT a vision model consumes. ML.DECODE_IMAGE is always the entry point;
-- ML.RESIZE_IMAGE, ML.CONVERT_COLOR_SPACE, and ML.CONVERT_IMAGE_TYPE nest
-- around it in any combination, and all four are usable inside a TRANSFORM
-- clause so the preprocessing is stored with the model.
--
-- GOTCHA these four functions REQUIRE a BigQuery Editions reservation.
-- Under on-demand (per-byte) pricing every one of them fails with
-- "BigQuery's ML image-processing functions requires reservation, but no
-- reservation was assigned for job type QUERY, to project <p> or its parent,
-- in location <loc>." None of the four reference pages mentions this. Create
-- a small ENTERPRISE autoscale reservation (0 baseline slots) -- NOT a
-- capacity commitment -- and delete it when done. See the notebook's Setup.
--
-- GOTCHA the output STRUCT's fields are named `dimensions` and `values`.
-- The reference pages describe the type as STRUCT<ARRAY<INT64> shape, ...>;
-- selecting `.shape` errors. `dimensions` is [height, width, channels] and
-- `values` is flattened row-major in HWC order.
--
-- GOTCHA ML.DECODE_IMAGE accepts ANY BYTES value, not only an object
-- table's `data` pseudocolumn -- every example below runs on a FROM_BASE64
-- literal, no bucket, connection, or object table required.
--
-- GOTCHA ML.DECODE_IMAGE always returns 3 channels. An RGBA image's alpha is
-- silently dropped, not composited (a 50%-transparent pixel decodes to its raw
-- RGB, unblended), and a single-channel grayscale image is replicated into
-- three identical channels. There is no flag and no warning. Going the other
-- way, ML.CONVERT_COLOR_SPACE(i, 'GRAYSCALE') returns 1 channel, not 3 -- the
-- channel count is set by the last function in the chain, not by the image.
--
-- GOTCHA the documented ranges are wrong at the top. Decoded values are
-- documented as [0, 1) and ML.CONVERT_IMAGE_TYPE output as [0, 255); a pure
-- white pixel returns exactly 1.0 and exactly 255. Both ranges are closed.
--
-- GOTCHA ML.CONVERT_IMAGE_TYPE is one-way -- there is no INT64 -> FLOAT64
-- signature, so it must be the last step of a pipeline.
--
-- GOTCHA ML.CONVERT_COLOR_SPACE's GRAYSCALE and YIQ's Y channel are two
-- DIFFERENT lumas. GRAYSCALE uses [0.2989, 0.5870, 0.1140] (TensorFlow's
-- rounded constants); YIQ's Y uses the true BT.601 [0.299, 0.587, 0.114].
-- They differ by a fraction of one 8-bit level -- invisible, but enough to
-- break a bit-for-bit comparison against a reimplementation.
--
-- GOTCHA HSV's hue is on [0, 1], not degrees. 20 degrees comes back as
-- 0.0555..., not 20.
--
-- GOTCHA ML.RESIZE_IMAGE returns float32-precision values while decode and
-- color-space conversion are float64-exact. It also PRESERVES the value type:
-- INT64 in, INT64 out (and it rounds half-to-even, so a true mean of 152.5
-- becomes 152). Keep the pipeline in floats and convert type last.
--
-- GOTCHA preserve_aspect_ratio = TRUE treats target_height/target_width as a
-- BOUNDING BOX: the scale is min(th/h, tw/w). If that scale rounds a source
-- dimension to zero, the query fails with a generic "internal error ...
-- usually caused by a transient issue ... Error: 80038528" that is in fact
-- fully deterministic -- and google-cloud-bigquery's default job-retry policy
-- resubmits it for minutes. Pass job_retry=None, and bound the box so that
-- min(th/h, tw/w) * min(h, w) >= 0.5.
--
-- GOTCHA an image whose decoded STRUCT would exceed 60 MB is AUTOMATICALLY
-- DOWNSCALED preserving aspect ratio, not rejected -- a silently resized
-- input, not a failed query. The hard limits are 20 MB per object-table file
-- and 10 MB for the BYTES value passed to ML.DECODE_IMAGE. Pin large images
-- with an explicit ML.RESIZE_IMAGE rather than relying on the ceiling.
--
-- Data: five images encoded inline as base64 PNG literals, so every example
--       below is self-contained. Pixel values, in RGB:
--         swatch   1x2  (200,100,50) and (0,128,255)
--         gradient 4x8  R = 32*x, G = 64*y, B = 128
--         alpha    1x2  swatch as RGBA, alpha 255 and 128
--         gray     1x2  swatch converted to single-channel L: 124, 104
--         white    1x1  (255,255,255)
--       Example 9 uses an object table -- see the notebook for creating it.
--
-- Full reference: ../../reference/model-free-functions.md
-- Official docs:
--   ML.DECODE_IMAGE:        https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-decode-image
--   ML.RESIZE_IMAGE:        https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-resize-image
--   ML.CONVERT_COLOR_SPACE: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-convert-color-space
--   ML.CONVERT_IMAGE_TYPE:  https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-convert-image-type
--   Object tables:          https://cloud.google.com/bigquery/docs/object-tables


-- =============================================================================
-- Example 1: ML.DECODE_IMAGE -- the contract
-- =============================================================================
-- dimensions is [height, width, channels]; values is flattened row-major in
-- HWC order (all three channels of pixel 1, then pixel 2), scaled to
-- pixel / 255 exactly. The field is `dimensions`, not `shape`.
SELECT
  ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7QOjdAAAAD0lEQVR4nGM4kWLE0PAfAAlyAt5YcK25AAAAAElFTkSuQmCC')).dimensions AS dimensions,
  ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7QOjdAAAAD0lEQVR4nGM4kWLE0PAfAAlyAt5YcK25AAAAAElFTkSuQmCC')).values     AS values;
-- dimensions = [1, 2, 3]
-- values     = [0.7843137254901961, 0.39215686274509803, 0.19607843137254902,
--               0.0,                0.5019607843137255,  1.0]


-- =============================================================================
-- Example 2: channels is always 3 -- alpha dropped, grayscale replicated
-- =============================================================================
-- The RGBA image's second pixel has alpha 128. Its RGB values come back
-- unchanged (0, 128, 255) -- nothing was composited against a background.
-- The single-channel grayscale image comes back as three identical channels.
SELECT
  ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAYAAAD0In+KAAAAEUlEQVR4nGM4kWL0n6HhfwMAEyoEXQfd9+cAAAAASUVORK5CYII=')).dimensions AS rgba_dimensions,
  ML.CONVERT_IMAGE_TYPE(
    ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAYAAAD0In+KAAAAEUlEQVR4nGM4kWL0n6HhfwMAEyoEXQfd9+cAAAAASUVORK5CYII='))).values AS rgba_as_ints,
  ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAAAAADRSSBWAAAAC0lEQVR4nGOseQMAAeoBajyCxnMAAAAASUVORK5CYII=')).dimensions AS gray_dimensions;
-- rgba_dimensions = [1, 2, 3]   -- not [1, 2, 4]
-- rgba_as_ints    = [200, 100, 50, 0, 128, 255]
-- gray_dimensions = [1, 2, 3]   -- not [1, 2, 1]

-- Non-image bytes name the accepted format list -- PNG, JPEG, BMP only.
-- One stray file in an object table fails the whole query, not just its row.
SELECT ML.DECODE_IMAGE(b'not an image at all').dimensions;
-- Input image bytes could not be decoded. Expected valid image of type
-- PNG, JPEG, or BMP; error in ML.DECODE_IMAGE expression


-- =============================================================================
-- Example 3: the documented ranges exclude endpoints that are attainable
-- =============================================================================
-- Compared in SQL rather than by eye: a float that prints as 1.0 need not
-- equal 1.0. This one does, and the integer is exactly 255.
SELECT
  ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/AAX+Av4N70a4AAAAAElFTkSuQmCC')).values[OFFSET(0)] = 1.0 AS float_is_exactly_one,
  ML.CONVERT_IMAGE_TYPE(
    ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/AAX+Av4N70a4AAAAAElFTkSuQmCC'))).values[OFFSET(0)] = 255 AS int_is_exactly_255;
-- true, true -- the ranges are [0, 1] and [0, 255], both closed.


-- =============================================================================
-- Example 4: ML.CONVERT_IMAGE_TYPE is exact, and one-way
-- =============================================================================
-- pixel / 255 and back is lossless for all 256 byte values.
SELECT ML.CONVERT_IMAGE_TYPE(
         ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7QOjdAAAAD0lEQVR4nGM4kWLE0PAfAAlyAt5YcK25AAAAAElFTkSuQmCC'))).values AS ints;
-- [200, 100, 50, 0, 128, 255] -- identical to the source pixels.

-- There is no reverse signature. The error text is also the authoritative
-- statement of the struct's real field names.
SELECT ML.CONVERT_IMAGE_TYPE(
         ML.CONVERT_IMAGE_TYPE(
           ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7QOjdAAAAD0lEQVR4nGM4kWLE0PAfAAlyAt5YcK25AAAAAElFTkSuQmCC')))).values;
-- No matching signature for function ML.CONVERT_IMAGE_TYPE
--   Argument types: STRUCT<dimensions ARRAY<INT64>, values ARRAY<INT64>>
--   Signature:      ML.CONVERT_IMAGE_TYPE(STRUCT<dimensions ARRAY<INT64>, values ARRAY<FLOAT64>>)


-- =============================================================================
-- Example 5: ML.CONVERT_COLOR_SPACE -- four targets, two different lumas
-- =============================================================================
-- GRAYSCALE returns 1 channel -- [1, 2, 1], not [1, 2, 3]. HSV/YIQ/YUV keep 3
-- distinct channels. Hue is on [0, 1].
WITH img AS (
  SELECT ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7QOjdAAAAD0lEQVR4nGM4kWLE0PAfAAlyAt5YcK25AAAAAElFTkSuQmCC')) AS i
)
SELECT
  ML.CONVERT_COLOR_SPACE(i, 'GRAYSCALE').dimensions AS grayscale_dimensions,
  ML.CONVERT_COLOR_SPACE(i, 'GRAYSCALE').values     AS grayscale,
  ML.CONVERT_COLOR_SPACE(i, 'HSV').values           AS hsv,
  ML.CONVERT_COLOR_SPACE(i, 'YIQ').values           AS yiq,
  ML.CONVERT_COLOR_SPACE(i, 'YUV').values           AS yuv
FROM img;
-- grayscale_dimensions = [1, 2, 1]
-- grayscale = [0.48698039215686273, 0.40865098039215686]  -- one value/pixel
-- Pixel 1 (200,100,50): HSV (0.05555555555555555, 0.75, 0.7843137254901961)
--   HSV hue 0.0555... = 20 degrees / 360, not 20.
--   grayscale = [0.2989, 0.5870, 0.1140] . rgb  = 0.48698039215686273
--   yiq's Y   = [0.299,  0.587,  0.114 ] . rgb  = 0.4870588235294117

-- The two lumas, side by side. The difference is a fraction of one 8-bit
-- level: invisible, but enough to break an exact reproducibility check.
WITH img AS (
  SELECT ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7QOjdAAAAD0lEQVR4nGM4kWLE0PAfAAlyAt5YcK25AAAAAElFTkSuQmCC')) AS i
)
SELECT
  ML.CONVERT_COLOR_SPACE(i, 'GRAYSCALE').values[OFFSET(0)] AS grayscale_luma,
  ML.CONVERT_COLOR_SPACE(i, 'YIQ').values[OFFSET(0)]       AS yiq_luma,
  (ML.CONVERT_COLOR_SPACE(i, 'GRAYSCALE').values[OFFSET(0)]
   - ML.CONVERT_COLOR_SPACE(i, 'YIQ').values[OFFSET(0)]) * 255 AS difference_in_8bit_levels
FROM img;

-- INT64 image data is accepted and normalized by 255 on the way in -- the
-- result is identical to the float path, and the output is FLOAT64 either way.
WITH img AS (
  SELECT ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7QOjdAAAAD0lEQVR4nGM4kWLE0PAfAAlyAt5YcK25AAAAAElFTkSuQmCC')) AS i
)
-- (ARRAY does not support `=`, so compare the JSON rendering.)
SELECT TO_JSON_STRING(ML.CONVERT_COLOR_SPACE(i, 'HSV').values)
     = TO_JSON_STRING(ML.CONVERT_COLOR_SPACE(ML.CONVERT_IMAGE_TYPE(i), 'HSV').values) AS identical
FROM img;
-- identical = true

-- An unrecognized target is rejected by name.
SELECT ML.CONVERT_COLOR_SPACE(
         ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7QOjdAAAAD0lEQVR4nGM4kWLE0PAfAAlyAt5YcK25AAAAAElFTkSuQmCC')), 'LAB').values;
-- Color space LAB is not supported; error in ML.CONVERT_COLOR_SPACE expression


-- =============================================================================
-- Example 6: ML.RESIZE_IMAGE -- preserve_aspect_ratio is a bounding box
-- =============================================================================
-- Source is 4 tall x 8 wide. With TRUE, the scale is min(th/h, tw/w) and the
-- result is the largest image inside the box at the original aspect ratio.
-- Halves round to even: 1.5 -> 2, but 4.5 -> 4.
WITH img AS (
  SELECT ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAgAAAAECAIAAAA8r+mnAAAAGElEQVR4nGNkYGhQYGDARCwMDgxYAekSAKPAAi66eFnrAAAAAElFTkSuQmCC')) AS i
)
SELECT
  i.dimensions                                 AS source,      -- [4, 8, 3]
  ML.RESIZE_IMAGE(i, 4, 4, TRUE).dimensions    AS fit_4x4,     -- [2, 4, 3]  scale 0.5
  ML.RESIZE_IMAGE(i, 3, 3, TRUE).dimensions    AS fit_3x3,     -- [2, 3, 3]  scale 0.375, 1.5 -> 2
  ML.RESIZE_IMAGE(i, 9, 9, TRUE).dimensions    AS fit_9x9,     -- [4, 9, 3]  scale 1.125, 4.5 -> 4
  ML.RESIZE_IMAGE(i, 4, 4, FALSE).dimensions   AS force_4x4    -- [4, 4, 3]  distorted
FROM img;

-- Bilinear with half-pixel centers (align_corners = False): output [0,0] is
-- the average of its four source neighbors, not a copy of the top-left pixel.
-- The values are float32-precision, unlike decode and color-space output.
SELECT ML.RESIZE_IMAGE(
         ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAgAAAAECAIAAAA8r+mnAAAAGElEQVR4nGNkYGhQYGDARCwMDgxYAekSAKPAAi66eFnrAAAAAElFTkSuQmCC')),
         2, 4, FALSE).values AS resized;
-- first value 0.062745101749897 = float32(16/255), not the float64 0.06274509803921569

-- Resize preserves the value type. INT64 in, INT64 out, rounding half to even
-- (the blue channel's true mean is 152.5 and comes back as 152).
SELECT ML.RESIZE_IMAGE(
         ML.CONVERT_IMAGE_TYPE(
           ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7QOjdAAAAD0lEQVR4nGM4kWLE0PAfAAlyAt5YcK25AAAAAElFTkSuQmCC'))),
         1, 1, FALSE).values AS int_in_int_out;
-- [100, 114, 152]


-- =============================================================================
-- Example 7: the degenerate aspect-preserved fit (a deterministic "transient"
--            internal error)
-- =============================================================================
-- 4x8 into a 1x1 box scales by 0.125, giving a height of 0.5 -- rounds to
-- zero. The error message says "usually caused by a transient issue" and the
-- client library's default job-retry policy believes it. It is deterministic.
-- Guard: require min(th/h, tw/w) * min(h, w) >= 0.5, or pass FALSE.
SELECT ML.RESIZE_IMAGE(
         ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAgAAAAECAIAAAA8r+mnAAAAGElEQVR4nGNkYGhQYGDARCwMDgxYAekSAKPAAi66eFnrAAAAAElFTkSuQmCC')),
         1, 1, TRUE).dimensions;
-- An internal error occurred and the request could not be completed. This is
-- usually caused by a transient issue. ... Error: 80038528


-- =============================================================================
-- Example 8: the full pipeline, nested
-- =============================================================================
-- Order matters: ML.CONVERT_IMAGE_TYPE last, because nothing accepts its
-- INT64 output back into the float domain.
SELECT ML.CONVERT_IMAGE_TYPE(
         ML.CONVERT_COLOR_SPACE(
           ML.RESIZE_IMAGE(
             ML.DECODE_IMAGE(FROM_BASE64('iVBORw0KGgoAAAANSUhEUgAAAAgAAAAECAIAAAA8r+mnAAAAGElEQVR4nGNkYGhQYGDARCwMDgxYAekSAKPAAi66eFnrAAAAAElFTkSuQmCC')),
             4, 4, FALSE),
           'GRAYSCALE')) AS features;
-- dimensions [4, 4, 1], 16 integer values -- a fixed-size feature vector
-- regardless of the source image's shape, format, or channel count. The 1 is
-- GRAYSCALE's doing: FALSE pins height and width, the last function in the
-- chain pins the channels.


-- =============================================================================
-- Example 9: the production path -- an object table over Cloud Storage
-- =============================================================================
-- Unlike the functions themselves, an object table DOES need a Cloud Resource
-- Connection, whose service account needs roles/storage.objectViewer on the
-- bucket. Replace PROJECT_ID / DATASET_ID / LOCATION / CONNECTION_ID / BUCKET.
CREATE OR REPLACE EXTERNAL TABLE `PROJECT_ID.DATASET_ID.image_object_table`
WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_ID`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['gs://BUCKET/bq_ml/image/*']
);

-- `data` is the pseudocolumn holding the file's bytes. `content_type` is what
-- Cloud Storage was told at upload time, not what the file is -- metadata,
-- not validation.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET_ID.image_features` AS
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS file,
  ML.CONVERT_IMAGE_TYPE(
    ML.CONVERT_COLOR_SPACE(
      ML.RESIZE_IMAGE(ML.DECODE_IMAGE(data), 4, 4, FALSE),
      'GRAYSCALE')) AS features
FROM `PROJECT_ID.DATASET_ID.image_object_table`
WHERE content_type IN ('image/png', 'image/jpeg');
-- Write to a table rather than selecting the struct: a 4000x3000 photo
-- decodes to 36 million doubles, and the resize belongs inside the same
-- statement that reads `data` so the large intermediate never materializes.
