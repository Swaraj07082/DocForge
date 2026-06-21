from sentence_transformers import SentenceTransformer
import faiss
import pickle

index = faiss.read_index("vector_store/index.faiss")

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

query = "what is lemmatization?"

query_embedding = model.encode([query], convert_to_numpy=True).astype("float32")
faiss.normalize_L2(query_embedding)


D , I = index.search(query_embedding, k=5)  # k is the number of nearest neighbors to retrieve


# D = Distances (or similarity scores) of the nearest neighbors
# I = Indices (IDs) of the nearest neighbors in the index

# Example:

# D, I = index.search(query_embedding, k=3)

# print(D)
# # [[0.12, 0.25, 0.31]]

# print(I)
# # [[42, 17, 89]]

# This means:

# Rank	Index (I)	Distance (D)
# 1st nearest	42	0.12
# 2nd nearest	17	0.25
# 3rd nearest	89	0.31

with open("vector_store/documents.pkl", "rb") as f:
    documents = pickle.load(f)


for idx in I[0]:
    print("Document:", documents[idx])
    print("--------------------------------")


