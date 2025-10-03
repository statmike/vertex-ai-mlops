# build on the vector search index created by rag-engine-vector-search.py

import os, re, subprocess, string
from collections import Counter
from google.cloud import storage
from google.cloud import aiplatform
from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import HybridQuery
import vertexai
from vertexai.preview import rag
#from vertexai import rag
import pandas as pd
from google import genai
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi
import nltk
import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM

# static variable definitions
LOCATION = 'us-east4' #'us-central1'
TOPICS = ['applied-genai', 'rag-engine', 'vertex-vector-search']

# derived variables & client setup
PROJECT_ID = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True).stdout.strip()
aiplatform.init(project=PROJECT_ID, location=LOCATION)
vertexai.init(project = PROJECT_ID, location = LOCATION)
storage_client = storage.Client(project=PROJECT_ID)
genai_client = genai.Client(vertexai = True, project = PROJECT_ID, location = LOCATION)

# Vertex Vector Search

# retrieve vertex vector search streaming index 
INDEX_NAME = '-'.join(TOPICS + ['streaming-index'])
indexes = aiplatform.MatchingEngineIndex.list(filter=f'display_name="{INDEX_NAME}"')
vvs_index = None
if indexes:
    vvs_index = indexes[0]
    print(f'Found existing index with name {vvs_index.display_name}')
else:
    print(f'Warning: Index "{INDEX_NAME}" not found. Please create it first using rag-engine-vector-search.py.')
    
# retrieve vertex vector search endpoint
ENDPOINT_NAME = '-'.join(TOPICS + ['endpoint'])
endpoints = aiplatform.MatchingEngineIndexEndpoint.list(filter=f'display_name="{ENDPOINT_NAME}"')
vvs_endpoint = None
if endpoints:
    vvs_endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoints[0].resource_name)
    print(f"Found existing endpoint: {vvs_endpoint.display_name}")
else:
    print(f'Warning: Endpoint "{ENDPOINT_NAME}" not found. Please create it first using rag-engine-vector-search.py.')


# Get deployed index
deployed_index_id = None
is_deployed = False
if vvs_index and vvs_endpoint:
    deployed_index_id = vvs_index.display_name.replace('-', '_')

    if deployed_index_id in [i.id for i in vvs_endpoint.deployed_indexes]:
        is_deployed = True
        print(f"Index '{vvs_index.display_name}' is already deployed to endpoint '{vvs_endpoint.display_name}'.")
        print("\nDeployment Details:")
        print(f"\tIndex: {vvs_index.resource_name}")
        print(f"\tEndpoint: {vvs_endpoint.resource_name}")
        print(f"\tDeployed Index ID: {deployed_index_id}")
    else:
        print(f"Warning: Index '{vvs_index.display_name}' is not deployed to endpoint '{vvs_endpoint.display_name}'. Please deploy it first using rag-engine-vector-search.py.")

else:
    if not vvs_index:
        print("Index not found, skipping deployment check.")
    if not vvs_endpoint:
        print("Endpoint not found, skipping deployment check.")

# RAG Engine: retrieve/create a corpus
CORPUS_NAME = '-'.join(TOPICS)

corpora = rag.list_corpora()
corpus = next((c for c in corpora if c.display_name == CORPUS_NAME), None)
if corpus:
    print(f"Found existing corpus: {corpus.display_name}")
else:
    print(f'Warning: Corpus "{CORPUS_NAME}" not found. Please create it first using rag-engine-vector-search.py.')

# Retrieval Options
query = "How big is second base?"


# Context Retrieval - Chunks
matches = rag.retrieval_query(
    rag_resources = [
        rag.RagResource(rag_corpus = corpus.name)
    ],
    text = query,
    rag_retrieval_config = rag.RagRetrievalConfig(
        top_k = 20,  # Optional
        filter = rag.Filter(vector_distance_threshold = 0)
    )
).contexts.contexts
print(len(matches), matches[0].distance, matches[-1].distance)
print(matches[0].text)
# set a lower threshold of 0 to prevent any filtering

# directly query the endpoint using Vertex AI Vector Search SDK
query_embedding = (
    genai_client.models.embed_content(
        model = 'text-embedding-005',
        contents = [query]
    )
).embeddings[0].values

matches = vvs_endpoint.find_neighbors(
    deployed_index_id = deployed_index_id,
    num_neighbors = 20,
    #embedding_ids = [''],
    queries = [query_embedding],
    return_full_datapoint = True # chunk text is in the restricts!
)[0]
print(len(matches), matches[0].distance, matches[-1].distance)




# Retrieve all the text chunk with ids from the index:
print(f'The index size is currently: {vvs_index.gca_resource.index_stats}')

# get full index:
index_data = vvs_endpoint.find_neighbors(
    deployed_index_id = deployed_index_id,
    num_neighbors = vvs_index.gca_resource.index_stats.vectors_count,
    queries = [query_embedding],
    return_full_datapoint = True # chunk text is in the restricts!
)[0]
print(f'Retrieved {len(index_data)} chunks from the index.')

# extract chunk data and id to dataframe:
chunk_data = [{
    'id': n.id,
    'chunk_text': next((r.allow_tokens[0] for r in n.restricts if r.name == 'chunk_data'), None)
    } for n in index_data]
print(chunk_data[:5])


###################################################################################################

# create tf-idf vectorizer
vectorizer = TfidfVectorizer(
    ngram_range = (1, 2), # handles all one and two word phrases in the vocabulary
    lowercase = True, # this is a default value
    max_features = 100, # default is 10000 - max vocabulary size
    min_df = 2, # minimum document frequency (int or floast/pct)
    max_df = 0.9, # maximum document frequency (int or float/pct)
    sublinear_tf = True, # replace tf with (1+log(tf)) - reduces outsized impact of keyword density in short chunks
)
vectorizer.fit_transform([d['chunk_text'] for d in chunk_data if d['chunk_text']])
#vectorizer.vocabulary_

###################################################################################################

# create BM25 Model And Embedding

nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('wordnet')
lemmatizer = nltk.stem.WordNetLemmatizer()
stemmer = nltk.stem.PorterStemmer()
stop_words = set(stopwords.words('english'))

def chunk_prep(chunk_text, lemmatize = True, stem = False, ngrams = 2):
    #unigrams = [token for token in re.sub(r'[^\w\s]', '', chunk_text.lower()).split() if len(token) > 1]
    #bigrams = [' '.join(grams) for grams in zip(unigrams, unigrams[1:])]
    #return unigrams + bigrams

    text = chunk_text
    text = re.sub(r'\{[^{}]*\}', '', text) # remove {...}
    text = re.sub(r'\[[^\[\]]*\]', '', text) # remove [...]
    text = re.sub(r'[,:"\']', ' ', text) # remove
    text = ' '.join(text.split()) 

    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    tokens = nltk.tokenize.word_tokenize(text)
    if lemmatize:
        unigrams = [lemmatizer.lemmatize(token) for token in tokens if len(token) > 1 and token not in stop_words]
    elif stem:
        unigrams = [stemmer.stem(token) for token in tokens if len(token) > 1 and token not in stop_words]
    else:
        unigrams = [token for token in tokens if len(token) > 1 and token not in stop_words]

    if ngrams == 2:
        bigrams = [' '.join(grams) for grams in zip(unigrams, unigrams[1:])]
        return unigrams + bigrams
    else:
        return unigrams
       

for chunk in chunk_data:
    chunk['tokenized_text'] = chunk_prep(chunk['chunk_text'])

bm25_model = BM25Okapi(
    [chunk['tokenized_text'] for chunk in chunk_data],
    k1 = 1.2, # term frequency saturation, lower saturates more quickly, higher more slowly, typical 1.2-2
    b = 0.6, # document length normalization, lower (0) means length matters less, higher (1) matters more
    epsilon = 0.25, # smoothing - small constant to be floor to scores and prevent terms not in corpus from having negative idf 
)
print(f'The bm25 vocabulary size is {len(bm25_model.idf.keys())}')

# convert model score to embedding
vocabulary = bm25_model.idf.keys()
vocab_map = {word: i for i, word in enumerate(vocabulary)}
def create_bm25_sparse_embedding(text, bm25_model, vocab_mapping):
    """
    Creates a BM25 sparse embedding for any given tokenized text.
    """
    indices = []
    values = []
    tokenized_text = chunk_prep(text)

    # 1. Calculate term frequencies and doc length for the INPUT text
    term_freqs = Counter(tokenized_text)
    doc_len = len(tokenized_text)
    
    # 2. Get model parameters from the trained bm25_model
    k1 = bm25_model.k1
    b = bm25_model.b
    avgdl = bm25_model.avgdl
    
    # 3. Calculate BM25 score for each term in the input text
    for term, freq in term_freqs.items():
        # Ignore words not in the original vocabulary
        if term not in vocab_mapping:
            continue

        term_index = vocab_mapping[term]
        idf = bm25_model.idf[term]
        
        # Core BM25 formula
        numerator = freq * (k1 + 1)
        denominator = freq + k1 * (1 - b + b * doc_len / avgdl)
        term_score = idf * (numerator / denominator)
        
        indices.append(term_index)
        values.append(term_score)
        
    return {"dimensions": indices, "values": values}

###################################################################################################

# SPLADE - Bert for Sparse - a learned embedding, sparse, interpretabled
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Load the tokenizer and model from Hugging Face
model_id = 'naver/splade-cocondenser-ensembledistil'
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForMaskedLM.from_pretrained(model_id)

# Move the model to the GPU if available
model.to(device)

def compute_splade_vector(text):
    """Computes the SPLADE sparse vector for a given text."""
    # Tokenize the input text
    tokens = tokenizer(text, return_tensors='pt', padding=True, truncation=True)
    # Move tokens to the GPU if available
    tokens = {k: v.to(device) for k, v in tokens.items()}

    # Pass tokens through the model
    with torch.no_grad():
        output = model(**tokens)

    # The model's output is a dense vector of "logits"
    # We apply a ReLU activation to zero out negative values
    relu_output = torch.relu(output.logits)

    # Logarithmically scale the weights and sum across the sequence length
    # This creates a single vector representing the document
    pooled_output = torch.sum(torch.log(1 + relu_output) * tokens['attention_mask'].unsqueeze(-1), dim=1)

    # Find the non-zero dimensions (indices) and their values
    indices = pooled_output.squeeze().nonzero().squeeze().cpu().tolist()
    values = pooled_output.squeeze()[indices].cpu().tolist()
    
    # Handle the case of a single non-zero value
    if not isinstance(indices, list):
        indices = [indices]
        values = [values]

    return {"dimensions": indices, "values": values}


###################################################################################################



# embedder function: sparse and dense
def embedder(query, dense_api = True):
    if dense_api:
        dense = genai_client.models.embed_content(
            model = 'text-embedding-005',
            contents = [query]
        ).embeddings[0].values
    else:
        dense = None

    # tfidf_vector = vectorizer.transform([query])
    # sparse = dict(
    #     values = [float(tfidf_value) for tfidf_value in tfidf_vector.data],
    #     dimensions = [int(tfidf_vector.indices[i]) for i, tfidf_value in enumerate(tfidf_vector.data)]
    # )
    sparse = create_bm25_sparse_embedding(query, bm25_model, vocab_map)
    #sparse = compute_splade_vector(query)
    return dict(dense = dense, sparse = sparse)

# example                
embedder(query)

# Get the ID and text for the first chunk
datapoint_id = chunk_data[0]['id']
chunk_text = chunk_data[0]['chunk_text']

if datapoint_id and chunk_text:
    # 1. Read the full datapoint
    print("Reading datapoint to update...")
    before_upsert = vvs_endpoint.read_index_datapoints(
        deployed_index_id = deployed_index_id,
        ids = [datapoint_id]
    )
    
    if before_upsert:
        mod_upsert = before_upsert[0]
        print("Datapoint before update:", mod_upsert)

        # 2. Modify it by adding the sparse embedding
        embedding = embedder(chunk_text, dense_api = False)
        
        # Convert to dict to safely modify
        mod_upsert_dict = type(mod_upsert).to_dict(mod_upsert)
        mod_upsert_dict['sparse_embedding'] = embedding['sparse']

        # 3. Upsert the modified full datapoint
        print("\nUpserting datapoint with sparse embedding...")
        vvs_index.upsert_datapoints(datapoints = [mod_upsert_dict])#, update_mask = [])
        print("Upsert complete.")


        # 4. Retrieve again to verify the change
        print("\nRetrieving datapoint after upsert to verify...")
        after_upsert = vvs_endpoint.read_index_datapoints(
            deployed_index_id = deployed_index_id,
            ids = [datapoint_id]
        )
        if after_upsert:
            print("Datapoint after update:", after_upsert[0])
        else:
            print("Could not retrieve datapoint after upsert.")
    else:
        print(f"Could not read datapoint with ID: {datapoint_id}")







# now upsert all entries with sparse embeddings
print("Reading all datapoints to add sparse embeddings...")
all_datapoint_ids = [c['id'] for c in chunk_data if c['id']]
existing_datapoints = vvs_endpoint.read_index_datapoints(
    deployed_index_id = deployed_index_id,
    ids = all_datapoint_ids
)
print(f"Read {len(existing_datapoints)} datapoints.")

# Create a map of ID to chunk_text for easier lookup
id_to_text_map = {c['id']: c['chunk_text'] for c in chunk_data if c['id']}

print("Preparing datapoints for upsert with sparse embeddings...")
datapoints_to_upsert = []
for dp in existing_datapoints:
    dp_dict = type(dp).to_dict(dp)
    chunk_text = id_to_text_map.get(dp.datapoint_id)
    if chunk_text:
        embedding = embedder(chunk_text, dense_api = False)
        dp_dict['sparse_embedding'] = embedding['sparse']
    datapoints_to_upsert.append(dp_dict)

# make the upserts
print(f"Upserting {len(datapoints_to_upsert)} datapoints...")
vvs_index.upsert_datapoints(datapoints_to_upsert)
print("Upsert of all datapoints with sparse embeddings is complete.")







# retrieve with rag to show no change
# Context Retrieval - Chunks
matches = rag.retrieval_query(
    rag_resources = [
        rag.RagResource(rag_corpus = corpus.name)
    ],
    text = query,
    rag_retrieval_config = rag.RagRetrievalConfig(
        top_k = 20,  # Optional
        filter = rag.Filter(vector_distance_threshold = 0)
    )
).contexts.contexts
print(len(matches), matches[0].distance, matches[-1].distance)
# set a lower threshold of 0 to prevent any filtering

# retreive dense matches with VVS to show no change
# directly query the endpoint using Vertex AI Vector Search SDK
matches = vvs_endpoint.find_neighbors(
    deployed_index_id = deployed_index_id,
    num_neighbors = 20,
    #embedding_ids = [''],
    queries = [embedder(query)['dense']],
    return_full_datapoint = True # chunk text is in the restricts!
)[0]
print(len(matches), matches[0].distance, matches[-1].distance)






# retreive sparse matches
print("Retrieving matches with a sparse-only hybrid query...")
embedding_dict = embedder(query)
hybrid_query = HybridQuery(
    sparse_embedding_dimensions = embedding_dict['sparse']['dimensions'],
    sparse_embedding_values = embedding_dict['sparse']['values']
)
matches = vvs_endpoint.find_neighbors(
    deployed_index_id = deployed_index_id,
    num_neighbors = 20,
    queries = [hybrid_query],
    return_full_datapoint = True # chunk text is in the restricts!
)[0]
print(f"Found {len(matches)} matches.")
if matches:
    print(f"Sparse Distances: from {matches[0].sparse_distance} to {matches[-1].sparse_distance}")




# retrieve mix of matches with alpha
print("\nRetrieving matches with a hybrid query (alpha=0.5)...")
embedding_dict = embedder(query)

hybrid_query = HybridQuery(
    dense_embedding=embedding_dict['dense'],
    sparse_embedding_dimensions=embedding_dict['sparse']['dimensions'],
    sparse_embedding_values=embedding_dict['sparse']['values'],
    rrf_ranking_alpha = 0.5
)

matches = vvs_endpoint.find_neighbors(
    deployed_index_id = deployed_index_id,
    num_neighbors = 0,
    queries = [hybrid_query],
    return_full_datapoint = True
)[0]

match_data = [{
    'id': n.id,
    'distance': n.distance,
    'sparse_distance': getattr(n, 'sparse_distance', None),
    'chunk_text': next((r.allow_tokens[0] for r in n.restricts if r.name == 'chunk_data'), None)
    } for n in matches]

print(f"Found {len(match_data)} matches:")
if match_data:
    print("Distance | Sparse Distance | ID")
    print("-------------------------")
    for item in match_data:
        dist_str = f"{item['distance']:.4f}"
        
        sparse_dist = item['sparse_distance']
        
        if sparse_dist is not None:
            sparse_dist_str = f"{sparse_dist:.4f}"
        else:
            sparse_dist_str = "N/A"
            
        print(f"{dist_str:<9} | {sparse_dist_str} | {item['id']}")













# 5536094114968600211_5536094115973747828
query_indices = embedder(query, dense_api = False)['sparse']['dimensions']
trythis = """# Rule 2.02 to 2.05\n\nhome base shall be beveled and the base shall be fixed in the ground level with the ground surface. (See drawing D in Appendix 2.)\n\n## 2.03 The Bases\n\nFirst, second and third bases shall be marked by white canvas or rubber-covered bags, securely attached to the ground as indicated in Diagram 2. The first and third base bags shall be entirely within the infield. The second base bag shall be centered on second base. The bags shall be 18 inches square, not less than three nor more than five inches thick, and filled with soft material.\n\n## 2.04 The Pitcher's Plate\n\nThe pitcher's plate shall be a rectangular slab of whitened rubber, 24 inches by 6 inches. It shall be set in the ground as shown in Diagrams 1 and 2, so that the distance between the pitcher's plate and home base (the rear point of home plate) shall be 60 feet, 6 inches.\n\n## 2.05 Benches\n\nThe home Club shall furnish players' benches, one each for the home and visiting teams."""
chunk_indices = embedder(trythis, dense_api = False)['sparse']['dimensions']


idf_scores = dict(zip(range(len(vectorizer.idf_)), vectorizer.idf_))
index_to_word = {i: word for word, i in vectorizer.vocabulary_.items()}
query_indices = [3470, 9895, 10941, 17581, 17584]
for index in query_indices:
    word = index_to_word[index]
    idf = idf_scores[index]
    print(f"Word: '{word}' (Index: {index}) -> IDF Score: {idf:.2f}")





# show how to manually supply context to ranking and|or gemini for answer



