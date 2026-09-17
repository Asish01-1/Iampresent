import numpy as np


class StudentMatcher:
    def __init__(self, database):
        self.database = database

    def match(self, query_embedding):
        # Convert query to a 1D vector
        query_embedding = np.asarray(query_embedding).reshape(-1)

        # Normalize query
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        best_student = None
        best_score = -1.0

        for student_id, student_embeddings in self.database.items():

            # Make sure stored embeddings are 2D: (number_of_images, 384)
            student_embeddings = np.asarray(student_embeddings)

            if student_embeddings.ndim == 1:
                student_embeddings = student_embeddings.reshape(1, -1)

            # Compare query with all enrollment embeddings
            scores = np.dot(student_embeddings, query_embedding)

            # Take the closest enrollment image
            score = float(np.max(scores))

            if score > best_score:
                best_score = score
                best_student = student_id

        return best_student, best_score