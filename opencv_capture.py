import cv2, time
DEV = "/dev/video0"
cap = cv2.VideoCapture(DEV, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'RGB3'))  # Device liefert BGR-Bytes
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,1080)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_CONVERT_RGB, 0.0)  # wichtig: double, keine interne Umwandlung

assert cap.isOpened(), "Video device busy/nicht offen"
cv2.namedWindow("X1300 Live (RGB3/bgr24)", cv2.WINDOW_NORMAL)
cv2.resizeWindow("X1300 Live (RGB3/bgr24)", 960, 540)

# Warmup
t0 = time.time()
while time.time()-t0 < 2.0:
    ok, _ = cap.read()
    if ok: break
    time.sleep(0.01)

while True:
    ok, frame = cap.read()
    if not ok: time.sleep(0.005); continue
    # Frame ist bereits BGR (trotz FOURCC 'RGB3'), also direkt anzeigen:
    cv2.imshow("X1300 Live (RGB3/bgr24)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release(); cv2.destroyAllWindows()