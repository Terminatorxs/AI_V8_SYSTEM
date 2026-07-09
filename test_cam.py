import cv2

print("Scanning cameras...")

for i in range(0, 5):
    print("Trying index:", i)

    cap = cv2.VideoCapture(i, cv2.CAP_MSMF)

    if cap.isOpened():
        ret, frame = cap.read()

        if ret:
            print("✅ CAMERA FOUND AT INDEX:", i)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                cv2.imshow("camera", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()
            exit()

    cap.release()

print("❌ NO CAMERA FOUND")