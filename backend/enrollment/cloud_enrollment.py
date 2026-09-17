import os
import numpy as np
from PIL import Image

from cloudinary_upload import upload_student_image
from recognition.dinov2_model import DinoV2
from database import supabase


def enroll_student(student_id):

    student_id = student_id.upper()

    image_folder = os.path.join(
        "data",
        "students",
        student_id
    )

    if not os.path.exists(image_folder):
        raise FileNotFoundError(
            f"No captured images found for {student_id}"
        )

    image_files = [
        f for f in os.listdir(image_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if not image_files:
        raise ValueError(
            f"No face images found for {student_id}"
        )

        existing = (
        supabase
        .table("embeddings")
        .select("id")
        .eq("student_id", student_id)
        .limit(1)
        .execute()
    )

    if existing.data:
        raise ValueError(
            f"{student_id} is already enrolled."
        )

    print(f"Found {len(image_files)} images")

    dino = DinoV2()

    embeddings = []

    for filename in image_files:

        image_path = os.path.join(
            image_folder,
            filename
        )

        print("Processing:", filename)

        # 1. Upload image to Cloudinary
        upload_result = upload_student_image(
            image_path,
            student_id
        )

        print("Uploaded:", upload_result["public_id"])

        # 2. Read image as RGB
        image = Image.open(image_path).convert("RGB")

        # 3. Generate DINOv2 embedding
        embedding = dino.extract(image)

        embeddings.append(embedding)

    # Convert to NumPy array
    embeddings = np.array(embeddings)

    # Normalize embeddings
    norms = np.linalg.norm(
        embeddings,
        axis=1,
        keepdims=True
    )

    embeddings = embeddings / norms

    # 4. Store embeddings in Supabase
    for embedding in embeddings:

        supabase.table("embeddings").insert({
            "student_id": student_id,
            "embedding": embedding.tolist()
        }).execute()

    print()
    print("================================")
    print("ENROLLMENT COMPLETE")
    print("================================")
    print("Student:", student_id)
    print("Images:", len(image_files))
    print("Embeddings:", len(embeddings))
    print("================================")