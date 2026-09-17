import os
import cv2
import mediapipe as mp
import requests

from collections import deque, Counter

from recognition.dinov2_model import DinoV2
from recognition.matcher import StudentMatcher
from recognition.database_loader import load_embeddings


# ==========================================
# SETTINGS
# ==========================================

THRESHOLD = 0.65

HISTORY_SIZE = 7
MIN_VOTES = 4

PADDING = 20

BACKEND_URL = "http://127.0.0.1:8000"
# Run DINOv2 every N frames for each tracked face.
# Lower = more recognition work.
# Higher = faster but less frequent recognition.
RECOGNITION_INTERVAL = 3

# Maximum movement allowed when matching
# a face to an existing track.
TRACK_DISTANCE = 100

# How many frames a track can disappear before
# being removed.
MAX_MISSED_FRAMES = 10


# ==========================================
# LOAD STUDENT EMBEDDINGS
# ==========================================

database = load_embeddings()


if len(database) == 0:

    print("No student embeddings found in Supabase.")

    exit()


for student_id, embeddings in database.items():

    print(
        f"Loaded student: {student_id} | "
        f"Embeddings: {embeddings.shape}"
    )


# ==========================================
# FACE DETECTOR MODEL PATH
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


MODEL_PATH = os.path.join(
    BASE_DIR,
    "face_detector.task"
)


if not os.path.exists(MODEL_PATH):

    print()
    print("Face detector model not found:")
    print(MODEL_PATH)

    exit()


# ==========================================
# LOAD DINOv2
# ==========================================

print()
print("Loading DINOv2...")

dino = DinoV2()


# ==========================================
# LOAD MEDIAPIPE
# ==========================================

BaseOptions = mp.tasks.BaseOptions

FaceDetector = mp.tasks.vision.FaceDetector

FaceDetectorOptions = (
    mp.tasks.vision.FaceDetectorOptions
)

VisionRunningMode = (
    mp.tasks.vision.RunningMode
)


options = FaceDetectorOptions(

    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),

    running_mode=VisionRunningMode.IMAGE,

    min_detection_confidence=0.6
)


face_detector = (
    FaceDetector.create_from_options(
        options
    )
)


# ==========================================
# CREATE MATCHER
# ==========================================

matcher = StudentMatcher(
    database
)


# ==========================================
# TRACK STORAGE
# ==========================================
#
# Each track looks like:
#
# {
#     "center": (x, y),
#     "history": deque(...),
#     "last_prediction": "001",
#     "last_score": 0.72,
#     "last_box": (...),
#     "missed": 0,
#     "last_recognition_frame": 0
# }
#
# ==========================================

tracks = {}

next_track_id = 0


# ==========================================
# FINAL DETECTED STUDENTS
# ==========================================

detected_students = set()


# ==========================================
# FRAME COUNTER
# ==========================================

frame_count = 0


# ==========================================
# CAMERA
# ==========================================

camera = cv2.VideoCapture(0)


if not camera.isOpened():

    print("Could not open camera.")

    face_detector.close()

    exit()


# ==========================================
# CAMERA INFORMATION
# ==========================================

print()
print("====================================")
print("LIVE FACE RECOGNITION")
print("====================================")

print(
    "Students:",
    list(database.keys())
)

print(
    "Threshold:",
    THRESHOLD
)

print(
    "History size:",
    HISTORY_SIZE
)

print(
    "Required votes:",
    MIN_VOTES
)

print(
    "Recognition interval:",
    RECOGNITION_INTERVAL
)

print()
print("Press Q to quit.")

print("====================================")


# ==========================================
# MAIN LOOP
# ==========================================

while True:

    success, frame = camera.read()


    if not success:

        print("Could not read frame.")

        break


    frame_count += 1


    # ======================================
    # FACE DETECTION
    # ======================================

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )


    result = face_detector.detect(
        mp_image
    )


    # ======================================
    # CURRENT DETECTIONS
    # ======================================

    current_detections = []


    if result.detections:

        for detection in result.detections:

            bbox = detection.bounding_box


            x = bbox.origin_x
            y = bbox.origin_y

            w = bbox.width
            h = bbox.height


            # ------------------------------
            # ORIGINAL BOUNDARY
            # ------------------------------

            x = max(0, x)
            y = max(0, y)

            x2 = min(
                frame.shape[1],
                x + w
            )

            y2 = min(
                frame.shape[0],
                y + h
            )


            if x2 <= x or y2 <= y:

                continue


            # ------------------------------
            # FACE CENTER
            # ------------------------------

            center_x = (
                x + x2
            ) // 2

            center_y = (
                y + y2
            ) // 2


            current_detections.append({

                "bbox": (
                    x,
                    y,
                    x2,
                    y2
                ),

                "center": (
                    center_x,
                    center_y
                )
            })


    # ======================================
    # TRACK MATCHING
    # ======================================

    matched_tracks = set()

    matched_detections = set()


    for detection_index, detection_data in enumerate(
        current_detections
    ):

        center = detection_data[
            "center"
        ]


        best_track_id = None

        best_distance = float("inf")


        # ----------------------------------
        # FIND CLOSEST EXISTING TRACK
        # ----------------------------------

        for track_id, track in tracks.items():

            if track_id in matched_tracks:

                continue


            old_center = track[
                "center"
            ]


            distance = (
                (
                    center[0] - old_center[0]
                ) ** 2

                +

                (
                    center[1] - old_center[1]
                ) ** 2
            ) ** 0.5


            if (
                distance < best_distance
                and distance <= TRACK_DISTANCE
            ):

                best_distance = distance

                best_track_id = track_id


        # ----------------------------------
        # USE EXISTING TRACK
        # ----------------------------------

        if best_track_id is not None:

            track_id = best_track_id

            matched_tracks.add(
                track_id
            )

            matched_detections.add(
                detection_index
            )

        # ----------------------------------
        # CREATE NEW TRACK
        # ----------------------------------

        else:

            track_id = next_track_id

            next_track_id += 1

            tracks[track_id] = {

                "center": center,

                "history": deque(
                    maxlen=HISTORY_SIZE
                ),

                "last_prediction": (
                    "CHECKING"
                ),

                "last_score": 0.0,

                "last_box": (
                    0,
                    0,
                    0,
                    0
                ),

                "missed": 0,

                "last_recognition_frame": (
                    -RECOGNITION_INTERVAL
                )
            }


    # ======================================
    # PROCESS CURRENT DETECTIONS
    # ======================================

    for detection_index, detection_data in enumerate(
        current_detections
    ):

        center = detection_data[
            "center"
        ]

        x1, y1, x2, y2 = (
            detection_data["bbox"]
        )


        # ----------------------------------
        # FIND TRACK ID
        # ----------------------------------

        assigned_track_id = None


        for track_id in matched_tracks:

            track = tracks[
                track_id
            ]


            if track[
                "center"
            ] == center:

                assigned_track_id = (
                    track_id
                )

                break


        # ----------------------------------
        # SAFER TRACK IDENTIFICATION
        # ----------------------------------
        #
        # The center can occasionally be
        # identical, so if not found above,
        # find the closest current track.
        #
        # ----------------------------------

        if assigned_track_id is None:

            best_distance = float("inf")

            for track_id in matched_tracks:

                track = tracks[
                    track_id
                ]

                old_center = track[
                    "center"
                ]

                distance = (
                    (
                        center[0]
                        - old_center[0]
                    ) ** 2

                    +

                    (
                        center[1]
                        - old_center[1]
                    ) ** 2
                ) ** 0.5


                if distance < best_distance:

                    best_distance = distance

                    assigned_track_id = (
                        track_id
                    )


        if assigned_track_id is None:

            continue


        track = tracks[
            assigned_track_id
        ]


        # ----------------------------------
        # UPDATE TRACK POSITION
        # ----------------------------------

        track["center"] = center

        track["last_box"] = (
            x1,
            y1,
            x2,
            y2
        )

        track["missed"] = 0


        # ==================================
        # SHOULD WE RUN DINOv2?
        # ==================================

        should_recognize = (
            frame_count
            - track[
                "last_recognition_frame"
            ]
            >= RECOGNITION_INTERVAL
        )


        if should_recognize:

            # ------------------------------
            # ADD FACE PADDING
            # ------------------------------

            crop_x1 = max(
                0,
                x1 - PADDING
            )

            crop_y1 = max(
                0,
                y1 - PADDING
            )

            crop_x2 = min(
                frame.shape[1],
                x2 + PADDING
            )

            crop_y2 = min(
                frame.shape[0],
                y2 + PADDING
            )


            face = frame[
                crop_y1:crop_y2,
                crop_x1:crop_x2
            ]


            if face.size != 0:

                # --------------------------
                # BGR → RGB
                # --------------------------

                face_rgb = cv2.cvtColor(
                    face,
                    cv2.COLOR_BGR2RGB
                )


                # --------------------------
                # DINOv2
                # --------------------------

                embedding = dino.extract(
                    face_rgb
                )


                # --------------------------
                # MATCH
                # --------------------------

                student_id, score = (
                    matcher.match(
                        embedding
                    )
                )


                # --------------------------
                # THRESHOLD
                # --------------------------

                if score >= THRESHOLD:

                    prediction = (
                        student_id
                    )

                else:

                    prediction = (
                        "UNKNOWN"
                    )


                # --------------------------
                # SAVE PREDICTION
                # --------------------------

                track[
                    "history"
                ].append(
                    prediction
                )


                track[
                    "last_prediction"
                ] = prediction


                track[
                    "last_score"
                ] = score


                track[
                    "last_recognition_frame"
                ] = frame_count


        # ==================================
        # TEMPORAL VOTING
        # ==================================

        history = track[
            "history"
        ]


        final_identity = (
            "UNKNOWN"
        )

        votes = 0


        if len(history) >= MIN_VOTES:

            counts = Counter(
                history
            )


            final_identity, votes = (
                counts.most_common(1)[0]
            )


            if (
                final_identity != "UNKNOWN"
                and votes >= MIN_VOTES
            ):

                display_identity = (
                    final_identity
                )


                # --------------------------
                # STABLE RECOGNITION
                # --------------------------

                detected_students.add(
                    final_identity
                )

            else:

                display_identity = (
                    "UNKNOWN"
                )

        else:

            display_identity = (
                "CHECKING"
            )


        # ==================================
        # SCORE
        # ==================================

        score = track[
            "last_score"
        ]


        # ==================================
        # LABEL
        # ==================================

        if display_identity == "CHECKING":

            label = (
                f"Checking... "
                f"{score:.2f}"
            )

        elif display_identity == "UNKNOWN":

            label = (
                f"UNKNOWN "
                f"{score:.2f}"
            )

        else:

            label = (
                f"{display_identity} "
                f"{score:.2f}"
            )


        # ==================================
        # DRAW BOX
        # ==================================

        cv2.rectangle(

            frame,

            (x1, y1),

            (x2, y2),

            (0, 255, 0),

            2
        )


        # ==================================
        # DRAW LABEL
        # ==================================

        cv2.putText(

            frame,

            label,

            (
                x1,
                max(
                    25,
                    y1 - 10
                )
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (0, 255, 0),

            2
        )


        # ==================================
        # DRAW TRACK ID
        # ==================================

        track_text = (
            f"Track {assigned_track_id}"
        )


        cv2.putText(

            frame,

            track_text,

            (
                x1,
                min(
                    frame.shape[0] - 30,
                    y2 + 20
                )
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.5,

            (255, 255, 0),

            1
        )


        # ==================================
        # DRAW VOTES
        # ==================================

        vote_text = (
            f"Votes: "
            f"{votes}/{HISTORY_SIZE}"
        )


        cv2.putText(

            frame,

            vote_text,

            (
                x1,
                min(
                    frame.shape[0] - 10,
                    y2 + 40
                )
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.5,

            (0, 255, 0),

            1
        )


    # ======================================
    # UPDATE MISSED TRACKS
    # ======================================

    current_track_ids = set(
        tracks.keys()
    )


    active_track_ids = set()


    for detection_index, detection_data in enumerate(
        current_detections
    ):

        center = detection_data[
            "center"
        ]


        best_track = None

        best_distance = float("inf")


        for track_id in tracks:

            old_center = tracks[
                track_id
            ][
                "center"
            ]


            distance = (
                (
                    center[0]
                    - old_center[0]
                ) ** 2

                +

                (
                    center[1]
                    - old_center[1]
                ) ** 2
            ) ** 0.5


            if (
                distance < best_distance
                and distance <= TRACK_DISTANCE
            ):

                best_distance = distance

                best_track = track_id


        if best_track is not None:

            active_track_ids.add(
                best_track
            )


    for track_id in current_track_ids:

        if track_id not in active_track_ids:

            tracks[
                track_id
            ]["missed"] += 1


    # ======================================
    # REMOVE OLD TRACKS
    # ======================================

    tracks_to_delete = []


    for track_id, track in tracks.items():

        if (
            track["missed"]
            > MAX_MISSED_FRAMES
        ):

            tracks_to_delete.append(
                track_id
            )


    for track_id in tracks_to_delete:

        del tracks[
            track_id
        ]


    # ======================================
    # DISPLAY INFORMATION
    # ======================================

    cv2.putText(

        frame,

        f"Faces: {len(current_detections)}",

        (20, 35),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (0, 255, 0),

        2
    )


    cv2.putText(

        frame,

        f"Students: {len(detected_students)}",

        (20, 65),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (0, 255, 0),

        2
    )


    # ======================================
    # SHOW CAMERA
    # ======================================

    cv2.imshow(

        "Student Attendance - Recognition",

        frame
    )


    # ======================================
    # QUIT
    # ======================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ==========================================
# CLEANUP
# ==========================================

camera.release()

face_detector.close()

cv2.destroyAllWindows()


# ==========================================
# FINAL RESULT
# ==========================================
print()
print("====================================")
print("RECOGNITION COMPLETE")
print("====================================")

print(
    "Detected students:",
    len(detected_students)
)


for student_id in sorted(
    detected_students
):

    print(
        "Student:",
        student_id
    )


# ==========================================
# SEND RESULTS TO FASTAPI
# ==========================================

student_ids = sorted(
    detected_students
)


try:

    response = requests.post(

        f"{BACKEND_URL}/recognition/results",

        json={
            "student_ids": student_ids
        },

        timeout=10
    )


    if response.status_code == 200:

        print()
        print(
            "Recognition results sent to backend."
        )

        print(
            response.json()
        )

    else:

        print()
        print(
            "Backend returned:",
            response.status_code
        )

        print(
            response.text
        )


except requests.exceptions.RequestException as error:

    print()
    print(
        "Could not send recognition results "
        "to backend."
    )

    print(
        "Error:",
        error
    )


print("====================================")
print("Recognition stopped.")