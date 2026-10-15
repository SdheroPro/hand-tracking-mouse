#!/usr/bin/env python3
"""
Gesture Mouse - single-file generator / installer / launcher.

    python gesture_mouse_setup.py              -> generate files, create venv, install, run
    python gesture_mouse_setup.py --build      -> also build a Windows .exe (PyInstaller)
    python gesture_mouse_setup.py --build --onefile
    python gesture_mouse_setup.py --no-run     -> generate + install only

Requires Python 3.9 - 3.12 (MediaPipe wheels) and a webcam.
"""
import argparse
import os
import subprocess
import sys

FILES = {}

# ---------------------------------------------------------------- requirements
FILES["requirements.txt"] = r'''mediapipe==0.10.21
customtkinter>=5.2.2
opencv-contrib-python
numpy
Pillow
pynput
pystray
'''

# ---------------------------------------------------------------- main.py
FILES["main.py"] = r'''import ctypes
import os
import sys
import traceback

if sys.stdout is None:  # windowed .exe has no console
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

if os.name == "nt":  # must happen before Tk is created: pixel-accurate cursor mapping
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def notify(title, msg):
    try:
        if os.name == "nt":
            ctypes.windll.user32.MessageBoxW(0, msg, title, 0x40)
        else:
            print(title + ": " + msg)
    except Exception:
        pass


def single_instance():
    import socket
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 47653))
        return s
    except OSError:
        return None


if __name__ == "__main__":
    lock = single_instance()
    if lock is None:
        notify("Gesture Mouse", "Gesture Mouse is already running (check the system tray).")
        sys.exit(0)
    try:
        from app.ui import App
        App().run()
    except Exception:
        tb = traceback.format_exc()
        try:
            from app import config
            with open(os.path.join(config.data_dir(), "error.log"), "a", encoding="utf-8") as f:
                f.write(tb + "\n")
        except Exception:
            pass
        notify("Gesture Mouse - error", "The program hit an error:\n\n" + tb[-900:])
'''

FILES["app/__init__.py"] = ""

# ---------------------------------------------------------------- config.py
FILES["app/config.py"] = r'''import copy
import json
import os

APP = "GestureMouse"
CFG_VERSION = 3


def data_dir():
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    p = os.path.join(base, APP)
    os.makedirs(p, exist_ok=True)
    return p


CFG_PATH = os.path.join(data_dir(), "settings.json")
GES_PATH = os.path.join(data_dir(), "gestures.json")

ACTIONS = {
    "move": "Move cursor",
    "left_click": "Left click",
    "right_click": "Right click",
    "double_click": "Double click",
    "middle_click": "Middle click",
    "drag": "Grab / drag and drop (hold)",
    "scroll": "Scroll (move hand up / down)",
    "back_click": "Mouse back button",
    "forward_click": "Mouse forward button",
    "pause": "Pause / resume control",
}

BUILTIN = {
    "open_hand": "Open hand (fingers spread)",
    "fist": "Closed fist",
    "index_up": "Only the index finger up",
    "peace": "Index + middle finger up (V sign)",
    "three_fingers": "Index + middle + ring finger up",
    "rock": "Index + pinky up",
    "pinch_index": "Thumb touches index fingertip",
    "pinch_middle": "Thumb touches middle fingertip",
    "pinch_ring": "Thumb touches ring fingertip",
    "pinch_pinky": "Thumb touches pinky fingertip",
}

SHORT = {
    "open_hand": "Open hand", "fist": "Fist", "index_up": "Index up", "peace": "Two fingers",
    "three_fingers": "Three fingers", "rock": "Index + pinky", "pinch_index": "Thumb + index",
    "pinch_middle": "Thumb + middle", "pinch_ring": "Thumb + ring", "pinch_pinky": "Thumb + pinky",
}

EMOJI = {
    "open_hand": "\u270b", "fist": "\u270a", "index_up": "\u261d", "peace": "\u270c", "three_fingers": "\u22ee",
    "rock": "\u2606", "pinch_index": "\u25c9", "pinch_middle": "\u25c9", "pinch_ring": "\u25c9", "pinch_pinky": "\u25c9",
}

DEFAULT_BINDINGS = {
    "move": "open_hand",
    "left_click": "pinch_index",
    "right_click": "pinch_middle",
    "double_click": "pinch_ring",
    "middle_click": "pinch_pinky",
    "drag": "fist",
    "scroll": "peace",
    "back_click": None,
    "forward_click": None,
    "pause": "three_fingers",
}

PRESETS = {
    "Beginner (extra smooth)": {"min_cutoff": 0.8, "beta": 5.0, "gain": 1.0, "stable_frames": 4, "click_cooldown": 0.5},
    "Balanced": {"min_cutoff": 1.5, "beta": 10.0, "gain": 1.0, "stable_frames": 3, "click_cooldown": 0.35},
    "Fast / gaming": {"min_cutoff": 3.0, "beta": 20.0, "gain": 1.3, "stable_frames": 2, "click_cooldown": 0.25},
}

DEFAULTS = {
    "theme": "Midnight Blue",
    "preset": "Balanced",
    "first_run": True,
    "camera_index": 0,
    "camera_url": "",
    "resolution": "640x480",
    "mirror": True,
    "rotate": "0",
    "brightness": 0.0,
    "contrast": 1.0,
    "hand": "Any",
    "model_complexity": 1,
    "auto_perf": True,
    "det_conf": 0.7,
    "track_conf": 0.6,
    "show_overlay": True,
    "region": [0.2, 0.15, 0.8, 0.7],
    "pointer": "palm",
    "min_cutoff": 1.5,
    "beta": 10.0,
    "gain": 1.0,
    "stable_frames": 3,
    "click_rewind": 3,
    "deadzone": 2.0,
    "drag_grace": 6,
    "pinch_lock": True,
    "click_cooldown": 0.35,
    "pinch_threshold": 0.30,
    "knn_threshold": 0.6,
    "scroll_speed": 40.0,
    "scroll_invert": False,
    "dwell_click": False,
    "dwell_time": 1.2,
    "start_engine": False,
    "start_minimized": False,
    "close_to_tray": True,
    "autostart": False,
    "hotkey": "<ctrl>+<alt>+g",
    "popup_on_start": False,
    "popup_w": 320,
    "popup_alpha": 0.9,
    "popup_x": 20,
    "popup_y": 20,
    "popup_borderless": True,
    "cfg_version": CFG_VERSION,
    "bindings": DEFAULT_BINDINGS,
}


def load():
    cfg = copy.deepcopy(DEFAULTS)
    try:
        with open(CFG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if saved.get("cfg_version", 1) < CFG_VERSION:  # old install: take the new gesture defaults
            for k in ("bindings", "pointer", "theme", "first_run", "model_complexity", "click_rewind"):
                saved.pop(k, None)
        for k, v in saved.items():
            if k == "bindings":
                cfg["bindings"].update({a: g for a, g in v.items() if a in ACTIONS})
            else:
                cfg[k] = v
    except Exception:
        pass
    cfg["cfg_version"] = CFG_VERSION
    return cfg


def save(cfg):
    try:
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass
'''

# ---------------------------------------------------------------- gestures.py
FILES["app/gestures.py"] = r'''import json

import numpy as np

from .config import GES_PATH

TIPS = (8, 12, 16, 20)
MCPS = (5, 9, 13, 17)
PINCH_NAMES = ("pinch_index", "pinch_middle", "pinch_ring", "pinch_pinky")


def d(a, b):
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


def analyse(pts):
    """pts: 21x2 pixel coordinates -> scale-invariant hand metrics."""
    size = d(pts[0], pts[9]) or 1.0
    # extension ratio = fingertip / knuckle distance from wrist: 1 extended, 0 curled, -1 unsure
    ratio = [d(pts[t], pts[0]) / max(d(pts[mc], pts[0]), 1e-6) for t, mc in zip(TIPS, MCPS)]
    ext = [1 if r > 1.45 else (0 if r < 1.25 else -1) for r in ratio]
    thumb = int(d(pts[4], pts[5]) / size > 0.6)
    pinch = [d(pts[4], pts[t]) / size for t in TIPS]
    reach = [d(pts[t], pts[0]) / size for t in TIPS]
    return {"ext": ext, "thumb": thumb, "pinch": pinch, "reach": reach, "size": size}


def near_pinch(m, thr, mult=1.5):
    """True when the thumb is approaching a fingertip (used to freeze the cursor before a click)."""
    return any(r < thr * mult and rc > 0.95 for r, rc in zip(m["pinch"], m["reach"]))


def classify_builtin(m, thr, prev=None, exit_mult=1.4):
    """Rule based gestures. `prev` enables hysteresis: a pinch is released only at thr*exit_mult."""
    best, best_score = None, 9.0
    for i, (r, rc) in enumerate(zip(m["pinch"], m["reach"])):
        held = prev == PINCH_NAMES[i]
        limit = thr * exit_mult if held else thr
        if r < limit and rc > (0.85 if held else 0.95) and r / limit < best_score:
            best, best_score = i, r / limit
    if best is not None:
        return PINCH_NAMES[best]
    e = list(m["ext"])
    if 0 not in e and e.count(1) >= 3:
        return "open_hand"
    if 1 not in e and e.count(0) >= 3:
        return "fist"
    table = {
        (1, 0, 0, 0): "index_up",
        (1, 1, 0, 0): "peace",
        (1, 1, 1, 0): "three_fingers",
        (1, 0, 0, 1): "rock",
    }
    return table.get(tuple(e))


def features(pts, label):
    """Translation/scale-normalised 42-vector; left hands are mirrored to look like right hands."""
    p = pts - pts[0]
    s = float(np.abs(p).max()) or 1.0
    v = p / s
    if label == "Left":
        v[:, 0] *= -1
    return v.flatten().astype(np.float32)


class GestureStore:
    """User-trained gestures + tiny k-NN classifier (no scikit-learn needed -> small .exe)."""

    def __init__(self):
        self.data = {}
        self.model = (np.zeros((0, 42), np.float32), [])
        self.load()

    def load(self):
        try:
            with open(GES_PATH, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception:
            self.data = {}
        self._build()

    def save(self):
        try:
            with open(GES_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
        except Exception:
            pass
        self._build()

    def _build(self):
        X, y = [], []
        for n, v in self.data.items():
            for s in v:
                X.append(s)
                y.append(n)
        arr = np.array(X, dtype=np.float32) if X else np.zeros((0, 42), np.float32)
        self.model = (arr, y)

    def add(self, name, samples):
        self.data.setdefault(name, []).extend(samples)
        self.save()

    def delete(self, name):
        self.data.pop(name, None)
        self.save()

    def predict(self, vec, k=5, thr=0.6):
        X, y = self.model
        if len(y) == 0:
            return None
        dist = np.linalg.norm(X - vec, axis=1)
        idx = np.argsort(dist)[:k]
        votes = {}
        for i in idx:
            votes.setdefault(y[i], []).append(float(dist[i]))
        name, ds = max(votes.items(), key=lambda kv: (len(kv[1]), -np.mean(kv[1])))
        return name if np.mean(ds) < thr else None
'''

# ---------------------------------------------------------------- engine.py
FILES["app/engine.py"] = r'''import math
import os
import threading
import time
from collections import deque

import cv2
import mediapipe as mp
import numpy as np
from pynput.mouse import Button, Controller

from .config import ACTIONS
from .gestures import analyse, classify_builtin, features, near_pinch

CLICKS = {
    "left_click": (Button.left, 1),
    "right_click": (Button.right, 1),
    "double_click": (Button.left, 2),
    "middle_click": (Button.middle, 1),
}
for _k, _n in (("back_click", "x1"), ("forward_click", "x2")):
    if hasattr(Button, _n):
        CLICKS[_k] = (getattr(Button, _n), 1)

POINTERS = {"index_tip": [8], "index_base": [5], "palm": [0, 5, 9, 13, 17]}


def screen_size():
    try:
        import ctypes
        u = ctypes.windll.user32
        return u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    except Exception:
        import tkinter
        r = tkinter.Tk()
        r.withdraw()
        w, h = r.winfo_screenwidth(), r.winfo_screenheight()
        r.destroy()
        return w, h


class OneEuro:
    """One Euro filter: heavy smoothing when still, low lag when moving fast."""

    def __init__(self):
        self.mc, self.beta, self.dc = 1.5, 10.0, 1.0
        self.reset()

    def reset(self):
        self.t = None
        self.x = 0.0
        self.dx = 0.0

    @staticmethod
    def _a(cut, dt):
        tau = 1.0 / (2 * math.pi * cut)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, x, t):
        if self.t is None:
            self.t, self.x, self.dx = t, x, 0.0
            return x
        dt = max(t - self.t, 1e-3)
        a = self._a(self.dc, dt)
        self.dx = a * ((x - self.x) / dt) + (1 - a) * self.dx
        a = self._a(self.mc + self.beta * abs(self.dx), dt)
        self.x = a * x + (1 - a) * self.x
        self.t = t
        return self.x


class Grabber(threading.Thread):
    """Reads the camera in its own thread so processing always sees the newest frame (low latency)."""

    def __init__(self, cap):
        super().__init__(daemon=True)
        self.cap, self.frame, self.id, self.t, self.alive = cap, None, 0, 0.0, True

    def run(self):
        while self.alive:
            ok, f = self.cap.read()
            if ok:
                self.frame, self.t = f, time.time()
                self.id += 1
            else:
                time.sleep(0.01)


class Engine(threading.Thread):
    def __init__(self, cfg, store):
        super().__init__(daemon=True)
        self.cfg, self.store = cfg, store
        self.running, self.paused, self.frozen = True, False, False
        self.frame, self.frame_id = None, 0
        self.fps = 0.0
        self.gesture = self.stable = self.action = None
        self.error = None
        self.vec = self.metrics = self.raw_ptr = None
        self.mouse = Controller()
        self.sw, self.sh = screen_size()
        self.fx, self.fy = OneEuro(), OneEuro()
        self.hist = deque(maxlen=12)
        self.cand, self.cnt, self.prev_act = None, 0, None
        self.dragging, self.drag_miss = False, 0
        self.scroll_ref = None
        self.last_click = 0.0
        self.cur = None      # stabilised target position (screen px, float)
        self.mpos = None     # position we last sent to the OS
        self.glide = 0
        self.sp = None       # smoothed landmarks used for classification
        self.events = deque(maxlen=40)
        self.ev_count = 0
        self.dwell_anchor, self.dwell_t = None, 0.0

    # ------------------------------------------------------------- helpers
    def _log(self, txt):
        self.events.append((time.strftime("%H:%M:%S"), txt))
        self.ev_count += 1

    def _pick(self, res):
        if not res.multi_hand_landmarks:
            return None, None
        want = self.cfg["hand"]
        for lm, hd in zip(res.multi_hand_landmarks, res.multi_handedness):
            label = hd.classification[0].label
            if not self.cfg["mirror"]:
                label = "Left" if label == "Right" else "Right"
            if want == "Any" or want == label:
                return lm, label
        return None, None

    def _stable(self, g):
        if g == self.cand:
            self.cnt += 1
        else:
            self.cand, self.cnt = g, 1
        if self.cnt >= int(self.cfg["stable_frames"]):
            self.stable = self.cand
        return self.stable

    def _stabilise(self, tx, ty):
        """Jitter filter: the target only moves once it leaves a small dead-zone around the last position."""
        dz = float(self.cfg["deadzone"])
        if self.cur is None:
            self.cur = [tx, ty]
            return
        dx, dy = tx - self.cur[0], ty - self.cur[1]
        dist = math.hypot(dx, dy)
        if dist > dz:
            k = (dist - dz) / dist
            self.cur[0] += dx * k
            self.cur[1] += dy * k

    def _rewind(self):
        k = int(self.cfg["click_rewind"])
        if k > 0 and len(self.hist) >= k:
            p = self.hist[-k]
            self.mouse.position = p
            self.mpos = [float(p[0]), float(p[1])]

    def _move(self):
        tx, ty = self.cur
        if self.mpos is None:
            self.mpos = [tx, ty]
        ease = 0.3 if self.glide > 0 else 1.0
        if self.glide > 0:
            self.glide -= 1
        self.mpos[0] += (tx - self.mpos[0]) * ease
        self.mpos[1] += (ty - self.mpos[1]) * ease
        p = (int(round(self.mpos[0])), int(round(self.mpos[1])))
        self.mouse.position = p
        self.hist.append(p)

    def _release(self):
        if self.dragging:
            try:
                self.mouse.release(Button.left)
            except Exception:
                pass
            self.dragging = False
            self._log("Drop")
        self.scroll_ref = None

    # ------------------------------------------------------------- actions
    def _apply(self, act, have, fy, lock):
        cfg, now = self.cfg, time.time()
        grace = int(cfg["drag_grace"])
        if self.dragging and act != "drag" and have and self.drag_miss < grace:
            self.drag_miss += 1      # ignore short gesture flicker while holding a grab
            act = "drag"
        elif act == "drag":
            self.drag_miss = 0
        edge = act != self.prev_act
        self.action = act
        if act == "pause" and edge and not self.frozen:
            self.paused = not self.paused
            self._log("Paused" if self.paused else "Resumed")
        if self.paused or self.frozen:
            self._release()
            self.prev_act = act
            return
        if not have:
            if self.dragging and self.drag_miss < grace * 2:
                self.drag_miss += 1
                return
            self._release()
            self.prev_act = act
            return
        if edge and act in ("move", "drag") and self.prev_act not in ("move", "drag"):
            try:
                self.mpos = [float(v) for v in self.mouse.position]
            except Exception:
                self.mpos = None
            self.glide = 6
        if edge and act in CLICKS and now - self.last_click > cfg["click_cooldown"]:
            self._rewind()
            btn, n = CLICKS[act]
            self.mouse.click(btn, n)
            self.last_click = now
            self._log(ACTIONS.get(act, act))
        if edge and act == "drag":
            self._rewind()
            self.mouse.press(Button.left)
            self.dragging, self.drag_miss = True, 0
            self._log("Grab")
        if self.dragging and act != "drag":
            self._release()
        if act in ("move", "drag") and not (act == "move" and lock):
            self._move()
        if act == "move" and cfg.get("dwell_click") and self.cur:
            a = self.dwell_anchor
            if a is None or math.hypot(self.cur[0] - a[0], self.cur[1] - a[1]) > 35:
                self.dwell_anchor, self.dwell_t = (self.cur[0], self.cur[1]), now
            elif now - self.dwell_t > cfg["dwell_time"] and now - self.last_click > 0.8:
                self.mouse.click(Button.left, 1)
                self.last_click = self.dwell_t = now
                self._log("Dwell click")
        else:
            self.dwell_anchor = None
        if act == "scroll":
            if edge or self.scroll_ref is None:
                self.scroll_ref = fy
            dlt = (self.scroll_ref - fy) * cfg["scroll_speed"] * (-1 if cfg["scroll_invert"] else 1)
            steps = int(dlt)
            if steps:
                self.mouse.scroll(0, steps)
                self.scroll_ref = fy
        else:
            self.scroll_ref = None
        self.prev_act = act

    # ------------------------------------------------------------- main loop
    def _make_hands(self, cx):
        c = self.cfg
        return mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1 if c["hand"] == "Any" else 2,
            model_complexity=cx,
            min_detection_confidence=float(c["det_conf"]),
            min_tracking_confidence=float(c["track_conf"]),
        )

    def run(self):
        cfg = self.cfg
        try:
            w, h = [int(v) for v in cfg["resolution"].split("x")]
        except Exception:
            w, h = 640, 480
        idx = int(cfg["camera_index"])
        url = str(cfg.get("camera_url", "")).strip()
        if url:
            cap = cv2.VideoCapture(url)
        else:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(idx)
            try:
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  # much higher FPS on most webcams
            except Exception:
                pass
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            self.error = "Cannot open the camera (%s). Close other apps using it or choose another camera." % (url or idx)
            return
        grab = Grabber(cap)
        grab.start()
        t0 = time.time()
        while grab.id == 0 and time.time() - t0 < 5 and self.running:
            time.sleep(0.02)
        if grab.id == 0:
            self.error = "The camera opened but sends no images. Try another camera."
            grab.alive = False
            cap.release()
            return
        cx = int(cfg["model_complexity"])
        hands = self._make_hands(cx)
        conns = list(mp.solutions.hands.HAND_CONNECTIONS)
        ip = lambda p: (int(p[0]), int(p[1]))
        last_id, last, nframes, slow = -1, time.time(), 0, 0.0
        try:
            while self.running:
                if grab.id == last_id:
                    if time.time() - grab.t > 3:
                        self.error = "The camera stopped sending images."
                        break
                    time.sleep(0.002)
                    continue
                img, last_id, now = grab.frame, grab.id, grab.t
                rot = str(cfg.get("rotate", "0"))
                if rot == "90":
                    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                elif rot == "180":
                    img = cv2.rotate(img, cv2.ROTATE_180)
                elif rot == "270":
                    img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                if cfg["mirror"]:
                    img = cv2.flip(img, 1)
                if cfg.get("brightness") or float(cfg.get("contrast", 1.0)) != 1.0:
                    img = cv2.convertScaleAbs(img, alpha=float(cfg["contrast"]), beta=float(cfg["brightness"]))
                elif img is grab.frame:
                    img = img.copy()
                H, W = img.shape[:2]
                res = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                lm, label = self._pick(res)
                g, pts, fy_n, lock = None, None, 0.0, False
                if lm is not None:
                    raw_pts = np.array([[p.x * W, p.y * H] for p in lm.landmark], np.float32)
                    self.sp = raw_pts if self.sp is None else 0.6 * raw_pts + 0.4 * self.sp
                    pts = self.sp
                    thr = float(cfg["pinch_threshold"])
                    m = analyse(pts)
                    vec = features(pts, label)
                    g = self.store.predict(vec, thr=cfg["knn_threshold"]) or classify_builtin(m, thr, self.gesture)
                    lock = bool(cfg["pinch_lock"]) and near_pinch(m, thr)
                    raw = raw_pts[POINTERS.get(cfg["pointer"], [0, 5, 9, 13, 17])].mean(0) / np.array([W, H], np.float32)
                    self.vec, self.metrics, self.raw_ptr = vec, m, (float(raw[0]), float(raw[1]))
                    for f in (self.fx, self.fy):
                        f.mc, f.beta = float(cfg["min_cutoff"]), float(cfg["beta"])
                    x0, y0, x1, y1 = cfg["region"]
                    nx = float(np.clip((raw[0] - x0) / max(x1 - x0, 1e-3), 0, 1))
                    ny = float(np.clip((raw[1] - y0) / max(y1 - y0, 1e-3), 0, 1))
                    nx, ny = (min(1.0, max(0.0, (v - 0.03) / 0.94)) for v in (nx, ny))  # screen edges/corners easy to reach
                    gx = 0.5 + (nx - 0.5) * cfg["gain"]
                    gy = 0.5 + (ny - 0.5) * cfg["gain"]
                    fxn, fy_n = self.fx(gx, now), self.fy(gy, now)
                    self._stabilise(float(np.clip(fxn, 0, 1)) * (self.sw - 1), float(np.clip(fy_n, 0, 1)) * (self.sh - 1))
                else:
                    self.vec = self.metrics = self.raw_ptr = None
                    self.sp = self.cur = None
                    self.fx.reset()
                    self.fy.reset()
                self.gesture = g
                sg = self._stable(g)
                rev = {gn: a for a, gn in cfg["bindings"].items() if gn}
                self._apply(rev.get(sg), self.cur is not None, fy_n, lock)

                if cfg["show_overlay"]:
                    x0, y0, x1, y1 = cfg["region"]
                    cv2.rectangle(img, (int(x0 * W), int(y0 * H)), (int(x1 * W), int(y1 * H)), (255, 160, 0), 1)
                    if pts is not None:
                        for a, b in conns:
                            cv2.line(img, ip(pts[a]), ip(pts[b]), (80, 220, 80), 2)
                        for p in pts:
                            cv2.circle(img, ip(p), 3, (0, 0, 255), -1)
                        if self.raw_ptr:
                            cv2.circle(img, (int(self.raw_ptr[0] * W), int(self.raw_ptr[1] * H)), 8, (255, 200, 0), 2)
                    state = "PAUSED" if self.paused else ("FROZEN" if self.frozen else ("LOCK" if lock else "ACTIVE"))
                    txt = "%s | %s > %s | %d fps" % (state, sg or "-", self.action or "-", self.fps)
                    cv2.putText(img, txt, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3)
                    cv2.putText(img, txt, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
                self.frame, self.frame_id = img, self.frame_id + 1
                t = time.time()
                dt = max(t - last, 1e-3)
                self.fps = 0.9 * self.fps + 0.1 / dt
                last = t
                nframes += 1
                if cx == 1 and cfg.get("auto_perf", True) and nframes > 90:   # PC too slow -> fall back to fast model
                    slow = slow + dt if self.fps < 16 else 0.0
                    if slow > 4:
                        cx, slow = 0, 0.0
                        hands.close()
                        hands = self._make_hands(0)
                        self._log("Switched to fast model for speed")
        except Exception as e:  # keep the UI informed instead of dying silently
            self.error = "Tracking error: %s" % e
        finally:
            self._release()
            grab.alive = False
            time.sleep(0.05)
            cap.release()
            hands.close()
'''

# ---------------------------------------------------------------- ui.py
FILES["app/ui.py"] = r'''import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import cv2
from PIL import Image, ImageDraw, ImageTk

from . import config as C
from .engine import Engine
from .gestures import GestureStore

THEMES = {
    "Midnight Blue": dict(mode="dark", bg="#0f1420", card="#182033", card2="#232d47", accent="#4f8cff", hover="#3a73e0", text="#e8ecf5", sub="#8d98b3"),
    "Neon Violet": dict(mode="dark", bg="#110f1c", card="#1b1830", card2="#2a2548", accent="#8b5cf6", hover="#7443e6", text="#ece8f8", sub="#9a93b8"),
    "Emerald": dict(mode="dark", bg="#0c1512", card="#14231e", card2="#1f362e", accent="#10b981", hover="#0b9468", text="#e6f4ee", sub="#8aa89b"),
    "Sunset": dict(mode="dark", bg="#1a1210", card="#281c18", card2="#3a2822", accent="#f97316", hover="#dc5f0a", text="#f6ece6", sub="#b39a8d"),
    "Cyber Pink": dict(mode="dark", bg="#150d17", card="#231528", card2="#341f3b", accent="#ec4899", hover="#d02f80", text="#f6e8f3", sub="#b393ab"),
    "OLED Black": dict(mode="dark", bg="#000000", card="#101114", card2="#1c1e24", accent="#38bdf8", hover="#1ea4e0", text="#f1f5f9", sub="#8b95a5"),
    "Clean Light": dict(mode="light", bg="#eef1f7", card="#ffffff", card2="#e3e8f2", accent="#2563eb", hover="#1d4fc4", text="#18202f", sub="#667289"),
    "Mint Light": dict(mode="light", bg="#eef6f2", card="#ffffff", card2="#dfeee7", accent="#059669", hover="#047857", text="#14261f", sub="#5f7a6e"),
}

SPEC = [
    ("Camera", [
        ("camera_index", "Camera number", "int", None, "Which webcam to use (0 = first). Use the Camera button to preview and pick."),
        ("camera_url", "Phone / network camera URL", "entry", None, "Optional, e.g. http://192.168.1.5:8080/video (IP Webcam / DroidCam). Leave empty for a normal webcam."),
        ("resolution", "Capture resolution", "choice", ["320x240", "640x480", "1280x720"], "Lower = faster on slow PCs. 640x480 is a good balance."),
        ("mirror", "Mirror image", "bool", None, "Feels natural, like a mirror. Turn off if left/right feels reversed."),
        ("rotate", "Rotate image (degrees)", "choice", ["0", "90", "180", "270"], "Use if your camera is mounted sideways or upside down."),
        ("brightness", "Brightness boost", "float", (-60.0, 80.0), "Raise this in dark rooms so the hand is detected better."),
        ("contrast", "Contrast", "float", (0.5, 2.0), "1.0 = normal."),
    ]),
    ("Tracking", [
        ("hand", "Tracked hand", "choice", ["Any", "Right", "Left"], "Choose your dominant hand to ignore the other one."),
        ("model_complexity", "Accuracy mode", "choice_int", ["0", "1"], "1 = most accurate (default), 0 = fastest. The app falls back to 0 automatically on slow PCs."),
        ("auto_perf", "Auto fall back to fast model", "bool", None, "Switches to the fast model if the frame rate stays low."),
        ("det_conf", "Detection confidence", "float", (0.3, 0.95), "Higher = fewer false detections, but may lose your hand more."),
        ("track_conf", "Tracking confidence", "float", (0.3, 0.95), "Higher = steadier, lower = keeps tracking in poor light."),
        ("show_overlay", "Draw hand skeleton and status", "bool", None, "Shows the green hand lines and the active-area box on the video."),
    ]),
    ("Cursor", [
        ("pointer", "Pointer point", "choice", ["palm", "index_base", "index_tip"], "Which part of the hand moves the cursor. Palm is the steadiest."),
        ("min_cutoff", "Smoothing (lower = smoother)", "float", (0.2, 5.0), "If the cursor shakes, lower this."),
        ("beta", "Responsiveness", "float", (0.0, 30.0), "Higher = less lag on fast moves."),
        ("gain", "Sensitivity", "float", (0.6, 2.0), "How far the cursor travels for each hand movement."),
        ("deadzone", "Jitter filter (pixels)", "float", (0.0, 10.0), "Tiny hand tremors smaller than this are ignored. Raise for rock-steady pointing, lower for ultra-fine movement."),
        ("pinch_lock", "Freeze cursor when pinching", "bool", None, "Stops the cursor as your fingers approach each other so clicks hit exactly where you aim."),
        ("drag_grace", "Grab hold tolerance (frames)", "int", None, "A grab is not dropped by a brief gesture flicker (0-15)."),
        ("stable_frames", "Frames to confirm a gesture", "int", None, "Higher = fewer accidental gestures, slightly slower reaction (1-10)."),
        ("click_rewind", "Click anti-drift (frames)", "int", None, "Cursor jumps back this many frames at click time so pinching does not move it (0-10)."),
        ("click_cooldown", "Click cooldown (s)", "float", (0.1, 1.0), "Minimum time between two clicks."),
        ("scroll_speed", "Scroll speed", "float", (10.0, 100.0), ""),
        ("scroll_invert", "Invert scroll direction", "bool", None, ""),
        ("dwell_click", "Dwell click (hold still to click)", "bool", None, "Accessibility: keep the cursor still for a moment to left-click."),
        ("dwell_time", "Dwell time (s)", "float", (0.5, 3.0), ""),
    ]),
    ("Recognition", [
        ("pinch_threshold", "Pinch sensitivity", "float", (0.1, 0.6), "Higher = easier to trigger clicks. Use Calibrate > Pinch for best results."),
        ("knn_threshold", "Custom gesture strictness", "float", (0.2, 1.5), "Lower = must match your trained pose more exactly."),
    ]),
    ("Appearance", [
        ("theme", "Theme", "choice", list(THEMES), "Pick a colour theme."),
        ("popup_on_start", "Show camera popup on launch", "bool", None, ""),
        ("popup_w", "Popup width (px)", "int", None, "160-900"),
        ("popup_alpha", "Popup opacity", "float", (0.3, 1.0), ""),
        ("popup_borderless", "Borderless popup (drag to move)", "bool", None, "Right-click the popup for size / opacity options."),
    ]),
    ("System", [
        ("start_engine", "Start tracking on launch", "bool", None, ""),
        ("start_minimized", "Start minimized in tray", "bool", None, ""),
        ("close_to_tray", "Close button hides to tray", "bool", None, "Turn off to make the X button quit the app."),
        ("autostart", "Run when Windows starts", "bool", None, ""),
        ("hotkey", "Pause / resume hotkey", "entry", None, "Format example: <ctrl>+<alt>+g"),
    ]),
]

HELP_QUICK = (
    "1.  Press  \u25b6 Start tracking.  Sit 50-70 cm from the camera with good light and a plain background.\n\n"
    "2.  Show your OPEN HAND  \u270b  - the cursor follows it.\n\n"
    "3.  Close your hand into a FIST  \u270a  to GRAB (mouse button held). Open your hand to drop.\n\n"
    "4.  Touch thumb + index fingertip to LEFT-CLICK. Thumb + middle = right click, thumb + ring = double click, thumb + pinky = middle click.\n\n"
    "5.  Show two fingers (V sign) and move your hand up / down to SCROLL.\n\n"
    "6.  Show three fingers (or press the hotkey) to PAUSE / RESUME the mouse.\n\n"
    "First time?  Run  Calibrate  in the sidebar so the cursor range matches how far you like to reach, then try the  Practice  board.\n"
    "Everything can be changed: Gestures (remap), Train (record your own gestures), Settings (all options)."
)

HELP_TROUBLE = (
    "Camera is black / will not open\n  - Close apps using the camera (Zoom, Teams, browser tabs), then press Camera and choose another one.\n\n"
    "Hand is not detected\n  - Add light, use a plain background, keep the whole hand in view, raise Brightness in Settings > Camera.\n\n"
    "Cursor shakes\n  - Use the 'Beginner' preset, raise Jitter filter, lower Smoothing, keep pointer = palm and add light.\n\n"
    "Cursor feels slow / laggy\n  - Use 'Fast / gaming' preset, resolution 320x240 or 640x480, Accuracy mode 0.\n\n"
    "Accidental clicks\n  - Run Calibrate > Pinch, raise 'Frames to confirm a gesture', or lower Pinch sensitivity.\n\n"
    "Click lands in the wrong place\n  - Raise 'Click anti-drift'. Make sure the hand is steady when you pinch.\n\n"
    "Cannot reach the screen corners\n  - Run Calibrate (cursor range) or raise Sensitivity.\n\n"
    "Gesture confused with another\n  - Train your own gesture (Train button) and bind it in Gestures.\n\n"
    "Antivirus flags the .exe\n  - PyInstaller programs sometimes get false alarms. Build it yourself or add an exception.\n\n"
    "Settings and trained gestures are stored in  %APPDATA%\\GestureMouse"
)


def make_icon():
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((2, 2, 62, 62), 14, fill=(79, 140, 255, 255))
    dr.ellipse((18, 28, 46, 54), fill="white")
    for x in (18, 26, 34, 42):
        dr.rounded_rectangle((x, 10, x + 6, 34), 3, fill="white")
    return im


def apply_palette(name):
    p = THEMES.get(name) or THEMES["Midnight Blue"]
    th = ctk.ThemeManager.theme

    def S(widget, **kv):
        th.setdefault(widget, {})
        for k, v in kv.items():
            th[widget][k] = [v, v]
    S("CTk", fg_color=p["bg"])
    S("CTkToplevel", fg_color=p["bg"])
    S("CTkFrame", fg_color=p["card"], top_fg_color=p["card2"], border_color=p["card2"])
    S("CTkButton", fg_color=p["accent"], hover_color=p["hover"], border_color=p["accent"], text_color="#ffffff")
    S("CTkLabel", text_color=p["text"])
    S("CTkEntry", fg_color=p["card2"], border_color=p["card2"], text_color=p["text"], placeholder_text_color=p["sub"])
    S("CTkSwitch", fg_color=p["card2"], progress_color=p["accent"], button_color="#ffffff", button_hover_color="#dddddd", text_color=p["text"])
    S("CTkCheckBox", fg_color=p["accent"], border_color=p["sub"], hover_color=p["hover"], checkmark_color="#ffffff", text_color=p["text"])
    S("CTkSlider", fg_color=p["card2"], progress_color=p["accent"], button_color=p["accent"], button_hover_color=p["hover"])
    S("CTkProgressBar", fg_color=p["card2"], progress_color=p["accent"], border_color=p["card2"])
    for w in ("CTkOptionMenu", "CTkComboBox"):
        S(w, fg_color=p["card2"], button_color=p["accent"], button_hover_color=p["hover"], text_color=p["text"],
          dropdown_fg_color=p["card"], dropdown_hover_color=p["card2"], dropdown_text_color=p["text"])
    S("CTkTextbox", fg_color=p["card2"], border_color=p["card2"], text_color=p["text"],
      scrollbar_button_color=p["sub"], scrollbar_button_hover_color=p["accent"])
    S("CTkScrollableFrame", label_fg_color=p["card2"])
    S("CTkScrollbar", button_color=p["sub"], button_hover_color=p["accent"])
    S("DropdownMenu", fg_color=p["card"], hover_color=p["card2"], text_color=p["text"])
    ctk.set_appearance_mode(p["mode"])
    return p


def set_autostart(on):
    if os.name != "nt":
        return
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        if on:
            if getattr(sys, "frozen", False):
                cmd = '"%s"' % sys.executable
            else:
                cmd = '"%s" "%s"' % (sys.executable.replace("python.exe", "pythonw.exe"), os.path.abspath(sys.argv[0]))
            winreg.SetValueEx(key, "GestureMouse", 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, "GestureMouse")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass


def scan_cameras(maxn=6):
    found = []
    for i in range(maxn):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(i)
        ok = False
        if cap.isOpened():
            ok, _ = cap.read()
        cap.release()
        if ok:
            found.append(i)
    return found


class Tip:
    def __init__(self, w, text):
        self.w, self.text, self.tw = w, text, None
        if text:
            w.bind("<Enter>", self.show, add="+")
            w.bind("<Leave>", self.hide, add="+")

    def show(self, e=None):
        if self.tw:
            return
        self.tw = tw = tk.Toplevel(self.w)
        tw.overrideredirect(True)
        tw.attributes("-topmost", True)
        tw.geometry("+%d+%d" % (self.w.winfo_rootx() + 12, self.w.winfo_rooty() + self.w.winfo_height() + 6))
        tk.Label(tw, text=self.text, bg="#111827", fg="#f3f4f6", padx=8, pady=5, justify="left", wraplength=280,
                 font=("Segoe UI", 9)).pack()

    def hide(self, e=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


class Popup(tk.Toplevel):
    """Always-on-top camera window with the tracked hand drawn on it."""

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        c = app.cfg
        self.title("Gesture Mouse - Camera")
        self.configure(bg=app.p["accent"])
        self.overrideredirect(bool(c["popup_borderless"]))
        self.attributes("-topmost", True)
        self.attributes("-alpha", float(c["popup_alpha"]))
        self.geometry("+%d+%d" % (c["popup_x"], c["popup_y"]))
        self.lbl = tk.Label(self, bd=0, bg="black", width=40, height=10, fg="white", text="waiting for camera...")
        self.lbl.pack(padx=2, pady=2)
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Bigger", command=lambda: self._size(1.2))
        self.menu.add_command(label="Smaller", command=lambda: self._size(0.8))
        self.menu.add_command(label="More transparent", command=lambda: self._alpha(-0.1))
        self.menu.add_command(label="Less transparent", command=lambda: self._alpha(0.1))
        self.menu.add_separator()
        self.menu.add_command(label="Close popup", command=app.toggle_popup)
        for w in (self, self.lbl):
            w.bind("<ButtonPress-1>", self._start)
            w.bind("<B1-Motion>", self._move)
            w.bind("<ButtonRelease-1>", lambda e: C.save(self.app.cfg))
            w.bind("<Button-3>", lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self.protocol("WM_DELETE_WINDOW", app.toggle_popup)
        self.ph = None

    def _start(self, e):
        self._ox, self._oy = e.x_root - self.winfo_x(), e.y_root - self.winfo_y()

    def _move(self, e):
        x, y = e.x_root - self._ox, e.y_root - self._oy
        self.geometry("+%d+%d" % (x, y))
        self.app.cfg["popup_x"], self.app.cfg["popup_y"] = x, y

    def _size(self, f):
        self.app.cfg["popup_w"] = int(min(900, max(160, self.app.cfg["popup_w"] * f)))
        C.save(self.app.cfg)

    def _alpha(self, d):
        a = round(min(1.0, max(0.3, float(self.app.cfg["popup_alpha"]) + d)), 2)
        self.app.cfg["popup_alpha"] = a
        self.attributes("-alpha", a)
        C.save(self.app.cfg)

    def update_img(self, img):
        w = int(self.app.cfg["popup_w"])
        h = int(w * img.height / img.width)
        self.ph = ImageTk.PhotoImage(img.resize((w, h)))
        self.lbl.config(image=self.ph, width=w, height=h)
        self.attributes("-alpha", float(self.app.cfg["popup_alpha"]))


class App:
    def __init__(self):
        self.cfg = C.load()
        if self.cfg["theme"] not in THEMES:
            self.cfg["theme"] = "Midnight Blue"
        self.store = GestureStore()
        self.engine = self.tray = self.popup = self.hk = None
        self.q = queue.Queue()
        self.sinks = []
        self.sliders = {}
        self._last_id, self._ev_seen, self._err_shown = -1, -1, False
        self.p = apply_palette(self.cfg["theme"])
        self.root = ctk.CTk()
        self.root.title("Gesture Mouse")
        self.root.geometry("1220x760")
        self.root.minsize(1060, 680)
        try:
            self.root.after(300, lambda: self.root.iconphoto(True, ImageTk.PhotoImage(make_icon())))
        except Exception:
            pass
        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<F1>", lambda e: self.help())
        self._start_hotkey()
        self._tick()
        if self.cfg["start_engine"]:
            self.start()
        if self.cfg["popup_on_start"]:
            self.toggle_popup()
        if self.cfg["start_minimized"]:
            self.root.after(400, self.to_tray)
        elif self.cfg["first_run"]:
            self.root.after(700, self.wizard)

    def run(self):
        self.root.mainloop()

    def post(self, fn):
        self.q.put(fn)

    def font(self, size=13, bold=False):
        return ctk.CTkFont(size=size, weight="bold" if bold else "normal")

    # ------------------------------------------------------------------ main window
    def build_ui(self):
        p, r = self.p, self.root
        for w in r.winfo_children():
            w.destroy()
        self.sliders = {}
        self._ev_seen = -1
        r.configure(fg_color=p["bg"])
        r.grid_columnconfigure(1, weight=1)
        r.grid_rowconfigure(0, weight=1)

        side = ctk.CTkFrame(r, width=230, corner_radius=0, fg_color=p["card"])
        side.grid(row=0, column=0, sticky="nsew")
        side.pack_propagate(False)
        ctk.CTkLabel(side, text="\u270b Gesture Mouse", font=self.font(21, True)).pack(anchor="w", padx=18, pady=(18, 0))
        ctk.CTkLabel(side, text="Control your PC with your hand", text_color=p["sub"], font=self.font(11)).pack(anchor="w", padx=18, pady=(0, 14))
        self.btn_start = ctk.CTkButton(side, text="\u25b6  Start tracking", height=44, font=self.font(14, True), command=self.toggle_run)
        self.btn_start.pack(fill="x", padx=16, pady=(0, 8))
        Tip(self.btn_start, "Turns the camera and hand tracking on or off.")
        self.btn_pause = ctk.CTkButton(side, text="\u23f8  Pause mouse", height=36, fg_color=p["card2"], hover_color=p["bg"],
                                       text_color=p["text"], command=self.toggle_pause)
        self.btn_pause.pack(fill="x", padx=16)
        Tip(self.btn_pause, "Stops the hand from controlling the mouse without turning off the camera. Hotkey: " + self.cfg["hotkey"])
        ctk.CTkLabel(side, text="CAMERA", text_color=p["sub"], font=self.font(10, True)).pack(anchor="w", padx=18, pady=(18, 2))
        row = ctk.CTkFrame(side, fg_color="transparent")
        row.pack(fill="x", padx=16)
        self.cam_menu = ctk.CTkOptionMenu(row, values=self.cam_values(), command=self.pick_camera, width=150)
        self.cam_menu.set(self.cam_current())
        self.cam_menu.pack(side="left")
        b = ctk.CTkButton(row, text="\u2699", width=36, fg_color=p["card2"], hover_color=p["bg"], text_color=p["text"], command=self.camera_dialog)
        b.pack(side="left", padx=(6, 0))
        Tip(b, "Preview and choose your camera (also phone / network cameras).")
        ctk.CTkLabel(side, text="MENU", text_color=p["sub"], font=self.font(10, True)).pack(anchor="w", padx=18, pady=(18, 2))
        for text, cmd, tip in (
                ("\u270b  Gestures", self.open_bindings, "Choose which gesture does which mouse action."),
                ("\u270e  Train gestures", self.open_train, "Record your own hand poses."),
                ("\u25ce  Calibrate", self.calibrate_menu, "Fit the cursor range and pinch to your hand (recommended)."),
                ("\u25a3  Practice board", self.practice, "Safe area to try clicking, dragging and scrolling."),
                ("\u2699  Settings", self.open_settings, "All options."),
                ("?  Help  (F1)", self.help, "Quick start, gesture guide, troubleshooting.")):
            bt = ctk.CTkButton(side, text=text, anchor="w", height=34, fg_color="transparent", hover_color=p["card2"],
                               text_color=p["text"], command=cmd)
            bt.pack(fill="x", padx=10, pady=1)
            Tip(bt, tip)
        bottom = ctk.CTkFrame(side, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=10, pady=12)
        for text, cmd in (("\u25bc  Minimize to tray", self.to_tray), ("\u25ad  Camera popup (on top)", self.toggle_popup)):
            ctk.CTkButton(bottom, text=text, anchor="w", height=32, fg_color=p["card2"], hover_color=p["bg"],
                          text_color=p["text"], command=cmd).pack(fill="x", pady=2)

        center = ctk.CTkFrame(r, fg_color="transparent")
        center.grid(row=0, column=1, sticky="nsew", padx=14, pady=14)
        center.grid_rowconfigure(0, weight=1)
        center.grid_columnconfigure(0, weight=1)
        self.pv = ctk.CTkFrame(center, corner_radius=16, fg_color=p["card"])
        self.pv.grid(row=0, column=0, sticky="nsew")
        self.preview = tk.Label(self.pv, bg=p["card"], fg=p["sub"], font=("Segoe UI", 13), bd=0,
                                text="Camera is off\n\nPress  \u25b6 Start tracking  to begin")
        self.preview.place(relx=0.5, rely=0.5, anchor="center")
        chips = ctk.CTkFrame(center, fg_color="transparent")
        chips.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.v_state, self.v_g, self.v_a, self.v_fps = (tk.StringVar(value="-") for _ in range(4))
        for i, (t, v) in enumerate((("STATE", self.v_state), ("GESTURE", self.v_g), ("ACTION", self.v_a), ("FPS", self.v_fps))):
            chips.grid_columnconfigure(i, weight=1)
            f = ctk.CTkFrame(chips, corner_radius=12)
            f.grid(row=0, column=i, sticky="ew", padx=4)
            ctk.CTkLabel(f, text=t, text_color=p["sub"], font=self.font(10, True)).pack(anchor="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(f, textvariable=v, font=self.font(15, True)).pack(anchor="w", padx=12, pady=(0, 8))
        self.hint = ctk.CTkLabel(center, text=self.hint_text(), text_color=p["sub"], wraplength=640, justify="left")
        self.hint.grid(row=2, column=0, sticky="w", padx=6, pady=(10, 0))

        right = ctk.CTkScrollableFrame(r, width=270, corner_radius=0, fg_color=p["card"])
        right.grid(row=0, column=2, sticky="nsew")
        ctk.CTkLabel(right, text="Quick tuning", font=self.font(16, True)).pack(anchor="w", pady=(6, 4))
        ctk.CTkLabel(right, text="Preset", text_color=p["sub"]).pack(anchor="w")
        pm = ctk.CTkOptionMenu(right, values=list(C.PRESETS), command=self.set_preset)
        pm.set(self.cfg["preset"] if self.cfg["preset"] in C.PRESETS else "Balanced")
        pm.pack(fill="x", pady=(0, 6))
        Tip(pm, "Ready-made smoothness / speed combinations.")
        ctk.CTkLabel(right, text="Theme", text_color=p["sub"]).pack(anchor="w")
        tm = ctk.CTkOptionMenu(right, values=list(THEMES), command=self.set_theme)
        tm.set(self.cfg["theme"])
        tm.pack(fill="x", pady=(0, 8))
        for text, key, lo, hi, tip in (
                ("Smoothing", "min_cutoff", 0.2, 5.0, "Lower = smoother but slower cursor. Raise if it feels sluggish."),
                ("Responsiveness", "beta", 0.0, 30.0, "Higher = less lag when moving fast."),
                ("Sensitivity", "gain", 0.6, 2.0, "How far the cursor moves for a given hand movement."),
                ("Jitter filter (px)", "deadzone", 0.0, 10.0, "Ignores tiny hand tremors. Higher = steadier pointer."),
                ("Pinch sensitivity", "pinch_threshold", 0.1, 0.6, "Higher = clicks trigger more easily."),
                ("Scroll speed", "scroll_speed", 10.0, 100.0, "")):
            self.qslider(right, text, key, lo, hi, tip)
        self.qswitch(right, "Mirror camera", "mirror", "Natural mirror view.")
        self.qswitch(right, "Dwell click", "dwell_click", "Hold the cursor still to left-click (no pinch needed).")
        self.qswitch(right, "Draw hand overlay", "show_overlay", "Green hand skeleton on the video.")
        ctk.CTkLabel(right, text="Activity", font=self.font(16, True)).pack(anchor="w", pady=(14, 4))
        self.log = ctk.CTkTextbox(right, height=170, state="disabled", wrap="none")
        self.log.pack(fill="x")

    def hint_text(self):
        b, parts = self.cfg["bindings"], []
        for a, name in (("move", "Move"), ("drag", "Grab"), ("left_click", "Click"), ("right_click", "Right-click"),
                        ("scroll", "Scroll"), ("pause", "Pause")):
            g = b.get(a)
            if g:
                parts.append("%s \u2192 %s" % (C.SHORT.get(g, g), name))
        return "   \u2022   ".join(parts) if parts else "Open Gestures to choose your controls."

    def qslider(self, parent, text, key, lo, hi, tip):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(4, 0))
        lab = ctk.CTkLabel(row, text=text, anchor="w")
        lab.pack(side="left")
        val = ctk.CTkLabel(row, text="%.2f" % self.cfg[key], text_color=self.p["sub"])
        val.pack(side="right")
        s = ctk.CTkSlider(parent, from_=lo, to=hi, command=lambda x, k=key, v=val: (self.cfg.__setitem__(k, round(float(x), 3)), v.configure(text="%.2f" % float(x))))
        s.set(self.cfg[key])
        s.pack(fill="x", pady=(0, 4))
        s.bind("<ButtonRelease-1>", lambda e: C.save(self.cfg))
        self.sliders[key] = (s, val)
        Tip(lab, tip)

    def qswitch(self, parent, text, key, tip):
        var = tk.IntVar(value=int(bool(self.cfg[key])))

        def ch():
            self.cfg[key] = bool(var.get())
            C.save(self.cfg)
        sw = ctk.CTkSwitch(parent, text=text, variable=var, command=ch)
        sw.var = var
        sw.pack(anchor="w", pady=5)
        Tip(sw, tip)

    def set_preset(self, name):
        for k, v in C.PRESETS[name].items():
            self.cfg[k] = v
            if k in self.sliders:
                s, l = self.sliders[k]
                s.set(v)
                l.configure(text="%.2f" % v)
        self.cfg["preset"] = name
        C.save(self.cfg)

    def set_theme(self, name):
        self.cfg["theme"] = name
        C.save(self.cfg)
        self.p = apply_palette(name)
        was_popup = self.popup is not None
        if was_popup:
            self.toggle_popup()
        self.build_ui()
        self._last_id = -1
        if self.engine and self.engine.is_alive():
            self.btn_start.configure(text="\u25a0  Stop tracking")
        if was_popup:
            self.toggle_popup()

    # ------------------------------------------------------------------ helpers
    def dialog(self, title, w, h):
        d = ctk.CTkToplevel(self.root)
        d.title(title)
        d.geometry("%dx%d" % (w, h))
        d.configure(fg_color=self.p["bg"])

        def front():
            try:
                if d.winfo_exists():
                    d.lift()
                    d.focus_force()
            except Exception:
                pass
        d.after(200, front)
        return d

    def freeze(self, d):
        if self.engine:
            self.engine.frozen = True

        def un(e):
            if e.widget is d and self.engine:
                self.engine.frozen = False
        d.bind("<Destroy>", un, add="+")

    def need_engine(self):
        if not (self.engine and self.engine.is_alive()):
            messagebox.showinfo("Gesture Mouse", "Start tracking first - the camera must be running.")
            return False
        return True

    def mini_preview(self, parent, w=380):
        lab = tk.Label(parent, bg=self.p["card"], bd=0, fg=self.p["sub"], text="(start tracking to see the camera)")

        def sink(img):
            h = int(w * img.height / img.width)
            ph = ImageTk.PhotoImage(img.resize((w, h)))
            lab.config(image=ph, text="")
            lab.image = ph
        self.sinks.append(sink)
        lab.bind("<Destroy>", lambda e: self.sinks.remove(sink) if sink in self.sinks else None)
        return lab

    def tabbed(self, d, names, scroll=True):
        nav = ctk.CTkFrame(d, width=170, corner_radius=0, fg_color=self.p["card"])
        nav.pack(side="left", fill="y")
        body = ctk.CTkFrame(d, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=14, pady=12)
        bar = ctk.CTkFrame(body, fg_color="transparent")
        bar.pack(side="bottom", fill="x", pady=(8, 0))
        holder = ctk.CTkFrame(body, fg_color="transparent")
        holder.pack(side="top", fill="both", expand=True)
        frames, btns = {}, {}

        def show(n):
            for f in frames.values():
                f.pack_forget()
            frames[n].pack(fill="both", expand=True)
            for k, b in btns.items():
                b.configure(fg_color=self.p["accent"] if k == n else "transparent")
        for n in names:
            frames[n] = (ctk.CTkScrollableFrame if scroll else ctk.CTkFrame)(holder, fg_color="transparent")
            btns[n] = ctk.CTkButton(nav, text=n, anchor="w", height=34, fg_color="transparent", hover_color=self.p["card2"],
                                    text_color=self.p["text"], command=lambda n=n: show(n))
            btns[n].pack(fill="x", padx=8, pady=2)
        show(names[0])
        return frames, bar, show

    # ------------------------------------------------------------------ engine control
    def start(self):
        if self.engine and self.engine.is_alive():
            return
        self._err_shown = False
        self.engine = Engine(self.cfg, self.store)
        self.engine.start()
        self.btn_start.configure(text="\u25a0  Stop tracking")

    def stop(self):
        e, self.engine = self.engine, None
        if e:
            e.running = False
            e.join(timeout=2)
        try:
            self.btn_start.configure(text="\u25b6  Start tracking")
            self.preview.config(image="", text="Camera is off\n\nPress  \u25b6 Start tracking  to begin")
            self.preview.image = None
            for v in (self.v_state, self.v_g, self.v_a, self.v_fps):
                v.set("-")
        except Exception:
            pass

    def toggle_run(self):
        self.stop() if (self.engine and self.engine.is_alive()) else self.start()

    def toggle_pause(self):
        if self.engine:
            self.engine.paused = not self.engine.paused

    def restart_if_running(self):
        if self.engine and self.engine.is_alive():
            self.stop()
            self.start()

    def _tick(self):
        try:
            while True:
                self.q.get_nowait()()
        except queue.Empty:
            pass
        except Exception:
            pass
        e = self.engine
        try:
            if e:
                if e.is_alive():
                    if e.frame is not None and e.frame_id != self._last_id:
                        self._last_id = e.frame_id
                        img = Image.fromarray(cv2.cvtColor(e.frame, cv2.COLOR_BGR2RGB))
                        if self.root.state() != "withdrawn":
                            w, h = max(self.pv.winfo_width() - 16, 320), max(self.pv.winfo_height() - 16, 240)
                            sc = min(w / img.width, h / img.height)
                            ph = ImageTk.PhotoImage(img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc)))))
                            self.preview.config(image=ph, text="")
                            self.preview.image = ph
                        if self.popup:
                            self.popup.update_img(img)
                        for s in list(self.sinks):
                            try:
                                s(img)
                            except Exception:
                                pass
                    self.v_state.set("PAUSED" if e.paused else ("CALIBRATING" if e.frozen else "ACTIVE"))
                    self.v_g.set(C.SHORT.get(e.stable, e.stable) if e.stable else "-")
                    self.v_a.set(C.ACTIONS.get(e.action, "-").split(" (")[0] if e.action else "-")
                    self.v_fps.set("%d" % e.fps)
                    self.btn_pause.configure(text="\u25b6  Resume mouse" if e.paused else "\u23f8  Pause mouse")
                    if e.ev_count != self._ev_seen:
                        self._ev_seen = e.ev_count
                        self.log.configure(state="normal")
                        self.log.delete("1.0", "end")
                        for t, txt in list(e.events)[::-1][:12]:
                            self.log.insert("end", "%s  %s\n" % (t, txt))
                        self.log.configure(state="disabled")
                elif e.error and not self._err_shown:
                    self._err_shown = True
                    err = e.error
                    self.stop()
                    messagebox.showerror("Gesture Mouse", err + "\n\nTip: open the Camera dialog (gear icon in the sidebar) and pick another camera.")
        except Exception:
            pass
        self.root.after(30, self._tick)

    # ------------------------------------------------------------------ tray / popup / hotkey
    def to_tray(self):
        try:
            import pystray
        except Exception:
            self.root.iconify()
            return
        self.root.withdraw()
        if self.tray:
            return
        mi = pystray.MenuItem
        menu = pystray.Menu(
            mi("Show window", lambda i, it: self.post(self.from_tray), default=True),
            mi("Pause / resume mouse", lambda i, it: self.post(self.toggle_pause)),
            mi("Start / stop tracking", lambda i, it: self.post(self.toggle_run)),
            mi("Camera popup", lambda i, it: self.post(self.toggle_popup)),
            mi("Exit", lambda i, it: self.post(self.quit)),
        )
        self.tray = pystray.Icon("GestureMouse", make_icon(), "Gesture Mouse", menu)
        self.tray.run_detached()

    def from_tray(self):
        self.root.deiconify()
        self.root.lift()
        if self.tray:
            self.tray.stop()
            self.tray = None

    def toggle_popup(self):
        if self.popup:
            C.save(self.cfg)
            self.popup.destroy()
            self.popup = None
        else:
            self.popup = Popup(self)

    def _start_hotkey(self):
        if self.hk:
            try:
                self.hk.stop()
            except Exception:
                pass
            self.hk = None
        try:
            from pynput import keyboard
            self.hk = keyboard.GlobalHotKeys({self.cfg["hotkey"]: lambda: self.post(self.toggle_pause)})
            self.hk.start()
        except Exception:
            self.hk = None

    def on_close(self):
        self.to_tray() if self.cfg["close_to_tray"] else self.quit()

    def quit(self):
        C.save(self.cfg)
        self.stop()
        for o in (self.hk, self.tray):
            try:
                o.stop()
            except Exception:
                pass
        self.root.destroy()

    # ------------------------------------------------------------------ camera
    def cam_values(self):
        n = max(4, int(self.cfg["camera_index"]) + 1)
        return ["Camera %d" % i for i in range(n)] + ["Network camera"]

    def cam_current(self):
        return "Network camera" if self.cfg["camera_url"].strip() else "Camera %d" % int(self.cfg["camera_index"])

    def pick_camera(self, v):
        if v == "Network camera":
            if not self.cfg["camera_url"].strip():
                self.cam_menu.set(self.cam_current())
                self.camera_dialog()
                return
        else:
            self.cfg["camera_index"] = int(v.split()[-1])
            self.cfg["camera_url"] = ""
        C.save(self.cfg)
        self.restart_if_running()

    def camera_dialog(self):
        was = bool(self.engine and self.engine.is_alive())
        self.stop()
        p = self.p
        d = self.dialog("Choose camera", 640, 700)
        st = {"cap": None, "idx": None, "url": ""}
        ctk.CTkLabel(d, text="Choose your camera", font=self.font(20, True)).pack(pady=(16, 0))
        info = ctk.CTkLabel(d, text="Scanning for cameras...", text_color=p["sub"])
        info.pack()
        pv = tk.Label(d, bg=p["card"], bd=0, width=60, height=18, fg=p["sub"], text="no preview")
        pv.pack(pady=10)
        row = ctk.CTkFrame(d, fg_color="transparent")
        row.pack(pady=4)
        menu = ctk.CTkOptionMenu(row, values=["..."], width=190, command=lambda v: open_cam(int(v.split()[-1])))
        menu.pack(side="left", padx=4)
        ctk.CTkButton(row, text="Rescan", width=90, command=lambda: scan()).pack(side="left", padx=4)
        ctk.CTkLabel(d, text="Phone / network camera URL (optional)", text_color=p["sub"]).pack(pady=(14, 2))
        urow = ctk.CTkFrame(d, fg_color="transparent")
        urow.pack()
        url = ctk.CTkEntry(urow, width=360, placeholder_text="http://192.168.1.5:8080/video")
        url.pack(side="left", padx=4)
        if self.cfg["camera_url"]:
            url.insert(0, self.cfg["camera_url"])
        ctk.CTkButton(urow, text="Test URL", width=90, command=lambda: open_url()).pack(side="left", padx=4)
        ctk.CTkLabel(d, text="Tip: apps like DroidCam or IP Webcam turn your phone into a camera.", text_color=p["sub"], font=self.font(11)).pack(pady=4)

        def release():
            if st["cap"] is not None:
                st["cap"].release()
                st["cap"] = None

        def open_cam(i):
            release()
            st["idx"], st["url"] = i, ""
            st["cap"] = cv2.VideoCapture(i, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(i)

        def open_url():
            release()
            u = url.get().strip()
            if u:
                st["url"], st["idx"] = u, None
                st["cap"] = cv2.VideoCapture(u)

        def loop():
            try:
                if not d.winfo_exists():
                    return
            except Exception:
                return
            cap = st["cap"]
            if cap is not None and cap.isOpened():
                ok, fr = cap.read()
                if ok:
                    if self.cfg["mirror"]:
                        fr = cv2.flip(fr, 1)
                    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
                    im = im.resize((480, int(480 * im.height / im.width)))
                    ph = ImageTk.PhotoImage(im)
                    pv.config(image=ph, text="")
                    pv.image = ph
            d.after(40, loop)

        def scan():
            release()
            info.configure(text="Scanning for cameras...")

            def work():
                found = scan_cameras()
                self.post(lambda: done(found))
            threading.Thread(target=work, daemon=True).start()

        def done(found):
            try:
                if not d.winfo_exists():
                    return
            except Exception:
                return
            if found:
                vals = ["Camera %d" % i for i in found]
                menu.configure(values=vals)
                cur = int(self.cfg["camera_index"])
                pick = cur if cur in found else found[0]
                menu.set("Camera %d" % pick)
                open_cam(pick)
                info.configure(text="Found %d camera(s). Pick one - the preview updates live." % len(found))
            else:
                info.configure(text="No camera found. Plug it in, close other apps using it, or use a network URL.")

        def use():
            if st["url"]:
                self.cfg["camera_url"] = st["url"]
            elif st["idx"] is not None:
                self.cfg["camera_index"], self.cfg["camera_url"] = st["idx"], ""
            else:
                d.destroy()
                return
            C.save(self.cfg)
            d.destroy()

        def closed(e):
            if e.widget is d:
                release()
                try:
                    self.cam_menu.configure(values=self.cam_values())
                    self.cam_menu.set(self.cam_current())
                except Exception:
                    pass
                if was:
                    self.start()
        ctk.CTkButton(d, text="Use this camera", height=40, font=self.font(14, True), command=use).pack(pady=16)
        d.bind("<Destroy>", closed, add="+")
        loop()
        scan()

    # ------------------------------------------------------------------ settings
    def open_settings(self):
        d = self.dialog("Settings", 780, 640)
        frames, bar, show = self.tabbed(d, [n for n, _ in SPEC])
        vars_ = {}
        for tab, items in SPEC:
            f = frames[tab]
            for key, label, kind, arg, hint in items:
                row = ctk.CTkFrame(f, fg_color="transparent")
                row.pack(fill="x", pady=(8, 0))
                ctk.CTkLabel(row, text=label, anchor="w", width=250, justify="left").pack(side="left")
                val = self.cfg[key]
                if kind == "bool":
                    v = tk.IntVar(value=int(bool(val)))
                    ctk.CTkSwitch(row, text="", variable=v, width=50).pack(side="right")
                elif kind == "float":
                    v = tk.DoubleVar(value=float(val))
                    lab = ctk.CTkLabel(row, text="%.2f" % float(val), width=44, text_color=self.p["sub"])
                    lab.pack(side="right")
                    ctk.CTkSlider(row, from_=arg[0], to=arg[1], variable=v, width=190,
                                  command=lambda x, l=lab: l.configure(text="%.2f" % float(x))).pack(side="right", padx=6)
                elif kind in ("choice", "choice_int"):
                    v = tk.StringVar(value=str(val))
                    ctk.CTkOptionMenu(row, values=[str(a) for a in arg], variable=v, width=200).pack(side="right")
                else:
                    v = tk.StringVar(value=str(val))
                    ctk.CTkEntry(row, textvariable=v, width=200 if kind == "entry" else 90).pack(side="right")
                vars_[key] = (v, kind)
                if hint:
                    ctk.CTkLabel(f, text=hint, text_color=self.p["sub"], font=self.font(11), anchor="w", justify="left", wraplength=470).pack(anchor="w")
        sysf = frames["System"]
        ctk.CTkLabel(sysf, text="Backup", font=self.font(14, True)).pack(anchor="w", pady=(18, 4))
        brow = ctk.CTkFrame(sysf, fg_color="transparent")
        brow.pack(anchor="w")
        ctk.CTkButton(brow, text="Export settings + gestures", command=self.export_all).pack(side="left", padx=(0, 8))
        ctk.CTkButton(brow, text="Import", width=90, command=self.import_all).pack(side="left")
        ctk.CTkButton(sysf, text="Reset everything to defaults", fg_color=self.p["card2"], text_color=self.p["text"],
                      hover_color=self.p["bg"], command=self.reset_all).pack(anchor="w", pady=10)

        def apply():
            old = self.cfg["theme"]
            for key, (v, kind) in vars_.items():
                try:
                    x = v.get()
                    if kind == "int":
                        x = int(float(x))
                    elif kind == "choice_int":
                        x = int(x)
                    elif kind == "float":
                        x = round(float(x), 3)
                    elif kind == "bool":
                        x = bool(x)
                    self.cfg[key] = x
                except Exception:
                    pass
            self.cfg["popup_w"] = min(900, max(160, int(self.cfg["popup_w"])))
            C.save(self.cfg)
            set_autostart(self.cfg["autostart"])
            self._start_hotkey()
            if self.cfg["theme"] != old:
                self.set_theme(self.cfg["theme"])
                return
            self.restart_if_running()
            if self.popup:
                self.popup.overrideredirect(bool(self.cfg["popup_borderless"]))
            d.destroy()
        ctk.CTkButton(bar, text="Save", width=110, command=apply).pack(side="right", padx=3)
        ctk.CTkButton(bar, text="Cancel", width=90, fg_color=self.p["card2"], text_color=self.p["text"], hover_color=self.p["bg"],
                      command=d.destroy).pack(side="right", padx=3)

    def export_all(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="gesture_mouse_backup.json")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"settings": self.cfg, "gestures": self.store.data}, f, indent=2)
            messagebox.showinfo("Export", "Saved to " + path)

    def import_all(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.cfg.update(data.get("settings", {}))
            self.store.data = data.get("gestures", {})
            self.store.save()
            C.save(self.cfg)
            self.set_theme(self.cfg["theme"] if self.cfg["theme"] in THEMES else "Midnight Blue")
            messagebox.showinfo("Import", "Imported.")
        except Exception as ex:
            messagebox.showerror("Import", "Could not import: %s" % ex)

    def reset_all(self):
        if messagebox.askyesno("Reset", "Reset ALL settings and gesture bindings to defaults? (Trained gestures are kept.)"):
            import copy
            self.cfg.clear()
            self.cfg.update(copy.deepcopy(C.DEFAULTS))
            C.save(self.cfg)
            self.set_theme(self.cfg["theme"])
            self.restart_if_running()

    # ------------------------------------------------------------------ gestures
    def glabel(self, g):
        if g in C.BUILTIN:
            return "%s %s" % (C.EMOJI.get(g, "\u2605"), C.BUILTIN[g])
        return "\u2605 %s (custom)" % g

    def open_bindings(self):
        d = self.dialog("Gesture controls", 640, 700)
        names = ["(none)"] + list(C.BUILTIN) + sorted(self.store.data)
        labels = {self.glabel(n) if n != "(none)" else "(none)": n for n in names}
        ctk.CTkLabel(d, text="Gesture controls", font=self.font(20, True)).pack(anchor="w", padx=22, pady=(16, 0))
        ctk.CTkLabel(d, text="Pick which hand gesture triggers each mouse action. Record your own in 'Train gestures'.",
                     text_color=self.p["sub"], wraplength=580, justify="left").pack(anchor="w", padx=22, pady=(0, 8))
        f = ctk.CTkScrollableFrame(d, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=14)
        vars_ = {}
        inv = {v: k for k, v in labels.items()}
        for a, lbl in C.ACTIONS.items():
            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=lbl, anchor="w", width=210).pack(side="left")
            v = tk.StringVar(value=inv.get(self.cfg["bindings"].get(a) or "(none)", "(none)"))
            ctk.CTkOptionMenu(row, values=list(labels), variable=v, width=300).pack(side="right")
            vars_[a] = v

        def save():
            chosen = {a: (labels.get(v.get()) if labels.get(v.get()) != "(none)" else None) for a, v in vars_.items()}
            used = [g for g in chosen.values() if g]
            if len(used) != len(set(used)) and not messagebox.askyesno("Same gesture used twice", "One gesture is bound to more than one action - only one will work. Continue?"):
                return
            self.cfg["bindings"] = chosen
            C.save(self.cfg)
            self.hint.configure(text=self.hint_text())
            d.destroy()

        def reset():
            for a, v in vars_.items():
                v.set(inv.get(C.DEFAULT_BINDINGS.get(a) or "(none)", "(none)"))
        bar = ctk.CTkFrame(d, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=14)
        ctk.CTkButton(bar, text="Save", width=110, command=save).pack(side="right", padx=3)
        ctk.CTkButton(bar, text="Back to defaults", width=130, fg_color=self.p["card2"], text_color=self.p["text"], hover_color=self.p["bg"], command=reset).pack(side="right", padx=3)

    def open_train(self):
        if not self.need_engine():
            return
        p = self.p
        d = self.dialog("Train custom gestures", 760, 600)
        self.freeze(d)
        left = ctk.CTkFrame(d, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=16, pady=16)
        right = ctk.CTkFrame(d, width=300, fg_color=p["card"])
        right.pack(side="right", fill="y", padx=(0, 16), pady=16)
        right.pack_propagate(False)
        ctk.CTkLabel(left, text="Train a custom gesture", font=self.font(20, True)).pack(anchor="w")
        ctk.CTkLabel(left, text="1. Type a name   2. Press Record   3. Hold the pose and slowly tilt/rotate your hand a little.\n"
                     "Then bind it to a mouse action in 'Gestures'.", text_color=p["sub"], justify="left", wraplength=400).pack(anchor="w", pady=6)
        self.mini_preview(left, 400).pack(pady=6)
        name = ctk.CTkEntry(left, placeholder_text="gesture name, e.g. thumbs_up")
        name.pack(fill="x", pady=4)
        msg = ctk.CTkLabel(left, text="", font=self.font(14, True))
        msg.pack(pady=4)
        bar = ctk.CTkProgressBar(left)
        bar.set(0)
        bar.pack(fill="x", pady=4)
        live = ctk.CTkLabel(left, text="", text_color=p["sub"])
        live.pack()
        ctk.CTkLabel(right, text="Your gestures", font=self.font(15, True)).pack(anchor="w", padx=14, pady=(14, 4))
        lst = ctk.CTkScrollableFrame(right, fg_color="transparent")
        lst.pack(fill="both", expand=True, padx=6, pady=6)

        def refresh():
            for w in lst.winfo_children():
                w.destroy()
            for n, v in self.store.data.items():
                r = ctk.CTkFrame(lst, fg_color="transparent")
                r.pack(fill="x", pady=2)
                ctk.CTkLabel(r, text="%s (%d)" % (n, len(v)), anchor="w").pack(side="left")
                ctk.CTkButton(r, text="\u2715", width=30, fg_color=p["card2"], text_color=p["text"], hover_color="#b91c1c",
                              command=lambda n=n: delete(n)).pack(side="right")

        def delete(n):
            self.store.delete(n)
            for a, g in list(self.cfg["bindings"].items()):
                if g == n:
                    self.cfg["bindings"][a] = None
            C.save(self.cfg)
            refresh()

        def rec():
            n = name.get().strip().replace(" ", "_")
            if not n or n in C.BUILTIN or n == "(none)":
                messagebox.showwarning("Name", "Enter a unique name (not a built-in gesture name).", parent=d)
                return

            def done(acc):
                if len(acc) > 20:
                    self.store.add(n, acc)
                    msg.configure(text="\u2714 Saved %d samples for '%s'" % (len(acc), n))
                else:
                    msg.configure(text="Hand was not visible enough - try again")
                refresh()
            self.collect(d, msg, bar, "Get ready: show gesture '%s'" % n,
                         lambda: None if self.engine is None or self.engine.vec is None else [round(float(x), 4) for x in self.engine.vec],
                         80, done)
        ctk.CTkButton(left, text="\u25cf  Record samples", height=40, command=rec).pack(fill="x", pady=6)

        def upd():
            try:
                if d.winfo_exists():
                    live.configure(text="Recognised right now: %s" % ((self.engine.gesture if self.engine else None) or "-"))
                    d.after(120, upd)
            except Exception:
                pass
        refresh()
        upd()

    def practice(self):
        p = self.p
        d = self.dialog("Practice board", 760, 560)
        ctk.CTkLabel(d, text="Practice board", font=self.font(20, True)).pack(anchor="w", padx=20, pady=(14, 0))
        ctk.CTkLabel(d, text="Try each action here: click the button, right-click / double-click the boxes, drag the square, scroll the text.",
                     text_color=p["sub"]).pack(anchor="w", padx=20)
        cv = tk.Canvas(d, width=440, height=330, bg=p["card"], highlightthickness=0)
        cv.pack(side="left", padx=20, pady=12)
        counts = {"left": 0, "right": 0, "double": 0, "middle": 0}
        txt = cv.create_text(220, 20, text="", fill=p["text"], font=("Segoe UI", 11))

        def upd():
            cv.itemconfigure(txt, text="left %d   right %d   double %d   middle %d" % (counts["left"], counts["right"], counts["double"], counts["middle"]))
        upd()

        def box(x, y, w, h, color, label, ev, key):
            i = cv.create_rectangle(x, y, x + w, y + h, fill=color, outline="")
            cv.create_text(x + w / 2, y + h / 2, text=label, fill="white", font=("Segoe UI", 11, "bold"))
            for t in (i,):
                cv.tag_bind(t, ev, lambda e, k=key: (counts.__setitem__(k, counts[k] + 1), upd()))
        box(20, 50, 130, 70, p["accent"], "LEFT CLICK", "<Button-1>", "left")
        box(160, 50, 130, 70, "#e11d48", "RIGHT CLICK", "<Button-3>", "right")
        box(300, 50, 120, 70, "#7c3aed", "DOUBLE CLICK", "<Double-Button-1>", "double")
        box(20, 130, 130, 50, "#0d9488", "MIDDLE CLICK", "<Button-2>", "middle")
        cv.create_text(220, 215, text="Drag the square (grab with a fist):", fill=p["sub"], font=("Segoe UI", 10))
        sq = cv.create_rectangle(190, 240, 250, 300, fill="#f59e0b", outline="")
        pos = {}

        def press(e):
            pos["x"], pos["y"] = e.x, e.y

        def drag(e):
            cv.move(sq, e.x - pos["x"], e.y - pos["y"])
            pos["x"], pos["y"] = e.x, e.y
        cv.tag_bind(sq, "<ButtonPress-1>", press)
        cv.tag_bind(sq, "<B1-Motion>", drag)
        tb = ctk.CTkTextbox(d, width=240)
        tb.pack(side="left", fill="y", pady=12, padx=(0, 16))
        tb.insert("end", "\n".join("Scroll line %d  -  use two fingers and move your hand up / down" % i for i in range(1, 80)))
        tb.configure(state="disabled")

    # ------------------------------------------------------------------ calibration
    def collect(self, d, lab, bar, text, getter, n, cb, delay=3, interval=50):
        def cd(k):
            try:
                if not d.winfo_exists():
                    return
            except Exception:
                return
            if k > 0:
                lab.configure(text="%s\n... %d" % (text, k))
                bar.set(0)
                self.root.after(1000, cd, k - 1)
            else:
                lab.configure(text="Recording - hold it!")
                samp([], 0)

        def samp(acc, i):
            try:
                if not d.winfo_exists():
                    return
            except Exception:
                return
            v = getter()
            if v is not None:
                acc.append(v)
            bar.set(i / n)
            if i < n:
                self.root.after(interval, samp, acc, i + 1)
            else:
                cb(acc)
        cd(delay)

    def calibrate_menu(self):
        d = self.dialog("Calibrate", 420, 300)
        ctk.CTkLabel(d, text="Calibration", font=self.font(20, True)).pack(pady=(18, 4))
        ctk.CTkLabel(d, text="Do both once for the most accurate control.\nTracking must be running.", text_color=self.p["sub"]).pack(pady=(0, 14))
        ctk.CTkButton(d, text="1.  Cursor range  (how far you reach)", height=40, command=lambda: (d.destroy(), self.calibrate_range())).pack(fill="x", padx=30, pady=5)
        ctk.CTkButton(d, text="2.  Pinch  (click sensitivity)", height=40, command=lambda: (d.destroy(), self.calibrate_pinch())).pack(fill="x", padx=30, pady=5)

    def calibrate_range(self):
        if not self.need_engine():
            return
        d = self.dialog("Calibrate cursor range", 560, 640)
        self.freeze(d)
        ctk.CTkLabel(d, text="Cursor range", font=self.font(20, True)).pack(pady=(14, 2))
        ctk.CTkLabel(d, text="Move your hand to each corner of the area you are comfortable reaching.\nThat area will cover your whole screen.",
                     text_color=self.p["sub"]).pack()
        self.mini_preview(d, 440).pack(pady=8)
        lab = ctk.CTkLabel(d, text="", font=self.font(15, True))
        lab.pack(pady=4)
        bar = ctk.CTkProgressBar(d, width=380)
        bar.set(0)
        bar.pack(pady=8)
        names = ["\u2196 TOP-LEFT", "\u2197 TOP-RIGHT", "\u2198 BOTTOM-RIGHT", "\u2199 BOTTOM-LEFT"]
        pts = []

        def step(i):
            if i == 4:
                if any(q is None for q in pts):
                    messagebox.showwarning("Calibration", "Hand was lost - please try again.")
                    d.destroy()
                    return
                x0, x1 = (pts[0][0] + pts[3][0]) / 2, (pts[1][0] + pts[2][0]) / 2
                y0, y1 = (pts[0][1] + pts[1][1]) / 2, (pts[2][1] + pts[3][1]) / 2
                if x1 - x0 < 0.05 or y1 - y0 < 0.05:
                    messagebox.showwarning("Calibration", "Range too small - move your hand further between corners.")
                else:
                    self.cfg["region"] = [round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3)]
                    C.save(self.cfg)
                    messagebox.showinfo("Calibration", "Cursor range saved.")
                d.destroy()
                return

            def done(acc, i=i):
                pts.append((sum(a[0] for a in acc) / len(acc), sum(a[1] for a in acc) / len(acc)) if acc else None)
                step(i + 1)
            self.collect(d, lab, bar, "Move your hand to the %s of your comfortable reach" % names[i],
                         lambda: self.engine.raw_ptr if self.engine else None, 20, done)
        step(0)

    def calibrate_pinch(self):
        if not self.need_engine():
            return
        d = self.dialog("Calibrate pinch", 560, 600)
        self.freeze(d)
        ctk.CTkLabel(d, text="Pinch sensitivity", font=self.font(20, True)).pack(pady=(14, 2))
        self.mini_preview(d, 440).pack(pady=8)
        lab = ctk.CTkLabel(d, text="", font=self.font(15, True))
        lab.pack(pady=4)
        bar = ctk.CTkProgressBar(d, width=380)
        bar.set(0)
        bar.pack(pady=8)

        def get():
            m = self.engine.metrics if self.engine else None
            return m["pinch"][0] if m else None

        def med(a):
            a = sorted(a)
            return a[len(a) // 2]

        def after_open(op):
            def after_pinch(pi):
                if len(op) < 5 or len(pi) < 5:
                    messagebox.showwarning("Calibration", "Hand was not visible enough. Try again.")
                else:
                    o, q = med(op), med(pi)
                    if o - q < 0.15:
                        messagebox.showwarning("Calibration", "Open and pinched poses look too similar. Try again.")
                    else:
                        self.cfg["pinch_threshold"] = round(min(0.6, max(0.12, q + 0.45 * (o - q))), 3)
                        C.save(self.cfg)
                        if "pinch_threshold" in self.sliders:
                            self.sliders["pinch_threshold"][0].set(self.cfg["pinch_threshold"])
                            self.sliders["pinch_threshold"][1].configure(text="%.2f" % self.cfg["pinch_threshold"])
                        messagebox.showinfo("Calibration", "Pinch sensitivity set to %.2f" % self.cfg["pinch_threshold"])
                d.destroy()
            self.collect(d, lab, bar, "Now PINCH thumb + index fingertip together and keep them touching", get, 30, after_pinch)
        self.collect(d, lab, bar, "Hold your hand OPEN, thumb and index NOT touching", get, 30, after_open)

    # ------------------------------------------------------------------ help + first-run wizard
    def help(self):
        d = self.dialog("Help", 860, 640)
        frames, bar, show = self.tabbed(d, ["Quick start", "Gestures", "Troubleshooting", "Tips", "About"], scroll=False)
        bar.destroy()

        def text(f, s):
            t = ctk.CTkTextbox(f, wrap="word", font=self.font(13))
            t.pack(fill="both", expand=True)
            t.insert("end", s)
            t.configure(state="disabled")
        text(frames["Quick start"], HELP_QUICK)
        g = "Your current controls (change them in 'Gestures'):\n\n"
        for a, lbl in C.ACTIONS.items():
            gn = self.cfg["bindings"].get(a)
            g += "  %-34s %s\n" % (lbl, ("%s  %s" % (C.EMOJI.get(gn, "\u2605"), C.SHORT.get(gn, gn))) if gn else "-")
        g += "\nBuilt-in gestures:\n\n" + "\n".join("  %s  %s" % (C.EMOJI[k], v) for k, v in C.BUILTIN.items())
        text(frames["Gestures"], g)
        text(frames["Troubleshooting"], HELP_TROUBLE)
        text(frames["Tips"],
             "\u2022 Good light on your hand matters more than a good camera.\n\n"
             "\u2022 Keep your elbow resting - small wrist/hand movements are enough once calibrated.\n\n"
             "\u2022 To click without moving the cursor, pinch calmly; the app rewinds the cursor a few frames.\n\n"
             "\u2022 Grab: close your fist, move, then open your hand to drop (drag and drop, selecting text, moving windows).\n\n"
             "\u2022 Pause hotkey: %s  (or show three fingers).\n\n"
             "\u2022 Camera popup: sidebar > 'Camera popup'. Drag it anywhere, right-click it to resize or fade it. It always stays on top.\n\n"
             "\u2022 Minimize to tray keeps everything running in the background. Right-click the tray icon for controls.\n\n"
             "\u2022 Left-handed? Settings > Tracking > Tracked hand.\n\n"
             "\u2022 Hard to pinch? Turn on Dwell click: keep the cursor still to click.\n\n"
             "\u2022 Use Export in Settings > System to back up your gestures and settings." % self.cfg["hotkey"])
        text(frames["About"], "Gesture Mouse\n\nHand-tracking mouse control powered by MediaPipe, OpenCV and pynput.\n"
             "All processing happens on your PC - no images leave your computer.\n\nData folder: %APPDATA%\\GestureMouse")
        ctk.CTkButton(frames["Quick start"], text="Run guided setup", command=lambda: (d.destroy(), self.wizard())).pack(pady=8)

    def wizard(self):
        p = self.p
        d = self.dialog("Welcome to Gesture Mouse", 780, 640)
        nav = ctk.CTkFrame(d, fg_color="transparent")
        nav.pack(side="bottom", fill="x", padx=24, pady=16)
        body = ctk.CTkFrame(d, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=26, pady=(18, 0))
        step = [0]

        def plain(b, s):
            ctk.CTkLabel(b, text=s, justify="left", wraplength=690, font=self.font(14), anchor="w").pack(anchor="w", pady=6)

        def pg_welcome(b):
            plain(b, "Control your mouse with your bare hand - no special hardware.\n\n"
                  "\u270b  Open hand  \u2192  move the cursor\n\u270a  Fist  \u2192  grab / drag and drop\n"
                  "\u25c9  Thumb + finger pinch  \u2192  clicks\n\u270c  Two fingers  \u2192  scroll\n\n"
                  "This 2-minute setup picks your camera, checks tracking and calibrates the cursor.\nYou need a webcam (or a phone camera app).")

        def pg_cam(b):
            plain(b, "Choose the camera you want to use. The dialog shows a live preview so you can be sure it is the right one.")
            ctk.CTkButton(b, text="Open camera chooser", height=40, command=self.camera_dialog).pack(anchor="w", pady=8)
            plain(b, "Current: " + self.cam_current())

        def pg_check(b):
            plain(b, "Press Start tracking, then hold your open hand in front of the camera - about 50-70 cm away with good light.")
            ctk.CTkButton(b, text="\u25b6  Start tracking", height=40, command=self.start).pack(anchor="w", pady=4)
            self.mini_preview(b, 400).pack(pady=8)
            st = ctk.CTkLabel(b, text="", font=self.font(16, True))
            st.pack()

            def chk():
                try:
                    if not st.winfo_exists():
                        return
                    e = self.engine
                    ok = bool(e and e.is_alive() and e.vec is not None)
                    st.configure(text="\u2714 Hand detected - great!" if ok else "Show your open hand to the camera...")
                    st.after(300, chk)
                except Exception:
                    pass
            chk()

        def pg_cal(b):
            plain(b, "Calibrate so the cursor reaches every screen corner comfortably and clicks feel right. Tracking must be running.")
            ctk.CTkButton(b, text="Calibrate cursor range", height=40, command=self.calibrate_range).pack(anchor="w", pady=6)
            ctk.CTkButton(b, text="Calibrate pinch", height=40, command=self.calibrate_pinch).pack(anchor="w", pady=6)

        def pg_done(b):
            plain(b, "You're ready!\n\n\u2022 Open the Practice board to try clicking, dragging and scrolling.\n"
                  "\u2022 Press F1 any time for help.\n\u2022 Change controls in Gestures, record your own in Train gestures.\n"
                  "\u2022 Pause with %s or three fingers." % self.cfg["hotkey"])
            ctk.CTkButton(b, text="Open practice board", height=40, command=self.practice).pack(anchor="w", pady=6)
        pages = [("Welcome", pg_welcome), ("1. Camera", pg_cam), ("2. Check tracking", pg_check), ("3. Calibrate", pg_cal), ("Done", pg_done)]
        back = ctk.CTkButton(nav, text="Back", width=90, fg_color=p["card2"], text_color=p["text"], hover_color=p["bg"], command=lambda: go(-1))
        nxt = ctk.CTkButton(nav, text="Next", width=110, command=lambda: go(1))
        skip = ctk.CTkButton(nav, text="Skip", width=70, fg_color="transparent", text_color=p["sub"], hover_color=p["card2"], command=lambda: finish())
        skip.pack(side="left")
        nxt.pack(side="right", padx=3)
        back.pack(side="right", padx=3)

        def finish():
            self.cfg["first_run"] = False
            C.save(self.cfg)
            d.destroy()

        def go(k):
            if step[0] + k >= len(pages):
                finish()
                return
            step[0] = max(0, step[0] + k)
            render()

        def render():
            for w in body.winfo_children():
                w.destroy()
            title, fn = pages[step[0]]
            ctk.CTkLabel(body, text=title, font=self.font(24, True)).pack(anchor="w")
            fn(body)
            nxt.configure(text="Finish" if step[0] == len(pages) - 1 else "Next")
            back.configure(state="normal" if step[0] else "disabled")
        render()
'''

# ---------------------------------------------------------------- build / launch scripts
BUILD_ARGS = [
    "--noconfirm", "--clean", "--windowed", "--name", "GestureMouse",
    "--collect-all", "mediapipe",
    "--collect-all", "customtkinter",
    "--hidden-import", "pystray._win32",
    "--hidden-import", "pynput.mouse._win32",
    "--hidden-import", "pynput.keyboard._win32",
]

FILES["run.bat"] = "@echo off\r\ncd /d %~dp0\r\nstart \"\" .venv\\Scripts\\pythonw.exe main.py\r\n"
FILES["build_exe.bat"] = (
    "@echo off\r\ncd /d %~dp0\r\n"
    ".venv\\Scripts\\python.exe -m pip install pyinstaller\r\n"
    ".venv\\Scripts\\python.exe -m PyInstaller " + " ".join(BUILD_ARGS) + " --onedir main.py\r\n"
    "echo.\r\necho Done: dist\\GestureMouse\\GestureMouse.exe\r\npause\r\n"
)


def sh(cmd, **kw):
    print(">", " ".join(cmd))
    return subprocess.call(cmd, **kw)


def main():
    ap = argparse.ArgumentParser(description="Gesture Mouse generator / installer / launcher")
    ap.add_argument("--dir", default="GestureMouse", help="project folder name")
    ap.add_argument("--no-install", action="store_true", help="only write files")
    ap.add_argument("--no-run", action="store_true", help="do not launch the app")
    ap.add_argument("--build", action="store_true", help="also build a Windows .exe with PyInstaller")
    ap.add_argument("--onefile", action="store_true", help="single-file exe (slower start-up than the default folder build)")
    ap.add_argument("--force", action="store_true", help="skip the Python version check")
    a = ap.parse_args()

    if not a.force and not ((3, 9) <= sys.version_info[:2] <= (3, 12)):
        sys.exit("MediaPipe needs Python 3.9-3.12 (you have %d.%d). Install Python 3.11/3.12 and run again, or use --force." % sys.version_info[:2])

    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), a.dir)
    for rel, content in FILES.items():
        path = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
    print("Project written to", root)
    if a.no_install:
        return

    win = os.name == "nt"
    py = os.path.join(root, ".venv", "Scripts" if win else "bin", "python.exe" if win else "python")
    if not os.path.exists(py):
        if sh([sys.executable, "-m", "venv", os.path.join(root, ".venv")]):
            sys.exit("Could not create virtual environment.")
    sh([py, "-m", "pip", "install", "--upgrade", "pip"])
    if sh([py, "-m", "pip", "install", "-r", os.path.join(root, "requirements.txt")]):
        sys.exit("Dependency installation failed.")

    if a.build:
        if sh([py, "-m", "pip", "install", "pyinstaller"]):
            sys.exit("Could not install PyInstaller.")
        cmd = [py, "-m", "PyInstaller"] + BUILD_ARGS + ["--onefile" if a.onefile else "--onedir", "main.py"]
        if sh(cmd, cwd=root):
            sys.exit("Build failed.")
        print("\nEXE ready in:", os.path.join(root, "dist"))

    if not a.no_run:
        sh([py, "main.py"], cwd=root)


if __name__ == "__main__":
    main()