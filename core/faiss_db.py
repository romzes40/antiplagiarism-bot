# core/faiss_db.py
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os

MODEL = SentenceTransformer('all-MiniLM-L6-v2')
DIM = 384
INDEX_PATH = "database/faiss_index/index.faiss"
METADATA_PATH = "database/faiss_index/metadata.pkl"

os.makedirs("database/faiss_index", exist_ok=True)

class FAISSDatabase:
    def __init__(self):
        if os.path.exists(INDEX_PATH):
            self.index = faiss.read_index(INDEX_PATH)
            with open(METADATA_PATH, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(DIM)
            self.metadata = []

    def add_text(self, text, title="Unknown"):
        sentences = [s.strip() for s in text.split('. ') if len(s.strip()) > 10]
        for sent in sentences:
            emb = MODEL.encode([sent])
            emb = np.array(emb).astype('float32')
            self.index.add(emb)
            self.metadata.append({"text": sent, "title": title})
        self.save()

    def search(self, query, k=5):
        if self.index.ntotal == 0:
            return []
        query_emb = MODEL.encode([query])
        query_emb = np.array(query_emb).astype('float32')
        distances, indices = self.index.search(query_emb, k)
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                similarity = 1 - (distances[0][i] / 2)
                if similarity > 0.3:  # только значимые совпадения
                    results.append({
                        "text": self.metadata[idx]["text"],
                        "title": self.metadata[idx]["title"],
                        "similarity": similarity
                    })
        return results

    def save(self):
        faiss.write_index(self.index, INDEX_PATH)
        with open(METADATA_PATH, 'wb') as f:
            pickle.dump(self.metadata, f)