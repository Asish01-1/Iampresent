import os
import numpy as np

from database import supabase

STUDENT_ID = "001"

embedding_path = os.path.join(
    "data",
    "embeddings",
    "Asish.npy"
)

if not os.path.exists(embedding_path):
    print("Embedding file not found:")
    print(embedding_path)
    exit()

embeddings = np.load(embedding_path)

if embeddings.ndim == 1:
    embeddings = embeddings.reshape(1, -1)

print("Loaded embeddings:", embeddings.shape)

for i, embedding in enumerate(embeddings):

    supabase.table("embeddings").insert({
        "student_id": STUDENT_ID,
        "embedding": embedding.tolist()
    }).execute()

    print(f"Uploaded embedding {i + 1}/{len(embeddings)}")

print()
print("================================")
print("MIGRATION COMPLETE")
print("================================")
print("Student ID:", STUDENT_ID)
print("Embeddings:", len(embeddings))
print("================================")