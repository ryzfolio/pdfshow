# PDF Slideshow Operator

A Python-based PDF slideshow tool with operator and fullscreen display support.
Made with **PyQt5** for the GUI and **PyMuPDF (fitz)** for rendering PDF pages.

This app is designed for live events, presentations, or church services where the operator controls the PDF slides while sending fullscreen output to another display.

---

## 🚀 Features

* Open and render PDF files into high-quality slides.
* Dual-window system: **Operator Window** (controller) + **Fullscreen Output** (audience display).
* Preview of current and next slide.
* Thumbnail navigation for quick slide access.
* Set and show **cover image** with blinking indicator.
* Stop slideshow mode with blinking button.
* Supports multiple displays (choose output display).
* Keyboard shortcuts for fast control:

  * `Right Arrow` / `Space` → Next slide
  * `Left Arrow` → Previous slide
  * `Ctrl + O` → Open PDF
  * `Esc` → Exit

---

## 📦 Requirements

* Python 3.8+
* PyQt5
* PyMuPDF (fitz)

Install dependencies with:

```bash
pip install -r requirements.txt
```

**requirements.txt**

```txt
PyQt5>=5.15.0
PyMuPDF>=1.18.0
```

---

## ▶️ Usage

Run the app with:

```bash
python main.py
```

(replace `main.py` with your script filename if different)

---


## 📜 License

Free to use and modify for your personal/project needs.
