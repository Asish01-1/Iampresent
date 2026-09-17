import os
import sys
import time

import cv2
import mediapipe as mp


# --------------------------------------------------
# 1. Get student ID from command line
# --------------------------------------------------

if len(sys.argv) < 2:
    print("Usage:")
    print("python -m enrollment.capture_faces STUDENT_ID")
    print()
    print("Example:")
    print("python -m enrollment.capture_faces BISWA")
    sys.exit()

STUDENT_ID = sys.argv[1].strip().upper()

if not STUDENT_ID:
    print("Student ID cannot be empty.")
    sys.exit()


# --------------------------------------------------
# 2. Create student folder dynamically
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STUDENT_FOLDER = os.path.join(
    BASE_DIR,
    "data",
    "students",
    STUDENT_ID
)

os.makedirs(STUDENT_FOLDER, exist_ok=True)


# --------------------------------------------------
# 3. MediaPipe Face Detector
# --------------------------------------------------

MODEL_PATH = os.path.join(BASE_DIR, "face_detector.task")

BaseOptions = mp.tasks.BaseOptions
FaceDetector = mp.tasks.vision.FaceDetector
FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceDetectorOptions(
    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),
    running_mode=VisionRunningMode.IMAGE,
    min_detection_confidence=0.6
)

face_detector = FaceDetector.create_from_options(options)


# --------------------------------------------------
# 4. Camera
# --------------------------------------------------

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Could not open camera.")
    face_detector.close()
    sys.exit()


# --------------------------------------------------
# 5. Capture settings
# --------------------------------------------------

TOTAL_IMAGES = 30
CAPTURE_INTERVAL = 0.5

saved_count = 0
last_capture_time = 0


print()
print("======================================")
print("FACE ENROLLMENT")
print("======================================")
print("Student ID:", STUDENT_ID)
print("Saving to:", STUDENT_FOLDER)
print("Images:", TOTAL_IMAGES)
print()
print("Look at the camera.")
print("Move your head slightly between captures.")
print("Press Q to cancel.")
print("======================================")


# --------------------------------------------------
# 6. Main camera loop
# --------------------------------------------------

while saved_count < TOTAL_IMAGES:

    success, frame = camera.read()

    if not success:
        print("Could not read frame.")
        break

    # OpenCV gives BGR.
    # MediaPipe expects RGB.
    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    result = face_detector.detect(mp_image)

    if result.detections:

        detection = result.detections[0]

        bbox = detection.bounding_box

        x = bbox.origin_x
        y = bbox.origin_y
        w = bbox.width
        h = bbox.height

        # Convert bounding box to corners
        x1 = max(0, x)
        y1 = max(0, y)

        x2 = min(
            frame.shape[1],
            x + w
        )

        y2 = min(
            frame.shape[0],
            y + h
        )

        # Add padding around face
        padding = 20

        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)

        x2 = min(
            frame.shape[1],
            x2 + padding
        )

        y2 = min(
            frame.shape[0],
            y2 + padding
        )

        # Make sure crop is valid
        if x2 > x1 and y2 > y1:

            # Draw rectangle
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            current_time = time.time()

            if current_time - last_capture_time >= CAPTURE_INTERVAL:

                face = frame[y1:y2, x1:x2]

                saved_count += 1

                filename = f"{saved_count:03d}.jpg"

                image_path = os.path.join(
                    STUDENT_FOLDER,
                    filename
                )

                cv2.imwrite(
                    image_path,
                    face
                )

                last_capture_time = current_time

                print(
                    f"Captured {saved_count}/{TOTAL_IMAGES}: "
                    f"{filename}"
                )

                cv2.putText(
                    frame,
                    f"Captured: {saved_count}/{TOTAL_IMAGES}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

    else:

        cv2.putText(
            frame,
            "No face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )

    cv2.imshow(
        "Face Enrollment",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        print("Enrollment cancelled.")
        break


# --------------------------------------------------
# 7. Cleanup
# --------------------------------------------------

camera.release()
face_detector.close()
cv2.destroyAllWindows()


print()
print("======================================")

if saved_count == TOTAL_IMAGES:
    print("ENROLLMENT COMPLETE")
    print("Student:", STUDENT_ID)
    print("Images:", saved_count)
    print("Folder:", STUDENT_FOLDER)
else:
    print("ENROLLMENT INCOMPLETE")
    print("Student:", STUDENT_ID)
    print("Images saved:", saved_count)
    print("Folder:", STUDENT_FOLDER)

print("======================================")