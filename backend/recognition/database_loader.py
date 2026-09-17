import numpy as np

from database import supabase


def load_embeddings():

    response = (
        supabase
        .table("embeddings")
        .select("student_id, embedding")
        .execute()
    )

    database = {}

    for row in response.data:

        student_id = row["student_id"]
        embedding = np.array(row["embedding"], dtype=np.float32)

        if student_id not in database:
            database[student_id] = []

        database[student_id].append(embedding)

    for student_id in database:
        database[student_id] = np.array(
            database[student_id]
        )

    return database