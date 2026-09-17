# from fastapi import FastAPI
# from database import supabase
# from pydantic import BaseModel
# from datetime import date

# app = FastAPI(
#     title="AI Student Attendance System"
# )

# class Student(BaseModel):
#     student_id: str
#     name: str
#     class_name: str | None = None

# class AttendanceRequest(BaseModel):
#     student_ids: list[str]

# class RecognitionRequest(BaseModel):
#     student_ids: list[str]

# @app.get("/")
# def home():
#     return {
#         "message": "AI Attendance Backend Running"
#     }


# @app.get("/health")
# def health():
#     return {
#         "status": "ok"
#     }

# @app.get("/students")
# def get_students():
#     response = (
#         supabase
#         .table("students")
#         .select("*")
#         .execute()
#     )

#     return response.data


# @app.post("/students")
# def create_student(student: Student):

#     image_folder = f"student_attendance/{student.student_id}"

#     response = (
#         supabase
#         .table("students")
#         .insert({
#             "student_id": student.student_id,
#             "name": student.name,
#             "class_name": student.class_name,
#             "image_folder": image_folder
#         })
#         .execute()
#     )

#     return response.data

# # Stores the latest recognition session
# latest_recognition = []

# @app.post("/recognition/results")
# def save_recognition_results(request: RecognitionRequest):

#     global latest_recognition

#     if not request.student_ids:

#         latest_recognition = []

#         return {
#             "students": []
#         }

#     response = (
#         supabase
#         .table("students")
#         .select("student_id, name, class_name")
#         .in_("student_id", request.student_ids)
#         .execute()
#     )

#     latest_recognition = response.data

#     return {
#         "message": "Recognition results saved.",
#         "students": latest_recognition
#     }


# @app.get("/recognition/results")
# def get_recognition_results():

#     return {
#         "students": latest_recognition
#     }

# @app.post("/attendance/proceed")
# def record_attendance(request: AttendanceRequest):

#     today = date.today().isoformat()

#     records = []

#     for student_id in request.student_ids:

#         records.append({
#             "student_id": student_id,
#             "attendance_date": today,
#             "present": True
#         })

#     if not records:
#         return {
#             "message": "No students provided.",
#             "attendance": []
#         }

#     response = (
#         supabase
#         .table("attendance")
#         .upsert(
#             records,
#             on_conflict="student_id,attendance_date"
#         )
#         .execute()
#     )

#     return {
#         "message": "Attendance recorded successfully.",
#         "date": today,
#         "attendance": response.data
#     }

# @app.get("/attendance/today")
# def get_today_attendance():

#     today = date.today().isoformat()

#     response = (
#         supabase
#         .table("attendance")
#         .select("*")
#         .eq("attendance_date", today)
#         .execute()
#     )

#     return {
#         "date": today,
#         "attendance": response.data
#     }

# @app.get("/students/{student_id}")
# def get_student(student_id: str):
#     response = (
#         supabase
#         .table("students")
#         .select("student_id, name, class_name")
#         .eq("student_id", student_id)
#         .single()
#         .execute()
#     )

#     return response.data

import os
from fastapi.responses import FileResponse
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, datetime, timezone
from typing import List
import io
import csv
from fastapi.responses import StreamingResponse

import numpy as np
from PIL import Image

import mediapipe as mp

from cloudinary_upload import upload_student_image
from database import supabase
from recognition.dinov2_model import DinoV2
from recognition.matcher import StudentMatcher


# ==========================================
# MEDIAPIPE FACE DETECTOR
# ==========================================

BaseOptions = mp.tasks.BaseOptions
FaceDetector = mp.tasks.vision.FaceDetector
FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

face_detector_options = FaceDetectorOptions(
    base_options=BaseOptions(
        model_asset_path="face_detector.task"
    ),
    running_mode=VisionRunningMode.IMAGE,
    min_detection_confidence=0.2
)

face_detector = FaceDetector.create_from_options(
    face_detector_options
)


# ==========================================
# FASTAPI
# ==========================================

app = FastAPI(
    title="AI Student Attendance System"
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# MODELS
# ==========================================

class Student(BaseModel):
    student_id: str
    name: str
    class_name: str | None = None


class AttendanceRequest(BaseModel):
    student_ids: list[str]


class RecognitionLogRequest(BaseModel):
    student_id: str
    session_start: str


# ==========================================
# GLOBAL AI MODEL
# ==========================================

dino = None
matcher = None


def get_dino():

    global dino

    if dino is None:

        print("Loading DINOv2...")

        dino = DinoV2()

        print("DINOv2 ready.")

    return dino


# ==========================================
# BASIC ROUTES
# ==========================================

@app.get("/")
def home():

    return {
        "message":
            "AI Attendance Backend Running"
    }


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


# ==========================================
# STUDENTS
# ==========================================

@app.get("/students")
def get_students():

    response = (
        supabase
        .table("students")
        .select(
            "student_id, name, class_name"
        )
        .order(
            "student_id"
        )
        .execute()
    )

    return response.data


@app.get("/students/{student_id}")
def get_student(student_id: str):

    response = (
        supabase
        .table("students")
        .select(
            "student_id, name, class_name"
        )
        .eq(
            "student_id",
            student_id
        )
        .single()
        .execute()
    )

    return response.data


@app.post("/students")
def create_student(student: Student):

    student_id = (
        student.student_id
        .strip()
        .upper()
    )

    response = (
        supabase
        .table("students")
        .insert({
            "student_id":
                student_id,

            "name":
                student.name.strip(),

            "class_name":
                student.class_name,

            "image_folder":
                f"student_attendance/{student_id}"
        })
        .execute()
    )

    return {
        "message":
            "Student created successfully.",

        "student":
            response.data
    }


# ==========================================
# ENROLLMENT
# ==========================================

@app.post("/enrollment")
async def enrollment(
    student_id: str = Form(...),
    images: list[UploadFile] = File(...)
):

    student_id = (
        student_id
        .upper()
        .strip()
    )

    # --------------------------------------
    # CHECK IMAGES
    # --------------------------------------

    if not images:

        return {
            "success": False,
            "message":
                "No images received."
        }

    if len(images) != 30:

        return {
            "success": False,
            "message":
                f"Expected 30 images, received {len(images)}."
        }

    # --------------------------------------
    # CHECK STUDENT
    # --------------------------------------

    student_response = (
        supabase
        .table("students")
        .select(
            "student_id, name, class_name"
        )
        .eq(
            "student_id",
            student_id
        )
        .execute()
    )

    if not student_response.data:

        return {
            "success": False,
            "message":
                f"Student {student_id} does not exist."
        }

    # --------------------------------------
    # CHECK EXISTING EMBEDDINGS
    # --------------------------------------

    existing = (
        supabase
        .table("embeddings")
        .select("id")
        .eq(
            "student_id",
            student_id
        )
        .limit(1)
        .execute()
    )

    if existing.data:

        return {
            "success": False,
            "message":
                f"{student_id} is already enrolled."
        }

    # --------------------------------------
    # LOAD DINOv2
    # --------------------------------------

    model = get_dino()

    embeddings = []
    image_data_list = []

    # --------------------------------------
    # PROCESS 30 IMAGES
    # --------------------------------------

    for index, image_file in enumerate(images):

        print(
            f"Processing image "
            f"{index + 1}/{len(images)}"
        )

        contents = await image_file.read()

        image_data_list.append(contents)

        image = Image.open(
            io.BytesIO(contents)
        ).convert("RGB")

        embedding = model.extract(image)

        embedding = (
            embedding /
            np.linalg.norm(embedding)
        )

        embeddings.append(
            embedding.tolist()
        )

    # --------------------------------------
    # CLOUDINARY
    # --------------------------------------

    print(
        f"Uploading {len(image_data_list)} "
        f"images to Cloudinary..."
    )

    uploaded_images = []

    for index, image_data in enumerate(
        image_data_list
    ):

        print(
            f"Uploading image "
            f"{index + 1}/{len(image_data_list)}"
        )

        upload_result = (
            upload_student_image(
                image_data,
                student_id,
                index + 1
            )
        )

        uploaded_images.append(
            upload_result
        )

    # --------------------------------------
    # SAVE EMBEDDINGS
    # --------------------------------------

    print(
        "Saving embeddings to Supabase..."
    )

    for embedding in embeddings:

        supabase.table(
            "embeddings"
        ).insert({
            "student_id":
                student_id,

            "embedding":
                embedding
        }).execute()

    print(
        f"Enrollment completed "
        f"for {student_id}"
    )

    return {

        "success": True,

        "student_id":
            student_id,

        "images_processed":
            len(images),

        "images_uploaded":
            len(uploaded_images),

        "embeddings_created":
            len(embeddings),

        "Cloudinary_folder":
            f"student_attendance/{student_id}",

        "message":
            "Student enrolled successfully."
    }



# ==========================================
# GALLERY ENROLLMENT
# ==========================================

@app.post("/enrollment/gallery")
async def gallery_enrollment(
    student_id: str = Form(...),
    images: list[UploadFile] = File(...)
):

    student_id = (
        student_id
        .upper()
        .strip()
    )

    # --------------------------------------
    # CHECK IMAGE COUNT
    # --------------------------------------

    if len(images) < 10 or len(images) > 30:

        return {
            "success": False,
            "message":
                f"Please upload between 10 and 30 images. Received {len(images)}."
        }


    # --------------------------------------
    # CHECK STUDENT
    # --------------------------------------

    student_response = (
        supabase
        .table("students")
        .select(
            "student_id, name, class_name"
        )
        .eq(
            "student_id",
            student_id
        )
        .execute()
    )

    if not student_response.data:

        return {
            "success": False,
            "message":
                f"Student {student_id} does not exist."
        }



    # --------------------------------------
    # LOAD DINOv2
    # --------------------------------------

    model = get_dino()

    embeddings = []
    image_data_list = []


    # --------------------------------------
    # PROCESS IMAGES
    # --------------------------------------

    for index, image_file in enumerate(images):

        print(
            f"Processing gallery image "
            f"{index + 1}/{len(images)}"
        )

        contents = await image_file.read()

        if not contents:

            return {
                "success": False,
                "message":
                    f"Image {index + 1} is empty."
            }

        image_data_list.append(contents)


        # ----------------------------------
        # OPEN IMAGE
        # ----------------------------------

        try:

            image = Image.open(
                io.BytesIO(contents)
            ).convert("RGB")

        except Exception:

            return {
                "success": False,
                "message":
                    f"Image {index + 1} is invalid."
            }


        # ----------------------------------
        # FACE DETECTION
        # ----------------------------------

        frame_array = np.array(image)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_array
        )

        detection_result = (
            face_detector.detect(
                mp_image
            )
        )

        face_count = len(
            detection_result.detections
        )


        # ----------------------------------
        # REQUIRE EXACTLY ONE FACE
        # ----------------------------------

        if face_count == 0:

            return {
                "success": False,
                "message":
                    f"Image {index + 1} does not contain a face."
            }


        if face_count > 1:

            return {
                "success": False,
                "message":
                    f"Image {index + 1} contains multiple faces. Please use one face per image."
            }


        # ----------------------------------
        # CREATE DINOv2 EMBEDDING
        # ----------------------------------

        embedding = model.extract(
            image
        )

        embedding = (
            embedding /
            np.linalg.norm(embedding)
        )

        embeddings.append(
            embedding.tolist()
        )


    # --------------------------------------
    # UPLOAD IMAGES TO CLOUDINARY
    # --------------------------------------

    print(
        f"Uploading {len(image_data_list)} "
        f"gallery images to Cloudinary..."
    )
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    uploaded_images = []

    for index, image_data in enumerate(
        image_data_list
    ):

        print(
            f"Uploading gallery image "
            f"{index + 1}/{len(image_data_list)}"
        )

        upload_result = upload_student_image(
        image_data,
        student_id,
        index + 1,
        prefix=f"gallery_{batch_id}"
        )

        uploaded_images.append(
            upload_result
        )


    # --------------------------------------
    # SAVE EMBEDDINGS TO SUPABASE
    # --------------------------------------

    print(
        "Saving gallery embeddings to Supabase..."
    )

    for embedding in embeddings:

        supabase.table(
            "embeddings"
        ).insert({

            "student_id":
                student_id,

            "embedding":
                embedding

        }).execute()


    # --------------------------------------
    # COMPLETED
    # --------------------------------------

    print(
        f"Gallery enrollment completed "
        f"for {student_id}"
    )

    return {

        "success": True,

        "student_id":
            student_id,

        "images_processed":
            len(images),

        "images_uploaded":
            len(uploaded_images),

        "embeddings_created":
            len(embeddings),

        "Cloudinary_folder":
            f"student_attendance/{student_id}",

        "message":
            "Gallery enrollment completed successfully."
    }


# ==========================================
# LOAD DATABASE FOR RECOGNITION
# ==========================================

def load_embeddings():

    response = (
        supabase
        .table("embeddings")
        .select(
            "student_id, embedding"
        )
        .execute()
    )

    database = {}

    for row in response.data:

        student_id = row["student_id"]

        embedding = np.array(
            row["embedding"],
            dtype=np.float32
        )

        if student_id not in database:

            database[student_id] = []

        database[student_id].append(
            embedding
        )

    for student_id in database:

        database[student_id] = np.array(
            database[student_id]
        )

    return database


# ==========================================
# RECOGNITION
# ==========================================

@app.post("/recognition")
async def recognition(
    image: UploadFile = File(...)
):

    global matcher

    contents = await image.read()

    try:

        frame = Image.open(
            io.BytesIO(contents)
        ).convert("RGB")

    except Exception:

        return {
            "success": False,
            "message":
                "Invalid image received."
        }

    # --------------------------------------
    # FACE DETECTION
    # --------------------------------------

    frame_array = np.array(frame)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=frame_array
    )

    detection_result = (
        face_detector.detect(mp_image)
    )

    if not detection_result.detections:

        return {
            "success": True,
            "face_count": 0,
            "faces": []
        }

    # --------------------------------------
    # LOAD EMBEDDINGS
    # --------------------------------------

    database = load_embeddings()

    if not database:

        return {
            "success": False,
            "message":
                "No enrolled students."
        }

    matcher = StudentMatcher(
        database
    )

    model = get_dino()

    # --------------------------------------
    # PROCESS FACES
    # --------------------------------------

    faces = []

    THRESHOLD = 0.65
    PADDING = 20

    for index, detection in enumerate(
        detection_result.detections
    ):

        bbox = detection.bounding_box

        x = bbox.origin_x
        y = bbox.origin_y

        width = bbox.width
        height = bbox.height

        x1 = max(
            0,
            x - PADDING
        )

        y1 = max(
            0,
            y - PADDING
        )

        x2 = min(
            frame.width,
            x + width + PADDING
        )

        y2 = min(
            frame.height,
            y + height + PADDING
        )

        face = frame.crop(
            (x1, y1, x2, y2)
        )

        embedding = model.extract(
            face
        )

        student_id, score = (
            matcher.match(
                embedding
            )
        )

        score = float(score)

        face_result = {

            "face_index":
                index + 1,

            "recognized":
                False,

            "student":
                None,

            "score":
                round(score, 3)
        }

        if (
            student_id is not None
            and score >= THRESHOLD
        ):

            response = (
                supabase
                .table("students")
                .select(
                    "student_id, name, class_name"
                )
                .eq(
                    "student_id",
                    student_id
                )
                .execute()
            )

            if response.data:

                face_result[
                    "recognized"
                ] = True

                face_result[
                    "student"
                ] = response.data[0]

        faces.append(
            face_result
        )

    return {

        "success": True,

        "face_count":
            len(faces),

        "faces":
            faces
    }


# ==========================================
# RECOGNITION VERIFICATION LOG
# ==========================================

@app.post("/recognition/log")
def create_recognition_log(
    request: RecognitionLogRequest
):

    try:

        session_start = (
            datetime.fromisoformat(
                request.session_start
            )
        )

    except ValueError:

        return {
            "success": False,
            "message":
                "Invalid session start time."
        }

    response = (
        supabase
        .table("recognition_logs")
        .insert({

            "student_id":
                request.student_id,

            "recognized_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "session_start":
                session_start.isoformat()
        })
        .execute()
    )

    return {

        "success": True,

        "log":
            response.data
    }


# ==========================================
# RECOGNITION RESULTS
# ==========================================

latest_recognition = []


@app.post("/recognition/results")
def save_recognition_results(
    request: AttendanceRequest
):

    global latest_recognition

    if not request.student_ids:

        latest_recognition = []

        return {
            "students": []
        }

    response = (
        supabase
        .table("students")
        .select(
            "student_id, name, class_name"
        )
        .in_(
            "student_id",
            request.student_ids
        )
        .execute()
    )

    latest_recognition = (
        response.data
    )

    return {

        "message":
            "Recognition results saved.",

        "students":
            latest_recognition
    }


@app.get("/recognition/results")
def get_recognition_results():

    return {
        "students":
            latest_recognition
    }


# ==========================================
# ATTENDANCE
# ==========================================

@app.post("/attendance/proceed")
def record_attendance(
    request: AttendanceRequest
):

    today = date.today().isoformat()

    records = []

    for student_id in request.student_ids:

        records.append({

            "student_id":
                student_id,

            "attendance_date":
                today,

            "present":
                True
        })

    if not records:

        return {

            "message":
                "No students provided.",

            "attendance":
                []
        }

    response = (
        supabase
        .table("attendance")
        .upsert(
            records,
            on_conflict=
                "student_id,attendance_date"
        )
        .execute()
    )

    return {

        "message":
            "Attendance recorded successfully.",

        "date":
            today,

        "attendance":
            response.data
    }


# ==========================================
# TODAY ATTENDANCE
# ==========================================

@app.get("/attendance/today")
def get_today_attendance():

    today = date.today().isoformat()

    response = (
        supabase
        .table("attendance")
        .select(
            "student_id, attendance_date, present, created_at"
        )
        .eq(
            "attendance_date",
            today
        )
        .order(
            "student_id"
        )
        .execute()
    )

    student_ids = [
        row["student_id"]
        for row in response.data
    ]

    students = {}

    if student_ids:

        student_response = (
            supabase
            .table("students")
            .select(
                "student_id, name, class_name"
            )
            .in_(
                "student_id",
                student_ids
            )
            .execute()
        )

        students = {
            row["student_id"]:
                row
            for row in
            student_response.data
        }

    result = []

    for row in response.data:

        student = students.get(
            row["student_id"],
            {}
        )

        result.append({

            "student_id":
                row["student_id"],

            "name":
                student.get(
                    "name",
                    ""
                ),

            "class_name":
                student.get(
                    "class_name",
                    ""
                ),

            "attendance_date":
                row["attendance_date"],

            "present":
                row["present"],

            "created_at":
                row["created_at"]
        })

    return {

        "date":
            today,

        "attendance":
            result
    }


# ==========================================
# DAILY ATTENDANCE DOWNLOAD
# ==========================================

@app.get("/attendance/today/download")
def download_today_attendance():

    data = get_today_attendance()

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow([
        "Student ID",
        "Name",
        "Class",
        "Date",
        "Present"
    ])

    for row in data["attendance"]:

        writer.writerow([

            row["student_id"],
            row["name"],
            row["class_name"],
            row["attendance_date"],
            "Present"
            if row["present"]
            else "Absent"
        ])

    output.seek(0)

    return StreamingResponse(

        iter([
            output.getvalue()
        ]),

        media_type=
            "text/csv",

        headers={
            "Content-Disposition":
                "attachment; filename=today_attendance.csv"
        }
    )


# ==========================================
# RECOGNITION VERIFICATION
# ==========================================

@app.get("/recognition/logs")
def get_recognition_logs(
    log_date: str
):

    try:

        start_date = datetime.strptime(
            log_date,
            "%Y-%m-%d"
        )

    except ValueError:

        return {
            "success": False,
            "message":
                "Invalid date. Use YYYY-MM-DD."
        }

    next_date = (
        start_date
        .replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
    )

    next_day = (
        next_date
        .timestamp()
        + 86400
    )

    end_datetime = datetime.fromtimestamp(
        next_day
    )

    response = (
        supabase
        .table("recognition_logs")
        .select(
            "id, student_id, recognized_at, session_start"
        )
        .gte(
            "recognized_at",
            next_date.isoformat()
        )
        .lt(
            "recognized_at",
            end_datetime.isoformat()
        )
        .order(
            "recognized_at"
        )
        .execute()
    )

    student_ids = list({
        row["student_id"]
        for row in response.data
    })

    students = {}

    if student_ids:

        student_response = (
            supabase
            .table("students")
            .select(
                "student_id, name, class_name"
            )
            .in_(
                "student_id",
                student_ids
            )
            .execute()
        )

        students = {
            row["student_id"]:
                row
            for row in
            student_response.data
        }

    result = []

    for row in response.data:

        student = students.get(
            row["student_id"],
            {}
        )

        result.append({

            "id":
                row["id"],

            "student_id":
                row["student_id"],

            "name":
                student.get(
                    "name",
                    ""
                ),

            "class_name":
                student.get(
                    "class_name",
                    ""
                ),

            "recognized_at":
                row["recognized_at"],

            "session_start":
                row["session_start"]
        })

    return {

        "date":
            log_date,

        "logs":
            result
    }


# ==========================================
# RECOGNITION LOG DOWNLOAD
# ==========================================

@app.get("/recognition/logs/download")
def download_recognition_logs(
    log_date: str
):

    data = get_recognition_logs(
        log_date
    )

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow([

        "Recognition Time",
        "Student ID",
        "Name",
        "Class",
        "Session Start"
    ])

    for row in data["logs"]:

        writer.writerow([

            row["recognized_at"],
            row["student_id"],
            row["name"],
            row["class_name"],
            row["session_start"]
        ])

    output.seek(0)

    return StreamingResponse(

        iter([
            output.getvalue()
        ]),

        media_type=
            "text/csv",

        headers={
            "Content-Disposition":
                f"attachment; filename=recognition_{log_date}.csv"
        }
    )


# ==========================================
# MONTHLY REPORT
# ==========================================

@app.get("/reports/monthly")
def monthly_report(
    year: int,
    month: int
):

    if month < 1 or month > 12:

        return {
            "success": False,
            "message":
                "Month must be between 1 and 12."
        }

    start_date = date(
        year,
        month,
        1
    )

    if month == 12:

        end_date = date(
            year + 1,
            1,
            1
        )

    else:

        end_date = date(
            year,
            month + 1,
            1
        )

    attendance_response = (
        supabase
        .table("attendance")
        .select(
            "student_id, attendance_date, present"
        )
        .gte(
            "attendance_date",
            start_date.isoformat()
        )
        .lt(
            "attendance_date",
            end_date.isoformat()
        )
        .eq(
            "present",
            True
        )
        .execute()
    )

    students_response = (
        supabase
        .table("students")
        .select(
            "student_id, name, class_name"
        )
        .order(
            "student_id"
        )
        .execute()
    )

    present_counts = {}

    for row in attendance_response.data:

        student_id = row["student_id"]

        present_counts[
            student_id
        ] = (
            present_counts.get(
                student_id,
                0
            ) + 1
        )

    result = []

    for student in students_response.data:

        student_id = (
            student["student_id"]
        )

        result.append({

            "student_id":
                student_id,

            "name":
                student["name"],

            "class_name":
                student.get(
                    "class_name",
                    ""
                ),

            "present":
                present_counts.get(
                    student_id,
                    0
                )
        })

    return {

        "year":
            year,

        "month":
            month,

        "report":
            result
    }


# ==========================================
# MONTHLY REPORT DOWNLOAD
# ==========================================

@app.get("/reports/monthly/download")
def download_monthly_report(
    year: int,
    month: int
):

    data = monthly_report(
        year,
        month
    )

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow([

        "Student ID",
        "Name",
        "Class",
        "Present"
    ])

    for row in data["report"]:

        writer.writerow([

            row["student_id"],
            row["name"],
            row["class_name"],
            row["present"]
        ])

    output.seek(0)

    return StreamingResponse(

        iter([
            output.getvalue()
        ]),

        media_type=
            "text/csv",

        headers={
            "Content-Disposition":
                f"attachment; filename=monthly_report_{year}_{month:02d}.csv"
        }
    )


# ==========================================
# INDIVIDUAL STUDENT REPORT
# ==========================================

@app.get("/reports/student")
def student_report(
    student_id: str,
    from_date: str,
    to_date: str
):

    student_id = (
        student_id
        .strip()
        .upper()
    )

    student_response = (
        supabase
        .table("students")
        .select(
            "student_id, name, class_name"
        )
        .eq(
            "student_id",
            student_id
        )
        .execute()
    )

    if not student_response.data:

        return {

            "success": False,

            "message":
                "Student not found."
        }

    attendance_response = (
        supabase
        .table("attendance")
        .select(
            "attendance_date, present"
        )
        .eq(
            "student_id",
            student_id
        )
        .gte(
            "attendance_date",
            from_date
        )
        .lte(
            "attendance_date",
            to_date
        )
        .order(
            "attendance_date"
        )
        .execute()
    )

    present = sum(
        1
        for row in attendance_response.data
        if row["present"]
    )

    absent = sum(
        1
        for row in attendance_response.data
        if not row["present"]
    )

    student = (
        student_response.data[0]
    )

    return {

        "success": True,

        "student": {

            "student_id":
                student["student_id"],

            "name":
                student["name"],

            "class_name":
                student.get(
                    "class_name",
                    ""
                )
        },

        "from_date":
            from_date,

        "to_date":
            to_date,

        "present":
            present,

        "absent":
            absent,

        "records":
            attendance_response.data
    }


# ==========================================
# INDIVIDUAL REPORT DOWNLOAD
# ==========================================

@app.get("/reports/student/download")
def download_student_report(
    student_id: str,
    from_date: str,
    to_date: str
):

    data = student_report(
        student_id,
        from_date,
        to_date
    )

    if not data.get("success"):

        return data

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow([

        "Student ID",
        "Name",
        "Class",
        "Date",
        "Status"
    ])

    student = data["student"]

    for row in data["records"]:

        writer.writerow([

            student["student_id"],
            student["name"],
            student["class_name"],
            row["attendance_date"],

            "Present"
            if row["present"]
            else "Absent"
        ])

    output.seek(0)

    safe_id = (
        student_id
        .strip()
        .upper()
    )

    return StreamingResponse(

        iter([
            output.getvalue()
        ]),

        media_type=
            "text/csv",

        headers={
            "Content-Disposition":
                f"attachment; filename=student_{safe_id}_attendance.csv"
        }
    )


# ==========================================
# TEST FACE
# ==========================================

@app.post("/test-face")
async def test_face(
    image: UploadFile = File(...)
):

    contents = await image.read()

    frame = Image.open(
        io.BytesIO(contents)
    ).convert("RGB")

    frame_array = np.array(frame)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=frame_array
    )

    detection_result = (
        face_detector.detect(
            mp_image
        )
    )

    return {

        "face_count":
            len(
                detection_result.detections
            )
    }
