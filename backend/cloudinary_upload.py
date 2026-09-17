import cloudinary.uploader
from cloudinary_config import cloudinary


def upload_student_image(image_data, student_id, image_number, prefix="face"):
    folder = f"student_attendance/{student_id}"

    result = cloudinary.uploader.upload(
        image_data,
        folder=folder,
        public_id=f"{prefix}_{image_number}"
    )

    return {
        "public_id": result["public_id"],
        "url": result["secure_url"]
    }