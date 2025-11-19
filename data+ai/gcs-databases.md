# Google Cloud Databases: An Overview

Google Cloud offers a comprehensive portfolio of fully managed database services, designed to meet the needs of any application, from transactional to analytical, at any scale. These services provide the flexibility, reliability, and performance required for modern cloud-native applications, while also offering seamless integration with Google Cloud's broader ecosystem of data analytics and machine learning services.

## Comparison Table

| Service | Type | Good For | Scale | Consistency Model |
|---|---|---|---|---|
| [Google Cloud Storage (GCS)](#google-cloud-storage-gcs) | Object | Unstructured data, blobs, media, backups | Petabytes+ | Strong |
| [BigQuery](#bigquery) | Analytical | Data warehousing, SQL analytics | Petabytes+ | ACID (within a single statement) |
| [Cloud SQL](#cloud-sql) | Relational | Traditional applications, OLTP | Terabytes | ACID |
| [AlloyDB for PostgreSQL](#alloydb-for-postgresql) | Relational | High-performance PostgreSQL, OLTP, OLAP | Terabytes | ACID |
| [Cloud Spanner](#cloud-spanner) | Relational | Global-scale, mission-critical applications, OLTP | Petabytes+ | External, Strong |
| [Cloud Bigtable](#cloud-bigtable) | NoSQL Wide-column | Large-scale, low-latency applications, time-series data | Petabytes+ | Eventual (within a cluster), Strong (within a single row) |
| [Firestore](#firestore) | NoSQL Document | Mobile and web applications, real-time data | Petabytes+ | Strong |
| [Memorystore](#memorystore) | In-memory | Caching, session management, real-time leaderboards | Gigabytes | N/A (depends on engine) |

## Table of Contents

- [Google Cloud Storage (GCS)](#google-cloud-storage-gcs)
- [BigQuery](#bigquery)
- [Cloud SQL](#cloud-sql)
- [AlloyDB for PostgreSQL](#alloydb-for-postgresql)
- [Cloud Spanner](#cloud-spanner)
- [Cloud Bigtable](#cloud-bigtable)
- [Firestore](#firestore)
- [Memorystore](#memorystore)

## Google Cloud Storage (GCS)

Google Cloud Storage is a unified object storage service that is scalable, durable, and highly available. It's a great choice for storing a wide variety of data, including unstructured data, backups, and large media objects.

- [Product Page](https://cloud.google.com/storage)
- [Documentation](https://cloud.google.com/storage/docs)

### GCS Architecture

Google Cloud Storage is organized in a hierarchical structure:

```
Project
  └── Bucket (global, regional, or multi-regional resource, scales automatically)
      └── Object
```

*   **Project:** A top-level container for all your Google Cloud resources.
*   **Bucket:** A container for your data. Buckets have a globally unique name and are created in a specific geographic location (regional, dual-regional, or multi-regional). GCS automatically scales the I/O capacity of a bucket in response to request rates.
*   **Object:** The individual pieces of data that you store in a bucket. Objects are immutable, and versioning can be enabled to keep a history of object modifications.
### Data Schema

Cloud Storage does not enforce any particular data schema. It is an object store, and you can store data in any format you choose. However, the data you store in Cloud Storage is typically unstructured or semi-structured. Common formats include CSV, JSON, Parquet, Avro, and various image and video formats.

### Data Ingress, Querying, and Egress

**Data Ingress:**

*   **`gsutil` CLI:** The `gsutil` command-line tool is a popular way to upload and download files and manage buckets and objects.
*   **Cloud Console:** You can drag and drop files to upload them to a bucket in the Google Cloud Console.
*   **Client Libraries:** Use the Cloud Storage client libraries to upload data from your application.
*   **Storage Transfer Service:** For large-scale online data transfers from other cloud providers or on-premises storage.
*   **Transfer Appliance:** A physical appliance you can use to securely migrate large volumes of data (hundreds of terabytes to a petabyte) to Google Cloud.

**Querying Data:**

While GCS is an object store and doesn't have a built-in query engine, you can query data in GCS in a few ways:

*   **BigQuery Federation:** You can create an external table in BigQuery that points to your data in GCS. This allows you to use SQL to query your data without loading it into BigQuery.
*   **Dataproc:** You can use Dataproc to run Spark or Hadoop jobs that process and analyze data in GCS.

**Data Egress:**

*   **`gsutil` CLI:** Download files and objects to your local machine.
*   **Cloud Console:** Download files directly from the console.
*   **Client Libraries:** Read data from GCS in your application.

## AlloyDB for PostgreSQL

AlloyDB is a fully managed, PostgreSQL-compatible database service for your most demanding enterprise database workloads. AlloyDB combines the best of Google with one of the most popular open-source database engines, PostgreSQL, for superior performance, scale, and availability.

- [Product Page](https://cloud.google.com/alloydb)
- [Documentation](https://cloud.google.com/alloydb/docs)

### AlloyDB Architecture

AlloyDB is organized in a hierarchical structure:

```
Cluster (regional resource)
  ├─ Instance (PRIMARY, read/write, e.g., Zone A)
  │   ├─ Compute (scales vertically, e.g., 2 to 128 vCPUs)
  │   └─ Storage (scales automatically up to 64 TB)
  └─ Instance (READ POOL, read-only replica, e.g., Zone B)
      ├─ Compute (scales vertically and horizontally)
      └─ ... (add more read pool instances for scaling)
```

**Cluster**: A regional resource that contains instances and defines networking.
- Multi-zone high availability support
- Automated backups and point-in-time recovery
- VPC network configuration
- User authentication settings

**Instance**: A compute resource that runs PostgreSQL.
- **PRIMARY**: The read/write instance, required, and only one per cluster.
- **READ POOL**: Read-only replicas for scaling reads. Optional, and you can have multiple.
- CPU and memory configuration (from 2 to 128 vCPUs) - scales vertically
- Availability type: ZONAL (single zone) or REGIONAL (multi-zone HA)
- You can add more read pool instances to scale reads horizontally.

**Database**: A PostgreSQL database within an instance.
- Multiple databases per instance.
- Standard PostgreSQL database features.
- Extensions and configuration options.

### Data Schema

AlloyDB is 100% compatible with standard PostgreSQL. You define your schema using standard PostgreSQL DDL (Data Definition Language) commands to create tables, specify columns and their data types, and define constraints. AlloyDB supports all PostgreSQL data types.

### Data Ingress, Querying, and Egress

**Data Ingress:**

*   **Standard PostgreSQL Tools:** Use standard PostgreSQL tools like `psql` and `pg_dump` to connect to the database and import data.
*   **Database Migration Service (DMS):** Use DMS for continuous, real-time replication from a source database to AlloyDB. DMS uses a full dump phase followed by a change data capture (CDC) phase.
*   **Dataflow:** Use Dataflow Flex Templates to load batch data from Google Cloud Storage (GCS) into AlloyDB tables.

**Querying Data:**

*   **Standard SQL:** Connect to your AlloyDB instance using any standard PostgreSQL client and use standard SQL for queries.
*   **Columnar Engine:** AlloyDB's adaptive columnar engine automatically chooses the best query plan for for analytical queries, providing up to 100x faster performance than standard PostgreSQL.
*   **Vertex AI Integration:**  Execute ML predictions directly from SQL using built-in integration with Vertex AI.

**Data Egress:**

*   **Standard PostgreSQL Tools:** Use `pg_dump` to export data from your AlloyDB database.
*   **Application Code:** Connect to the database from your application and retrieve data using standard PostgreSQL libraries.
*   **Export to GCS:** You can export query results or entire tables to Google Cloud Storage in various formats like CSV.

### AlloyDB Capabilities

**Performance:**
- ✅ **4x faster** than standard PostgreSQL for transactional workloads
- ✅ **100x faster** for analytical queries (columnar engine)
- ✅ Intelligent caching and query optimization
- ✅ Sub-millisecond latency for point queries

**AI & ML Integration:**
- ✅ **Built-in Vertex AI integration** for ML predictions from SQL
- ✅ **Vector search** with `pgvector` and ScaNN extensions
- ✅ **Embedding generation** directly in database
- ✅ Call any Vertex AI endpoint or deployed model

**Scalability:**
- ✅ Scale compute independently (2-128 vCPUs)
- ✅ Scale storage automatically (up to 64 TB)
- ✅ Read pool replicas for horizontal read scaling
- ✅ Connection pooling with PgBouncer

**High Availability:**
- ✅ Multi-zone REGIONAL instances (99.99% SLA)
- ✅ Automatic failover (typically < 60 seconds)
- ✅ Continuous backups and point-in-time recovery
- ✅ Cross-region replication (optional)

**PostgreSQL Compatibility:**
- ✅ 100% compatible with PostgreSQL
- ✅ Support for PostgreSQL extensions (pgvector, PostGIS, etc.)
- ✅ Standard SQL and PostgreSQL tools work seamlessly
- ✅ Easy migration from existing PostgreSQL databases

### Scaling AlloyDB

AlloyDB offers flexible scaling options for different workload needs:

**Vertical Scaling (Compute):**
- **Development/Test**: 2 vCPUs, 16 GB RAM
- **Small Production**: 4-8 vCPUs, 32-64 GB RAM
- **Medium Production**: 16-32 vCPUs, 128-256 GB RAM
- **Large Production**: 64-128 vCPUs, 512-864 GB RAM
- Scale up/down with minimal downtime

**Horizontal Scaling (Read Replicas):**
- Add **READ POOL instances** to distribute read traffic
- Each replica can have different CPU/memory configurations
- Automatic load balancing across replicas
- Replicas stay in sync (sub-second replication lag)

**Storage Scaling:**
- Automatically grows as needed (up to 64 TB)
- No manual provisioning required
- Instant expansion without downtime

## BigQuery

BigQuery is a fully managed, serverless data warehouse that enables super-fast SQL queries using the processing power of Google's infrastructure. It's designed for large-scale data analytics.

- [Product Page](https://cloud.google.com/bigquery)
- [Documentation](https://cloud.google.com/bigquery/docs)

### BigQuery Architecture

BigQuery is organized in a hierarchical structure:

```
Project
  └── Dataset (regional or multi-regional resource)
      ├── Tables (columnar storage, scales automatically)
      │   ├── Internal
      │   ├── External
      │   └── Materialized Views
      └── Views
```

*   **Project:** A top-level container for all your Google Cloud resources.
*   **Dataset:** A logical container for tables and views. A dataset is created in a specific geographic location (a region or a multi-region).
*   **Tables:** The fundamental unit for storing data in BigQuery. Storage scales automatically as your data grows.
    *   **Internal Tables:** Native BigQuery tables that are stored in Colossus.
    *   **External Tables:** Tables that read data directly from external sources like Google Cloud Storage, Bigtable, Spanner, or Google Sheets.
    *   **Materialized Views:** Precomputed views that periodically cache the results of a query for increased performance and efficiency.
*   **Views:** A virtual table defined by a SQL query. A view does not store any data.

BigQuery's architecture is serverless and separates compute and storage, allowing them to scale independently and automatically. It is built on the following Google technologies:

*   **Colossus:** Google's global, distributed file system that stores data in a columnar format called Capacitor. Storage scales automatically.
*   **Dremel:** The query execution engine that processes SQL queries in parallel across thousands of machines. Compute scales automatically based on query complexity.
*   **Borg:** Google's cluster management system that allocates and manages the resources for Dremel jobs.
*   **Jupiter:** Google’s high-speed network that allows for rapid data movement between storage and compute.

### Data Schema

BigQuery uses a schema to define the structure of the data in a table. The schema is specified when you create a table and consists of a list of column definitions. Each column definition includes a column name, a data type, and an optional description.

BigQuery supports a variety of data types, including:

*   **Standard SQL data types:** `STRING`, `BYTES`, `INTEGER`, `FLOAT`, `NUMERIC`, `BOOLEAN`, `TIMESTAMP`, `DATE`, `TIME`, `DATETIME`, `INTERVAL`
*   **Complex data types:** `ARRAY`, `STRUCT`

### Data Ingress, Querying, and Egress

**Data Ingress:**

*   **Batch Loading:** Load large datasets from files in Cloud Storage (CSV, JSON, Avro, Parquet, ORC) or other sources. The BigQuery Data Transfer Service can automate this process.
*   **Streaming Ingestion:** Stream data in real-time using the Storage Write API, which provides exactly-once delivery semantics.
*   **Federated Queries:** Query data in external sources like Cloud Storage, Bigtable, Spanner, or Google Sheets without loading it into BigQuery.
*   **Datastream:** Replicate data changes from relational databases into BigQuery in near real-time.

**Querying Data:**

*   **Standard SQL:** BigQuery supports a standard SQL dialect (ANSI SQL 2011 compliant) for querying data.
*   **BigQuery UI/CLI/API:** Run queries through the Google Cloud Console, the `bq` command-line tool, or the BigQuery REST API.
*   **BI & Visualization Tools:** Connect to BigQuery from popular business intelligence and data visualization tools like Looker, Tableau, and Power BI.
*   **BigQuery ML:** Create and execute machine learning models in BigQuery using SQL queries.

**Data Egress:**

*   **Export to Cloud Storage:** Export large datasets from BigQuery tables to Cloud Storage in various formats.
*   **Storage Read API:** Efficiently read and stream data from BigQuery tables to other applications or services.
*   **Connectors:** Use connectors to read data from BigQuery in services like Dataflow or Dataproc.
*   **BigQuery BI Engine:** A fast, in-memory analysis service that accelerates query performance for BI use cases.

## Cloud SQL

Cloud SQL is a fully managed relational database service that makes it easy to set up, maintain, manage, and administer your relational MySQL, PostgreSQL, and SQL Server databases in the cloud.

- [Product Page](https://cloud.google.com/sql)
- [Documentation](https://cloud.google.com/sql/docs)

### Cloud SQL Versions and Architecture

Cloud SQL is organized in a hierarchical structure:

```
Instance (regional resource)
  ├─ Primary (read/write, e.g., Zone A)
  │   └─ Compute (scales vertically)
  ├─ Standby (HA replica, e.g., Zone B)
  │   └─ Compute (matches primary)
  └─ Read Replica (read-only, e.g., Zone C)
      ├─ Compute (scales vertically and horizontally)
      └─ ... (add more read replicas for scaling)
```

*   **Instance:** A virtual machine running a specific database engine (MySQL, PostgreSQL, or SQL Server).
    *   **Primary Instance:** The main instance that handles all read and write operations. You can scale the vCPU and memory of the primary instance vertically.
    *   **Standby Instance:** In a high availability configuration, a standby instance is created in a different zone. Data is synchronously replicated to the standby instance.
    *   **Read Replicas:** You can create one or more read replicas to scale out read traffic. Data is asynchronously replicated to read replicas. You can scale read replicas vertically and horizontally.
*   **Database:** A logical container for your data.
*   **Schema:** A namespace for database objects like tables and views.

### Data Schema

Cloud SQL uses the standard schema of the database engine you choose (MySQL, PostgreSQL, or SQL Server). You define your schema using standard SQL DDL (Data Definition Language) commands to create tables, specify columns and their data types, and define constraints.

### Data Ingress, Querying, and Egress

**Data Ingress:**

*   **SQL Dump Files:** Import data from SQL dump files in Cloud Storage.
*   **CSV Files:** Import data from CSV files.
*   **Database Migration Service (DMS):** Migrate your databases to Cloud SQL from on-premises or other clouds with minimal downtime.

**Querying Data:**

*   **Standard SQL:** Connect to your Cloud SQL instance using any standard client for your database engine and use standard SQL.
*   **Cloud SQL Studio:** Use the interactive SQL editor in the Google Cloud Console.
*   **BigQuery Federation:** Query your Cloud SQL data directly from BigQuery without copying or moving data.

**Data Egress:**

*   **SQL Dump Files:** Export your data to SQL dump files in Cloud Storage.
*   **CSV Files:** Export your data to CSV files.
*   **Database Client Tools:** Use standard database tools to export data.

## Cloud Bigtable

Cloud Bigtable is a fully managed, scalable NoSQL wide-column store that is ideal for large analytical and operational workloads with low latency. It supports the popular open-source HBase API standard.

- [Product Page](https://cloud.google.com/bigtable)
- [Documentation](https://cloud.google.com/bigtable/docs)

### Cloud Bigtable Architecture

Bigtable is organized in a hierarchical structure:

```
Instance (logical container)
  ├─ Cluster (regional resource, e.g., us-east1)
  │   ├─ Node (compute, Zone A)
  │   ├─ Node (compute, Zone B)
  │   └─ ... (scales horizontally by adding/removing nodes)
  ├─ Cluster (optional replication, e.g., us-west1)
  │   ├─ Node (compute, Zone A)
  │   ├─ Node (compute, Zone B)
  │   └─ ...
  └─ Table (data, replicated across all clusters)
      ├─ Tablet (distributed across nodes)
      ├─ Tablet
      └─ ...
```

*   **Instance:** A logical container for your clusters and tables. An instance can have one or more clusters, enabling multi-region replication.
*   **Cluster:** A regional resource that handles read and write requests. You can add clusters to an instance for replication to improve availability and durability. Each cluster can be in a different region.
*   **Nodes:** The compute resources within a cluster that manage tablets. Scaling is achieved by adding or removing nodes. Bigtable offers autoscaling to automatically adjust the number of nodes based on CPU and storage utilization.
*   **Tablets:** Tables are divided into contiguous blocks of rows called tablets. Tablets are the unit of load balancing and are distributed among the nodes in a cluster.


### Data Schema

Bigtable is a sparsely populated table that can scale to billions of rows and thousands of columns. It is a key/value store, and each value is indexed by a row key, column key, and a timestamp.

*   **Row key:** A unique identifier for a row.
*   **Column family:** A group of related columns.
*   **Column qualifier:** A unique identifier for a column within a column family.
*   **Timestamp:** The time at which the data was written.

Bigtable does not support joins or multi-row transactions.

### Data Ingress, Querying, and Egress

**Data Ingress:**

*   **Dataflow:** Use Dataflow to read data from various sources, transform it, and write it to Bigtable.
*   **Dataproc:** Use Dataproc to run Hadoop MapReduce jobs or Spark jobs that write data to Bigtable.
*   **`cbt` CLI:** Use the `cbt` command-line tool to import data from CSV files.
*   **Client Libraries:** Use the Bigtable client libraries for Go, Java, Python, and other languages to write data from your application.

**Querying Data:**

*   **Client Libraries:** The primary way to read data from Bigtable is through the client libraries, which allow you to read a single row or a range of rows.
*   **`cbt` CLI:** Use the `cbt` tool for simple reads and scans from the command line.
*   **BigQuery Federation:** You can query Bigtable data from BigQuery by creating an external table, which allows you to use SQL for analytical queries.

**Data Egress:**

*   **Dataflow:** Export data from Bigtable to other storage systems like Cloud Storage or BigQuery.
*   **Dataproc:** Read data from Bigtable in Hadoop or Spark jobs for processing and export.
*   **Client Libraries:** Programmatically read data from Bigtable and write it to another destination.

## Cloud Spanner

Cloud Spanner is a globally distributed, strongly consistent, relational database service that combines the benefits of relational databases with the horizontal scalability of NoSQL databases.

- [Product Page](https://cloud.google.com/spanner)
- [Documentation](https://cloud.google.com/spanner/docs)

### Cloud Spanner Architecture

Spanner is organized in a hierarchical structure:

```
Instance (regional or multi-regional resource)
  ├─ Node (compute, e.g., Zone A)
  ├─ Node (compute, e.g., Zone B)
  ├─ Node (compute, e.g., Zone C)
  │   └─ ... (scales horizontally by adding/removing nodes)
  └─ Database
      └── Schema
          ├── Tables
          │   └── Interleaved Tables
          └── Views
```

*   **Instance:** A container for databases. An instance defines the geographic configuration (regional or multi-regional) and compute capacity in nodes or processing units. You can scale the compute capacity by adding or removing nodes.
*   **Database:** A container for tables, views, and indexes. It also defines the SQL dialect (GoogleSQL or PostgreSQL).
*   **Schema:** A namespace for database objects.
*   **Tables:** Structured with rows and columns, and a primary key.
    *   **Interleaved Tables:** A parent-child relationship can be defined between tables to co-locate related rows for improved performance.
*   **Views:** A virtual table defined by a SQL query.

Spanner's architecture is built for global scale and high availability, with decoupled compute and storage. It uses the following Google technologies:

*   **Colossus:** Google's distributed file system for storing data.
*   **Paxos:** A consensus algorithm for replicating data across multiple zones to ensure high availability and strong consistency.
*   **TrueTime:** A globally distributed clock that provides globally consistent timestamps to transactions.

### Data Schema

Spanner has a relational data model. You define a schema for your database using Spanner's data definition language (DDL), which is similar to standard SQL. The schema defines tables, columns, indexes, and relationships between tables.

Spanner supports a variety of data types, including:

*   **Scalar types:** `BOOL`, `INT64`, `FLOAT64`, `STRING`, `BYTES`, `DATE`, `TIMESTAMP`
*   **Array type:** `ARRAY<T>`, where `T` is a non-array type.

### Data Ingress, Querying, and Egress

**Data Ingress:**

*   **DML Statements:** Use standard SQL DML statements (`INSERT`, `UPDATE`, `UPSERT`) to write data to Spanner.
*   **Dataflow:** For large-scale data ingestion, use Dataflow to read from sources like Avro files in Cloud Storage and write to Spanner.
*   **Spanner Change Streams:** Capture and stream data changes in real-time to other services for analytics or other purposes.

**Querying Data:**

*   **SQL:** Spanner supports two SQL dialects: GoogleSQL and PostgreSQL.
*   **Client Libraries:** Use the Spanner client libraries to execute queries and read data from your application.
*   **Spanner Studio:** The Google Cloud Console provides a web-based interface for running SQL queries.
*   **Partitioned DML:** For bulk updates or deletes, you can use Partitioned DML to parallelize the work across multiple transactions.

**Data Egress:**

*   **Dataflow:** Use Dataflow to read data from Spanner and export it to other destinations like Cloud Storage or BigQuery.
*   **Spanner to Avro/CSV:** You can export Spanner databases to Cloud Storage in Avro or CSV format.
*   **Client Libraries:** Programmatically read data from Spanner and write it to another location.

## Firestore

Firestore is a flexible, scalable NoSQL document database for mobile, web, and server development from Firebase and Google Cloud. It keeps your data in sync across client apps through real-time listeners and offers offline support for mobile and web so you can build responsive apps that work regardless of network latency or Internet connectivity.

- [Product Page](https://cloud.google.com/firestore)
- [Documentation](https://cloud.google.com/firestore/docs)

### Firestore Architecture

Firestore is organized in a hierarchical structure:

```
Project
  └── Database (regional or multi-regional, scales automatically)
      └── Collection
          └── Document
              └── Subcollection
                  └── Document
```

*   **Project:** A top-level container for all your Google Cloud resources.
*   **Database:** A container for your collections. It can be a regional or multi-regional resource and scales automatically to handle the load of your application.
*   **Collection:** A container for documents.
*   **Document:** The basic unit of storage. Documents are lightweight records that contain fields, which map to values.
*   **Subcollection:** A collection that is associated with a specific document.

Firestore is a serverless, document-oriented database that scales automatically. It offers real-time data synchronization and offline support.
### Data Schema

Firestore is a NoSQL, document-oriented database. Unlike a SQL database, there are no tables or rows. Instead, you store data in *documents*, which are organized into *collections*.

Each document contains a set of key-value pairs. Firestore is schema-less, so you don't need to define a schema for your collections. However, it's a good practice to use a consistent data structure for the documents in a collection.

### Data Ingress, Querying, and Egress

**Data Ingress:**

*   **Client SDKs:** The primary way to add data to Firestore is through the client SDKs (for Web, iOS, Android, and more).
*   **Server Client Libraries:** You can also use server client libraries (for Node.js, Java, Python, Go, etc.) to add data.
*   **Setting Data:** You can set the data of a document within a collection, specifying a document ID.
*   **Adding Data:** You can add a new document to a collection, and Firestore will automatically generate the document ID.

**Querying Data:**

*   **Get a document:** You can retrieve a single document from a collection.
*   **Get multiple documents:** You can retrieve all documents in a collection or a subset of documents.
*   **Simple and Compound Queries:** You can perform simple queries to filter and order your data. You can also chain filters to create more specific compound queries.
*   **Real-time Listeners:** You can add a real-time listener to your app, which will be notified of any data changes.

**Data Egress:**

*   **Managed Export and Import:** You can export your Firestore data to a Google Cloud Storage bucket. From there, you can use other services like BigQuery to analyze the data.
*   **Client SDKs/Server Client Libraries:** You can read data from Firestore and then do what you want with it in your application.

## Memorystore

Memorystore is a fully managed in-memory data store service for Redis and Memcached at any scale. It automates the complex tasks of provisioning, replication, failover, and patching so you can spend more time on your application.

- [Product Page](https://cloud.google.com/memorystore)
- [Documentation](https://cloud.google.com/memorystore/docs)

### Memorystore Versions and Architecture

Memorystore is organized in a hierarchical structure:

```
Instance (regional resource)
  ├─ Primary (read/write, e.g., Zone A)
  │   └─ Compute (scales vertically)
  └─ Read Replica (read-only, e.g., Zone B)
      ├─ Compute (scales vertically and horizontally)
      └─ ... (add more read replicas for scaling)

Instance (Redis Cluster)
  ├─ Shard 1
  │   ├─ Primary
  │   └─ Replica
  ├─ Shard 2
  │   ├─ Primary
  │   └─ Replica
  └─ ... (scales horizontally by adding/removing shards)
```

*   **Instance:** A Redis, Memcached, or Valkey instance. It is a regional resource.
    *   **Memorystore for Redis and Memcached:**
        *   **Basic Tier:** A standalone instance.
        *   **Standard Tier:** A primary instance with a replica in a different zone for high availability. You can scale vertically by increasing the instance size, and scale reads horizontally by adding read replicas.
    *   **Memorystore for Redis Cluster:** A Redis Cluster instance that is composed of shards. You can scale horizontally by adding or removing shards.
*   **Shards:** Each shard is composed of a primary node and up to two replica nodes.
*   **Nodes:** The compute resources within an instance or shard.
### Data Schema

Memorystore for Redis and Memcached are key-value stores and do not enforce a schema. You can store any data you want in the values, but it is up to your application to interpret the data.

### Data Ingress, Querying, and Egress

**Data Ingress:**

*   **Redis/Memcached Clients:** Use any standard Redis or Memcached client to connect to your Memorystore instance and write data.
*   **Import RDB files (Redis):** You can import data into a Memorystore for Redis instance from an RDB file in Cloud Storage.

**Querying Data:**

*   **Redis/Memcached Commands:** Use the standard Redis or Memcached commands and data structures to query your data.
*   **Vector Search (Redis):** Memorystore for Redis supports vector search capabilities, allowing you to perform similarity searches on vector embeddings.

**Data Egress:**

*   **Redis/Memcached Clients:** Read data from your instance using a standard client.
*   **Export RDB files (Redis):** You can export a snapshot of your Memorystore for Redis instance to an RDB file in Cloud Storage.
