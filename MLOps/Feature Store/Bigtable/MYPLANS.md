![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FFeature+Store%2FBigtable&file=MYPLANS.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%20Store/Bigtable/MYPLANS.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Bigtable/MYPLANS.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Bigtable/MYPLANS.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Bigtable/MYPLANS.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Bigtable/MYPLANS.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/Bigtable/MYPLANS.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/Bigtable/MYPLANS.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# **Course: Building a High-Performance Feature Store with BigQuery & Bigtable**

## **Course Objective**

To design, implement, and optimize a production-grade Feature Store that leverages BigQuery for analytical feature engineering and Bigtable for low-latency online inference.

## **Prerequisites (Step 0): The Data Source Foundation**

Before the first lesson, we establish the source datasets in BigQuery.

* **Table A (Dense):** 1 row per entity. Contains 200+ features of varying types (INT64, FLOAT64, ARRAY, STRUCT, JSON, GEOGRAPHY).  
* **Table B (Sparse/Time-Series):** Multiple rows per entity defined by entity\_id and timestamp.  
* **Goal:** Understand the "impedance mismatch" between BigQuery's analytical format and Bigtable's key-value format.

## **Module 1: The "Vision" \- Your First Serving Layer**

**Goal:** Get features into Bigtable immediately to see the end-to-end flow.

* **The "Native" Push:** Using EXPORT DATA (Reverse ETL) to move a subset of Table A to Bigtable.  
* **Instant Serving:** A simple Python/Go script to fetch a feature by rowkey.  
* **Visualizing Success:** Introduction to the **Bigtable Key Visualizer** to see the initial data distribution.  
* **Latency Baseline:** Measure the "Native" read latency (p99) for a single entity.

## **Module 2: The Payload (Packaging & Serialization)**

**Goal:** Compare methods of storing data within a cell and making them "Self-Describing."

* **Methods Lab:**  
  * **Native:** Mapping BQ columns to Bigtable Qualifiers.  
    * **Self-Description:** Using a specific Column Family (e.g., metadata) to store a JSON map of qualifier names to data types.  
  * **Casting:** Storing JSON strings (The "Quick & Dirty" method).  
    * **Self-Description:** Embedding a \_schema\_version key within the JSON blob itself.  
  * **Concatenation:** Using SQL CONCAT with delimiters (e.g., |) for a single-column read.  
    * **Self-Description:** Storing a "header" column (e.g., schema\_def) that contains the ordered list of feature names used in the concatenation.  
  * **Protobuf:** Compiling BQ rows into binary blobs (The "Gold Standard").  
    * **Self-Description:** Storing the serialized FileDescriptorSet (the .proto definition) in a reserved row (e.g., \_SCHEMA\_\#VERSION\_1) or a dedicated metadata column.  
  * **Hybrid:** Native for top-10 features, Protobuf for the remaining 190\.  
    * **Self-Description:** A multi-column approach where a manifest column describes which features are in the clear and which are in the binary blob.  
* **The "Tax" Analysis:**  
  * Compare **Storage Size** (Native vs. Concatenated vs. Protobuf).  
  * Compare **Read Latency** (Network transfer time vs. Client-side Deserialization/Parsing CPU time).  
  * **The Delimiter Trap:** Discussion on data integrity and why concatenation is risky for production.

## **Module 3: Synchronization & Propagation**

**Goal:** Timing the "Freshness" of features.

* **Sync Patterns:**  
  * **One-time:** Manual EXPORT for backfilling.  
  * **Scheduled:** BQ Data Transfer Service / Scheduled Queries (latency in minutes/hours).  
  * **Continuous:** Using BQ Change Data Capture (CDC) or Pub/Sub → Dataflow (latency in seconds).  
* **The Propagation Race:** Students modify a value in BQ and measure how long it takes to reflect in the Bigtable Serving Layer across all three methods.

## **Module 4: History & Time-Travel**

**Goal:** Managing point-in-time features for training vs. serving.

* **Design Choice A: History in the Key:** entity\_id\#timestamp.  
  * *Pros:* Range scans for training data.  
  * *Cons:* Manual Garbage Collection; potential hotspotting.  
* **Design Choice B: Cell Versioning:** entity\_id as key, multiple versions per cell.  
  * *Pros:* Cleanest for inference; automatic GC (Max Versions).  
* **Lab:** Implementing a "Point-in-Time" join using Bigtable Filters.

## **Module 5: Write-Path Optimization & Bypassing BQ**

**Goal:** Handling high-frequency updates and preventing "Double Writes."

* **Direct Writes:** Writing "Streaming Features" (e.g., clicks in the last 30 seconds) directly to Bigtable.  
* **The Dual-Write Challenge:** \* Pattern 1: App → Pub/Sub → (Dataflow) →![][image1]  
  .  
  * Pattern 2: App → Bigtable → (Change Stream) → BQ.  
* **Idempotency:** How to ensure a retry in the pipeline doesn't create duplicate versions or incorrect feature states.

## **Module 6: Multi-Tenant & Multi-Table Management**

**Goal:** Organizing thousands of features for hundreds of models.

* **The "Single Table" Philosophy:** Managing multiple feature groups in one table using Column Families.  
* **Key Namespacing:** Prefixing keys (e.g., USER\#123 vs PROD\#456).  
* **The Ordering Problem:** In Hybrid/Partial updates, how to ensure features updated at different frequencies are correctly merged at the client side without "Version Skew."

## **Module 7: Schema Evolution & Deprecation**

**Goal:** Maintaining the Feature Store over time.

* **The Change Log:** What happens when a feature is dropped or renamed?  
* **Versioned Protobufs:** Using "Feature Metadata" columns to tell the serving app how to decode the payload.  
* **Backfilling:** Strategies for updating historical features in Bigtable without interrupting live inference traffic.

## **Module 8: Observability & Production Readiness**

**Goal:** Detecting "Hotspots" before they crash the model.

* **Monitoring:** Using Cloud Monitoring for Disk Utilization vs. CPU.  
* **Key Visualizer Deep Dive:** Identifying "Sequential Keys" and "Hot Rows."  
* **Cost Optimization:** When to move from SSD to HDD (spoiler: almost never for Feature Stores) and how to scale nodes based on throughput.

## **Final Project**

**Challenge:** Build a real-time recommendation engine feature store.

* **Source:** BQ Dense User Table \+ BQ Sparse Transaction Table.  
* **Requirement:** Sub-10ms p99 read latency, support for 1000 requests/sec, and a documented plan for adding a new feature without downtime.

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAtCAYAAAATDjfFAAAC7ElEQVR4Xu3czYtNYRwH8CEvGyxkUtN9mVNXw2wshggJKQsLdvZK/AFSys7GAgvlJZSkhuxFxEIWWHiJrJAsFIvBRkni93TPydNxx4y3ze3zqV/nPL/nOS/Lb/eecwYGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAe2u32t7LeRT2KujM8PLx7bGxsdm3diaiXUUejHrRarbX5/N+I830q7+Fj1LO4/v10nWz+xmQV07OyUwEA9KcUkgYHB+eVw5lleDpbzUeAWhXjYyMjI/PTOMLauRh/qeb/hXTNOO++bPw2rru03B8vimJ9p9OZG/sT6T5i7bqYP//jDAAAfSpCz/YUlvJeGdhelPsfY831fL7sP4kAtaDez8Vxq+u9yaSAFpuZ2fhM1M44x6GstzNqbzWOuQ3VPgBA34oAdGSSwLY121+TzycpxBVFsbzez003sDUajYVxjYt5L8YfYjMrtoez3oVms7kiG2+q9gEA+lYZyNKzaTdarda9qNfZ3IH8b8pK+mUtHVfv1003sMW5TkfdSvdQ1sTQ0NCiHuumvCYAQN8pA1tRjdOzbCkwlXN3Go3Gkh+ruyLEXYu5rz3667LQleputn91dHR0Tv2YpFcQm24PAKDvtctn1bLxsqgHaT+9XNBsNlfm8+Wa9ILAyXq/7jd+YfspiPXozYje+1oPAKC/tbsP9e+pxhHCTuVBqdPpDMb4YVEU7YHu82Qbo56nZ86qNb8yzcCWgtibahDHbEt/y9Y/G5L+mo25/XkPAKCvRUh6msJZ1Oeox+3uN9AuRyjakq8b7n4T7VVsd8R2PILTrtSf6g3RZKrAFue7GfUh3UesvZ3CYLv7N+rBak1cb3OMJ8p7/RLjS/k5AADIpDc0IzQdj3pR/7BuL0VRLK73AAD4zyKsXan3AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPhz3wE+wKrdOohHKwAAAABJRU5ErkJggg==>