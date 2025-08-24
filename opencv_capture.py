#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Logger früh dämpfen, bevor cv2 geladen wird
import os
os.environ.setdefault("OPENCV_LOG_LEVEL", "SILENT")  # alternativ: "ERROR"

import sys, time, cv2
try:
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
except Exception:
    pass

# --- Env ---------------------------------------------------------------------
env = "/tmp/x1300_env"
if os.path.exists(env):
    with open(env) as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k] = v

DEV    = os.environ.get("X1300_DEVICE", "/dev/video0")
PIXFMT = os.environ.get("X1300_PIXFMT", "RGB3").upper()  # RGB3/BGR3/YUYV/UYVY
W      = int(os.environ.get("X1300_WIDTH",  "1920"))
H      = int(os.environ.get("X1300_HEIGHT", "1080"))
SWAP_RB = int(os.environ.get("X1300_SWAP_RB", "0")) == 1  # erzwinge R/B-Tausch

# --- Capture -----------------------------------------------------------------
cap = cv2.VideoCapture(DEV, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*PIXFMT))
cap.set(cv2.CAP_PROP_CONVERT_RGB, 0.0)  # manche Stacks ignorieren das leider

if not cap.isOpened():
    sys.exit(f"[X1300][FATAL] Cannot open {DEV}")

def fourcc_to_str(v):
    v = int(v)
    return "".join([chr((v >> (8 * i)) & 0xFF) for i in range(4)])

actual_fourcc = fourcc_to_str(cap.get(cv2.CAP_PROP_FOURCC))
title = f"X1300 Live {W}x{H} (req:{PIXFMT}/act:{actual_fourcc})"
cv2.namedWindow(title, cv2.WINDOW_NORMAL)
cv2.resizeWindow(title, max(320, W//2), max(180, H//2))

# --- Format → BGR (minimal, kein Doppel-Swap) --------------------------------
def to_bgr(img, fmt, force_swap_rb=False):
    fmt = fmt.upper()
    if fmt == "YUYV":
        img = cv2.cvtColor(img, cv2.COLOR_YUV2BGR_YUYV)
    elif fmt == "UYVY":
        img = cv2.cvtColor(img, cv2.COLOR_YUV2BGR_UYVY)
    # RGB3/BGR3: nichts tun – wir vertrauen dem Backend
    if force_swap_rb:
        img = img[:, :, ::-1]
    return img

# --- Warmup ------------------------------------------------------------------
t0 = time.time()
ok = False
while time.time() - t0 < 2.0:
    ok, _ = cap.read()
    if ok: break
    time.sleep(0.01)
if not ok:
    cap.release(); cv2.destroyAllWindows()
    sys.exit("[X1300][FATAL] No frame within 2s.")

# --- Loop (eigene FPS-Messung, keine cap.get(CAP_PROP_FPS)) ------------------
last_title = time.time()
fps_cnt, fps_t0 = 0, time.time()

blank = 0
while True:
    ok, raw = cap.read()
    if not ok:
        blank += 1
        if blank > 60:
            print("[X1300][WARN] 60 leere Reads -> Pipeline prüfen"); blank = 0
        time.sleep(0.002); continue

    frame = to_bgr(raw, PIXFMT, SWAP_RB)

    # FPS selbst messen (Frames / Zeitfenster)
    fps_cnt += 1
    now = time.time()
    if now - last_title >= 1.0:
        fps_est = fps_cnt / (now - fps_t0)
        cv2.setWindowTitle(title, f"{title} ~{fps_est:.0f} FPS")
        last_title = now
        fps_cnt, fps_t0 = 0, now

    cv2.imshow(title, frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        SWAP_RB = not SWAP_RB
        print(f"[X1300] SWAP_RB -> {SWAP_RB}")

cap.release()
cv2.destroyAllWindows()
