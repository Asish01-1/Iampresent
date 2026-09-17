import os
import sys
import numpy as np
from PIL import Image

from recognition.dinov2_model import DinoV2


# ==========================================
# GET STUDENT ID
# ==========================================

if len(sys.argv) < 2:
    print("Usage:")
    print("python -m enrollment.enroll STUDENT_ID")
    print()
    print("Example:")
    print("python -m enrollment.enroll ASHISH")
    exit()

STUDENT_ID = sys.argv[1].upper()


# ==========================================
# PATHS
# ==========================================

IMAGE_FOLDER = os.path.join(
    "data",
    "students",
    STUDENT_ID
)

OUTPUT_FOLDER = os.path.join(
    "data",
    "embeddings"
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ==========================================
# CHECK STUDENT IMAGES
# ==========================================

if not os.path.exists(IMAGE_FOLDER):

    print("Student image folder not found:")
    print(IMAGE_FOLDER)

    print()
    print("Create the folder and put the captured")
    print("face images inside it.")

    exit()


# ==========================================
# LOAD DINOv2
# ==========================================

print("Loading DINOv2...")

dino = DinoV2()


# ==========================================
# PROCESS IMAGES
# ==========================================

embeddings = []

files = sorted(
    os.listdir(IMAGE_FOLDER)
)


for filename in files:

    if not filename.lower().endswith(
        (".jpg", ".jpeg", ".png")
    ):
        continue


    image_path = os.path.join(
        IMAGE_FOLDER,
        filename
    )


    print(
        "Processing:",
        filename
    )


    image = (
        Image
        .open(image_path)
        .convert("RGB")
    )


    embedding = dino.extract(
        image
    )


    embeddings.append(
        embedding
    )


# ==========================================
# CHECK RESULT
# ==========================================

if len(embeddings) == 0:

    print("No images found.")

    exit()


embeddings = np.array(
    embeddings
)


# ==========================================
# NORMALIZE
# ==========================================

norms = np.linalg.norm(
    embeddings,
    axis=1,
    keepdims=True
)

embeddings = (
    embeddings / norms
)


# ==========================================
# SAVE
# ==========================================

output_path = os.path.join(
    OUTPUT_FOLDER,
    f"{STUDENT_ID}.npy"
)


np.save(
    output_path,
    embeddings
)


# ==========================================
# RESULT
# ==========================================

print()
print("================================")
print("ENROLLMENT COMPLETE")
print("================================")

print(
    "Student:",
    STUDENT_ID
)

print(
    "Images:",
    len(embeddings)
)

print(
    "Embedding shape:",
    embeddings.shape
)

print(
    "Saved:",
    output_path
)

print("================================")