
import os
import openai
import pickle
import faiss
import numpy as np
from typing import List, Tuple

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# FAISS index and metadata paths
dim = 1536
INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_index.bin")
META_PATH = os.getenv("FAISS_METADATA_PATH", "./faiss_metadata.pkl")

# Load or initialize FAISS index and metadata
if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "rb") as f:
        id_to_text = pickle.load(f)
else:
    index = faiss.IndexFlatL2(dim)
    id_to_text = []

# Embed text via OpenAI embeddings
def embed_text(text: str) -> List[float]:
    resp = openai.Embeddings.create(
        model="text-embedding-ada-002",
        input=[text]
    )
    return resp['data'][0]['embedding']

# Upsert documents into FAISS index
def upsert_documents(docs: List[Tuple[str, str]]):
    texts = [t for _, t in docs]
    resp = openai.Embeddings.create(
        model="text-embedding-ada-002",
        input=texts
    )
    vectors = np.array([d['embedding'] for d in resp['data']], dtype='float32')

    index.add(vectors)
    id_to_text.extend(texts)

    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(id_to_text, f)

# Retrieve top-k similar docs
def get_top_k_docs(user_emb: List[float], k: int = 3) -> List[str]:
    query_vec = np.array(user_emb, dtype='float32').reshape(1, -1)
    _, indices = index.search(query_vec, k)
    results = []
    for idx in indices[0]:
        if idx < len(id_to_text):
            results.append(id_to_text[idx])
    return results