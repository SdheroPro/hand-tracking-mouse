# ✋ Gesture Mouse — Bare-Hand PC Control & Tracking

[![Python Version](https://img.shields.io/badge/python-3.9--3.12-blue.svg)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.21-green.svg)](https://google.github.io/mediapipe/)
[![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-orange.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)

**Gesture Mouse** is a single-file Python application, installer, and generator that lets you control your PC cursor, perform clicks, grab/drag items, and scroll windows using **only your bare hand and a standard webcam**—no specialized hardware required.

It combines **MediaPipe landmark tracking**, a **One Euro jitter-filtering algorithm**, **k-NN custom gesture recognition**, and a modern **CustomTkinter GUI** with multiple themes, a live overlay popup, and custom calibration options.

---

## ✨ Key Features

* 🖱️ **Full Cursor Control:** Smooth pointing, left/right/middle clicking, double-clicking, drag-and-drop holding, and vertical scrolling.
* ⚡ **Ultra-Low Latency Tracking:** Multi-threaded webcam frame grabber keeps tracking responsive and smooth even on modest webcams.
* 🎯 **One Euro Filter & Anti-Drift:** Custom filtering handles cursor jitter when holding still while eliminating lag during rapid movements.
* 🧠 **Train Custom Gestures:** Features a built-in k-NN classifier allowing you to train, record, and save your own hand poses without heavy machine learning dependencies.
* 🎨 **Modern Dark/Light UI:** Built with CustomTkinter featuring 8 themes (Midnight Blue, Neon Violet, Cyber Pink, OLED Black, etc.), live activity logs, and a practice board.
* 📌 **Floating Camera Popup:** Always-on-top, resizable, borderless camera overlay with adjustable transparency.
* ⚙️ **One-File Setup Script:** Automated installer creates virtual environments, handles dependency checks, generates app modules, and can compile standalone `.exe` packages via PyInstaller.

---

## 🖐️ Default Gesture Controls

| Hand Gesture | Visual | Triggered Action |
| :--- | :---: | :--- |
| **Open Hand** | 🖐️ | **Move Cursor** |
| **Pinch Index** | 🤏 | **Left Click** |
| **Pinch Middle** | 🤌 | **Right Click** |
| **Pinch Ring** | 🤏 | **Double Click** |
| **Pinch Pinky** | 🤏 | **Middle Click** |
| **Closed Fist** | ✊ | **Grab / Drag & Drop** (Hold) |
| **Peace / V-Sign** | ✌️ | **Scroll** (Move hand up/down) |
| **Three Fingers** | 🤟 | **Pause / Resume Control** |

*Note: All gesture bindings can be fully remapped or replaced with custom-trained gestures inside the app UI.*

---

## 🛠️ Quick Start & Installation

### Requirements
* **Python:** 3.9 – 3.12 *(required for MediaPipe wheels)*
* **Hardware:** Any standard USB or built-in webcam (or phone camera via DroidCam/IP Webcam)

### Running with Setup Script
Clone this repository and run `gesture_mouse_setup.py`. It will automatically create a `.venv`, install required packages (`mediapipe`, `opencv-contrib-python`, `customtkinter`, `pynput`, `pystray`), write all application files, and launch the GUI:

```bash
# Clone the repository
git clone https://github.com/SdheroPro/hand-tracking-mouse.git
cd hand-tracking-mouse

# Run setup & launch app
python gesture_mouse_setup.py
