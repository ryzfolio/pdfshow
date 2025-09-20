import sys
import fitz  # PyMuPDF
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QListWidget,
    QHBoxLayout, QVBoxLayout, QListWidgetItem, QMessageBox, QComboBox, QAction
)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QFont
from PyQt5.QtCore import Qt, QSize, QTimer

# --- TEST WINDOW ---
class TestWindow(QWidget):
    def __init__(self, screen, label_text):
        super().__init__()
        self.setWindowFlag(Qt.Window)
        self.setStyleSheet("background-color: #474343;")
        self.setWindowTitle(label_text)

        label = QLabel(label_text, self)
        label.setStyleSheet("color: white; font-size: 48px;")
        label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()
        self.setLayout(layout)
        self.setGeometry(screen.geometry())

        # Auto-close 2 detik
        QTimer.singleShot(2000, self.close)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

# --- FULLSCREEN WINDOW ---
class FullscreenWindow(QWidget):
    def __init__(self, screen=None):
        super().__init__()
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.screen = screen
        self.current_pixmap = None

    def show_on_screen(self):
        if self.screen:
            self.setGeometry(self.screen.geometry())
        self.showFullScreen()

    def set_pixmap(self, pixmap: QPixmap):
        self.current_pixmap = pixmap
        if pixmap is None:
            self.label.clear()
            return
        scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)

    def resizeEvent(self, event):
        if self.current_pixmap:
            self.set_pixmap(self.current_pixmap)
        super().resizeEvent(event)

# --- OPERATOR WINDOW ---
class OperatorWindow(QWidget):
    def closeEvent(self, event):
        if hasattr(self, 'fullscreen_win') and self.fullscreen_win.isVisible():
            self.fullscreen_win.close()
        event.accept()

    def __init__(self, app):
        
        super().__init__()
        self.app = app
        self.setWindowTitle('PDF Slideshow - Operator')
        self.pdf_doc = None
        self.page_pixmaps = []
        self.current_index = 0
        self.cover_pixmap = None
        self.show_cover_flag = False
        self.stop_flag = False
        self.test_windows = [] 

        # Blink timers
        self.blink_timer = QTimer()
        self.blink_timer.setInterval(500)
        self.blink_timer.timeout.connect(self._toggle_cover_blink)
        self.blink_state = False

        self.stop_blink_timer = QTimer()
        self.stop_blink_timer.setInterval(500)
        self.stop_blink_timer.timeout.connect(self._toggle_stop_blink)
        self.stop_blink_state = False

        # Screens
        self.display_combo = QComboBox()
        self.screens = self.app.screens()
        for i, screen in enumerate(self.screens):
            self.display_combo.addItem(f"Display {i+1}")
        self.display_combo.setCurrentIndex(0)

        # Tombol besar & aesthetic
        btn_style = """
            background-color: #FF9A91; 
            color: black; 
            font-size: 20px; 
            padding:10px 25px; 
            border-radius:10px;
            margin-left:5px;
            margin-right:5px
        """
        
        self.open_btn = QPushButton('Open PDF'); self.open_btn.setStyleSheet(btn_style); self.open_btn.clicked.connect(self.open_pdf)
        self.test_btn = QPushButton('Tes Output'); self.test_btn.setStyleSheet(btn_style); self.test_btn.clicked.connect(self.test_output)
        self.stop_btn = QPushButton('Stop Slideshow'); self.stop_btn.setStyleSheet(btn_style); self.stop_btn.setCheckable(True); self.stop_btn.clicked.connect(self.toggle_stop)
        self.set_cover_btn = QPushButton('Set Cover'); self.set_cover_btn.setStyleSheet(btn_style); self.set_cover_btn.clicked.connect(self.set_cover)
        self.show_cover_btn = QPushButton('Show Cover'); self.show_cover_btn.setStyleSheet(btn_style); self.show_cover_btn.setCheckable(True); self.show_cover_btn.clicked.connect(self.toggle_cover)
        self.prev_btn = QPushButton('Prev ◀'); self.prev_btn.setStyleSheet(btn_style); self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton('Next ▶'); self.next_btn.setStyleSheet(btn_style); self.next_btn.clicked.connect(self.next_page)

        # Preview labels
        font_label = "font-size:16px; font-weight:bold; color:white;margin-top:35px"
        self.current_label_text = QLabel("Current Page"); self.current_label_text.setAlignment(Qt.AlignCenter); self.current_label_text.setStyleSheet(font_label)
        self.preview_label = QLabel(); self.preview_label.setAlignment(Qt.AlignCenter); self.preview_label.setFixedSize(800, 450); self.preview_label.setStyleSheet("background-color: #1E1E1E; border: 2px solid #FFFFFF;")
        self.next_label_text = QLabel("Next Page"); self.next_label_text.setAlignment(Qt.AlignCenter); self.next_label_text.setStyleSheet(font_label)
        self.next_preview_label = QLabel(); self.next_preview_label.setAlignment(Qt.AlignCenter); self.next_preview_label.setFixedSize(800, 450); self.next_preview_label.setStyleSheet("background-color: #1E1E1E; border: 2px solid #FFFFFF;")

        # Thumbnail horizontal
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setViewMode(QListWidget.IconMode)
        self.thumbnail_list.setFlow(QListWidget.LeftToRight)
        self.thumbnail_list.setWrapping(False)
        self.thumbnail_list.setIconSize(QSize(320, 180))
        self.thumbnail_list.setResizeMode(QListWidget.Adjust)
        self.thumbnail_list.itemClicked.connect(self.thumbnail_clicked)
        self.thumbnail_list.setStyleSheet("background-color: #878787; color: white;")

        # Layouts
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.open_btn); top_layout.addWidget(QLabel("Output:")); top_layout.addWidget(self.display_combo); top_layout.addWidget(self.test_btn); top_layout.addWidget(self.stop_btn); top_layout.addStretch()

        cover_layout = QHBoxLayout()
        cover_layout.addWidget(self.set_cover_btn); cover_layout.addWidget(self.show_cover_btn); cover_layout.addStretch()

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.prev_btn); controls_layout.addWidget(self.next_btn)

        current_layout = QVBoxLayout()
        current_layout.addWidget(self.current_label_text)
        current_layout.addWidget(self.preview_label)

        next_layout = QVBoxLayout()
        next_layout.addWidget(self.next_label_text)
        next_layout.addWidget(self.next_preview_label)

        preview_layout = QHBoxLayout()
        preview_layout.addLayout(current_layout)
        preview_layout.addLayout(next_layout)

        main_left_layout = QVBoxLayout()
        main_left_layout.addLayout(top_layout)
        main_left_layout.addLayout(cover_layout)
        main_left_layout.addLayout(preview_layout)
        main_left_layout.addLayout(controls_layout)
        main_left_layout.addWidget(self.thumbnail_list)

        self.setLayout(main_left_layout)
        self.setStyleSheet("background-color: #121212; color: white;")
        self.showMaximized()

        self.fullscreen_win = FullscreenWindow(screen=self.screens[self.display_combo.currentIndex()])
        self.display_combo.currentIndexChanged.connect(self.update_display)
        self._init_shortcuts()

    # --- SHORTCUTS ---
    def _init_shortcuts(self):
        for key, func in [("Right", self.next_page), ("Left", self.prev_page), ("Space", self.next_page), ("Ctrl+O", self.open_pdf)]:
            act = QAction(self)
            act.setShortcut(key)
            act.triggered.connect(func)
            self.addAction(act)

    # --- COVER & STOP ---
    def toggle_stop(self):
        self.stop_flag = not self.stop_flag
        if self.stop_flag:
            self.fullscreen_win.close()
            self.stop_blink_timer.start()
        else:
            self.stop_blink_timer.stop()
            self.stop_btn.setStyleSheet('background-color: #FF9A91; color: black; font-size: 20px; padding:10px 25px; border-radius:10px;margin-left:5px; margin-right:5px')
            self.fullscreen_win = FullscreenWindow(screen=self.screens[self.display_combo.currentIndex()])
            if self.show_cover_flag and self.cover_pixmap:
                self.fullscreen_win.set_pixmap(self.cover_pixmap)
            elif self.page_pixmaps:
                self.fullscreen_win.set_pixmap(self.page_pixmaps[self.current_index])
            self.fullscreen_win.show_on_screen()

    def _toggle_stop_blink(self):
        if self.stop_flag:
            self.stop_blink_state = not self.stop_blink_state
            self.stop_btn.setStyleSheet('background-color: red; color: white; font-size: 20px; padding:10px 25px; border-radius:10px;margin-left:5px; margin-right:5px' if self.stop_blink_state else 'background-color: #FF9A91; color: black; font-size: 20px; padding:10px 25px; border-radius:10px;margin-left:5px; margin-right:5px')

    def _toggle_cover_blink(self):
        if self.show_cover_flag:
            self.blink_state = not self.blink_state
            self.show_cover_btn.setStyleSheet('background-color: red; color: white; font-size: 20px; padding:10px 25px; border-radius:10px;margin-left:5px; margin-right:5px' if self.blink_state else 'background-color: #FF9A91; color: black; font-size: 20px; padding:10px 25px; border-radius:10px;margin-left:5px; margin-right:5px')
        else:
            self.show_cover_btn.setStyleSheet('background-color: #FF9A91; color: black; font-size: 20px; padding:10px 25px; border-radius:10px;margin-left:5px; margin-right:5px')
            self.blink_timer.stop()

    # --- DISPLAY ---
    def update_display(self, idx):
        self.fullscreen_win.screen = self.screens[idx]

    def test_output(self):
        self.test_windows = []
        for i, screen in enumerate(self.screens):
            win = TestWindow(screen, f"DISPLAY {i+1} - TEST VISUAL")
            win.show()
            win.raise_()           # pastikan di depan
            win.activateWindow()   # aktifkan window
            self.test_windows.append(win) 

    # --- COVER ---
    def set_cover(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Set Cover Image', '', 'Images (*.png *.jpg *.jpeg)')
        if not path: return
        pix = QPixmap(path)
        if pix.isNull():
            QMessageBox.critical(self, 'Error', 'Failed to load image'); return
        self.cover_pixmap = pix
        QMessageBox.information(self, 'Cover Set', 'Cover image set successfully.')

    def toggle_cover(self):
        if not self.cover_pixmap:
            QMessageBox.warning(self, 'No Cover', 'No cover set.'); self.show_cover_btn.setChecked(False); return
        self.show_cover_flag = not self.show_cover_flag
        if self.show_cover_flag:
            self.fullscreen_win.screen = self.screens[self.display_combo.currentIndex()]
            self.fullscreen_win.set_pixmap(self.cover_pixmap)
            self.fullscreen_win.show_on_screen()
            self.blink_timer.start()
        else:
            self.blink_timer.stop()
            self.show_cover_btn.setStyleSheet('')
            if self.page_pixmaps:
                self.fullscreen_win.set_pixmap(self.page_pixmaps[self.current_index])
            else:
                self.fullscreen_win.set_pixmap(None)

    # --- PDF ---
    def open_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open PDF', '', 'PDF Files (*.pdf)')
        if not path: return
        try: self.pdf_doc = fitz.open(path)
        except Exception as e: QMessageBox.critical(self, 'Error', f'Failed to open PDF:\n{e}'); return
        self.render_pages()

    def render_pages(self):
        self.page_pixmaps = []
        self.thumbnail_list.clear()
        for i in range(len(self.pdf_doc)):
            page = self.pdf_doc[i]; mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes(output='png'); qimg = QImage.fromData(img_bytes)
            qpix = QPixmap.fromImage(qimg)
            self.page_pixmaps.append(qpix)
            thumbnail_pix = qpix.scaled(480, 270, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon = QIcon(thumbnail_pix)
            item = QListWidgetItem(); item.setIcon(icon); item.setData(Qt.UserRole,i); item.setText(str(i+1)); item.setSizeHint(QSize(400,250))
            self.thumbnail_list.addItem(item)
        if self.page_pixmaps: self.show_page(0); self.fullscreen_win.show_on_screen()

    def show_page(self, index):
        if index<0 or index>=len(self.page_pixmaps): return
        self.current_index=index
        pix=self.page_pixmaps[index]
        self.preview_label.setPixmap(pix.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if index+1<len(self.page_pixmaps):
            next_pix=self.page_pixmaps[index+1]
            self.next_preview_label.setPixmap(next_pix.scaled(self.next_preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else: self.next_preview_label.clear()
        if not self.show_cover_flag: self.fullscreen_win.set_pixmap(pix)
        item=self.thumbnail_list.item(index)
        if item: self.thumbnail_list.setCurrentItem(item)

    def prev_page(self): 
        if not self.page_pixmaps: return
        self.show_page(max(0,self.current_index-1))

    def next_page(self):
        if not self.page_pixmaps: return
        self.show_page(min(len(self.page_pixmaps)-1,self.current_index+1))

    def thumbnail_clicked(self,item:QListWidgetItem):
        idx=item.data(Qt.UserRole)
        self.show_page(idx)

    def keyPressEvent(self,event):
        if event.key() in (Qt.Key_Space,Qt.Key_Right): self.next_page()
        elif event.key()==Qt.Key_Left: self.prev_page()
        elif event.key()==Qt.Key_Escape:
            if self.show_cover_flag: return
            else: self.fullscreen_win.close(); self.close()
        super().keyPressEvent(event)

# --- MAIN ---
def main():
    app=QApplication(sys.argv)
    op=OperatorWindow(app)
    op.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()
