# camera.py
# RK3588 AI Security Platform
# Dynamic scene switching version
#
# Features:
# 1. Campus mode: people >= 3 triggers crowd alarm
# 2. Warehouse mode: people >= 2 triggers loitering alarm
# 3. Restricted mode: person inside ROI triggers intrusion alarm
# 4. Home mode: face whitelist registration and stranger alarm

import cv2
import time
import threading
import os

from flask import Response
from detector import detect


# ======================
# folders
# ======================

os.makedirs("events", exist_ok=True)
os.makedirs("faces_db", exist_ok=True)
os.makedirs("faces_db/whitelist", exist_ok=True)


# ======================
# system status
# ======================

system_status = {
    "people": 0,
    "car": 0,
    "in_count": 0,
    "out_count": 0,
    "alarm_level": "LOW",
    "system": "STARTING",
    "intrusion": False,
    "crowd": False,
    "loitering": False,
    "stranger": False,
    "fps": 0,
    "inference_ms": 0,
    "mode": "dashboard",
    "events": [],
    "face_status": "NONE"
}


status_lock = threading.Lock()
frame_lock = threading.Lock()

current_mode = "dashboard"
latest_frame = None


# ======================
# OpenCV face detector
# ======================

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


# ======================
# whitelist cache
# ======================

whitelist_faces = []


def preprocess_face(face_img):

    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(
        gray,
        (100, 100)
    )

    gray = cv2.equalizeHist(gray)

    return gray


def load_whitelist_faces():

    global whitelist_faces

    whitelist_faces = []

    folder = "faces_db/whitelist"

    if not os.path.exists(folder):

        os.makedirs(folder, exist_ok=True)

        return

    for filename in os.listdir(folder):

        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):

            continue

        path = os.path.join(folder, filename)

        img = cv2.imread(path)

        if img is None:

            continue

        try:

            face = preprocess_face(img)

            whitelist_faces.append({
                "name": filename,
                "face": face
            })

        except Exception as e:

            print("load face failed:", filename, e)

    print("whitelist faces loaded:", len(whitelist_faces))


def detect_largest_face(frame):

    if frame is None:

        return None, None

    if face_cascade.empty():

        print("face cascade load failed")

        return None, None

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )

    if len(faces) == 0:

        return None, None

    faces = sorted(
        faces,
        key=lambda box: box[2] * box[3],
        reverse=True
    )

    x, y, w, h = faces[0]

    face_img = frame[
        y:y + h,
        x:x + w
    ]

    return (x, y, w, h), face_img


def is_whitelist_face(face_img):

    global whitelist_faces

    if face_img is None:

        return False

    if len(whitelist_faces) == 0:

        load_whitelist_faces()

    if len(whitelist_faces) == 0:

        return False

    try:

        face = preprocess_face(face_img)

    except Exception:

        return False

    best_score = 999999
    best_name = "unknown"

    for item in whitelist_faces:

        template = item["face"]

        diff = cv2.absdiff(
            face,
            template
        )

        score = diff.mean()

        if score < best_score:

            best_score = score
            best_name = item["name"]

    threshold = 50

    print(
        "face compare:",
        best_name,
        "score:",
        round(best_score, 2)
    )

    if best_score < threshold:

        return True

    return False


# ======================
# register face
# called by app.py
# ======================

def register_face(name="whitelist_user"):

    global latest_frame

    with frame_lock:

        if latest_frame is None:

            return {
                "status": "error",
                "message": "no camera frame"
            }

        frame = latest_frame.copy()

    box, face_img = detect_largest_face(frame)

    if face_img is None:

        return {
            "status": "error",
            "message": "no clear face detected"
        }

    safe_name = str(name).replace("/", "_").replace("\\", "_").strip()

    if safe_name == "":

        safe_name = "whitelist_user"

    filename = "{}_{}.jpg".format(
        safe_name,
        int(time.time())
    )

    save_path = os.path.join(
        "faces_db/whitelist",
        filename
    )

    cv2.imwrite(
        save_path,
        face_img
    )

    load_whitelist_faces()

    print("face registered:", save_path)

    return {
        "status": "ok",
        "message": "face registered",
        "name": safe_name,
        "file": save_path
    }


# ======================
# switch mode
# ======================

def set_mode(mode):

    global current_mode

    current_mode = mode

    with status_lock:

        system_status["mode"] = mode

    print("MODE SWITCH:", mode)


# ======================
# open camera
# ======================

def open_camera():

    for cam in [
        "/dev/video21",
        "/dev/video22",
        "/dev/video20",
        "/dev/video0",
        0
    ]:

        cap = cv2.VideoCapture(
            cam,
            cv2.CAP_V4L2
        )

        if cap.isOpened():

            cap.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                640
            )

            cap.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                480
            )

            cap.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )

            print("camera opened:", cam)

            return cap

        cap.release()

    raise RuntimeError("camera not found")


def get_status():

    with status_lock:

        return system_status.copy()


# ======================
# scene alarm rules
# ======================

def mode_check(
    mode,
    people,
    cars,
    restricted_alarm=False,
    stranger_alarm=False
):

    intrusion = False
    crowd = False
    loitering = False
    stranger = False
    alarm = "LOW"

    if mode == "mall":

        if people >= 8:

            crowd = True
            alarm = "MEDIUM"

    elif mode == "campus":

        if people >= 3:

            crowd = True
            alarm = "MEDIUM"

        if people >= 8:

            crowd = True
            alarm = "HIGH"

    elif mode == "factory":

        if people > 0:

            intrusion = True
            alarm = "HIGH"

    elif mode == "parking":

        if cars > 5:

            alarm = "MEDIUM"

    elif mode == "warehouse":

        if people >= 2:

            loitering = True
            alarm = "MEDIUM"

        if people >= 5:

            loitering = True
            alarm = "HIGH"

    elif mode == "home":

        if stranger_alarm:

            stranger = True
            intrusion = True
            alarm = "HIGH"

    elif mode == "restricted":

        if restricted_alarm:

            intrusion = True
            alarm = "HIGH"

    return intrusion, crowd, loitering, stranger, alarm


# ======================
# video generator
# ======================

def gen():

    global current_mode
    global latest_frame

    load_whitelist_faces()

    cap = open_camera()

    frame_id = 0
    last_results = []

    fps = 0
    count = 0
    last_time = time.time()

    total_in = 0
    total_out = 0
    previous_people = 0

    while True:

        mode = current_mode

        ret, frame = cap.read()

        if not ret:

            continue

        with frame_lock:

            latest_frame = frame.copy()

        frame_id += 1
        count += 1

        if time.time() - last_time >= 1:

            fps = count
            count = 0
            last_time = time.time()

        start = time.time()

        if frame_id % 2 == 0:

            last_results = detect(frame)
            inference = (time.time() - start) * 1000

        else:

            inference = 0

        people = 0
        cars = 0
        restricted_alarm = False
        stranger_alarm = False
        face_status = "NONE"

        h, w = frame.shape[:2]

        if mode == "restricted":

            roi_x1, roi_y1 = int(w * 0.1), int(h * 0.1)
            roi_x2, roi_y2 = int(w * 0.9), int(h * 0.9)

        for obj in last_results:

            name = obj["name"]
            conf = obj["conf"]
            x1, y1, x2, y2 = obj["xyxy"]

            if conf < 0.5:

                continue

            color = (0, 255, 0)

            if name == "person":

                people += 1

                if mode == "restricted":

                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2

                    if roi_x1 < cx < roi_x2 and roi_y1 < cy < roi_y2:

                        restricted_alarm = True
                        color = (0, 0, 255)

            elif name == "car":

                cars += 1
                color = (255, 0, 0)

            else:

                continue

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

        # ======================
        # home mode face whitelist
        # ======================

        if mode == "home" and people > 0:

            face_box, face_img = detect_largest_face(frame)

            if face_img is None:

                stranger_alarm = True
                face_status = "NO_FACE"

            else:

                is_white = is_whitelist_face(face_img)

                fx, fy, fw, fh = face_box

                if is_white:

                    face_status = "WHITELIST"

                    cv2.rectangle(
                        frame,
                        (fx, fy),
                        (fx + fw, fy + fh),
                        (0, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        "WHITELIST",
                        (fx, fy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )

                else:

                    stranger_alarm = True
                    face_status = "STRANGER"

                    cv2.rectangle(
                        frame,
                        (fx, fy),
                        (fx + fw, fy + fh),
                        (0, 0, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        "STRANGER",
                        (fx, fy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )

        if people > previous_people:

            total_in += people - previous_people

        elif people < previous_people:

            total_out += previous_people - people

        previous_people = people

        intrusion, crowd, loitering, stranger, alarm = mode_check(
            mode,
            people,
            cars,
            restricted_alarm,
            stranger_alarm
        )

        with status_lock:

            system_status.update({
                "people": people,
                "car": cars,
                "in_count": total_in,
                "out_count": total_out,
                "alarm_level": alarm,
                "intrusion": intrusion,
                "crowd": crowd,
                "loitering": loitering,
                "stranger": stranger,
                "fps": fps,
                "inference_ms": round(inference, 2),
                "system": "ONLINE",
                "mode": mode,
                "face_status": face_status
            })

        if mode == "restricted":

            cv2.rectangle(
                frame,
                (roi_x1, roi_y1),
                (roi_x2, roi_y2),
                (0, 0, 255),
                3
            )

            cv2.putText(
                frame,
                "RESTRICTED AREA",
                (roi_x1, roi_y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        cv2.putText(
            frame,
            f"MODE:{mode}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"PEOPLE:{people}",
            (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"ALARM:{alarm}",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255) if alarm == "HIGH" else (0, 255, 255),
            2
        )

        if mode == "home":

            cv2.putText(
                frame,
                f"FACE:{face_status}",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0) if face_status == "WHITELIST" else (0, 0, 255),
                2
            )

            cv2.putText(
                frame,
                f"FPS:{fps} {inference:.1f}ms",
                (20, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

        else:

            cv2.putText(
                frame,
                f"FPS:{fps} {inference:.1f}ms",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

        ret, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 75]
        )

        if ret:

            yield (
                b"--frame\r\n"
                b"Content-Type:image/jpeg\r\n\r\n" +
                buffer.tobytes() +
                b"\r\n"
            )


def get_camera_stream():

    return Response(
        gen(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )
