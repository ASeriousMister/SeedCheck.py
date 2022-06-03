import qrcode

from PyQt5.QtGui import QColor, QPen
import PyQt5.QtGui as QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton, QWidget,
    QFileDialog,
)

from electrum.i18n import _
from electrum.simple_config import SimpleConfig

from .util import WindowModalDialog, WWLabel, getSaveFileName


class QRCodeWidget(QWidget):

    def __init__(self, data = None, fixedSize=False):
        QWidget.__init__(self)
        self.data = None
        self.qr = None
        self.margin = 0
        self.fixedSize=fixedSize
        if fixedSize:
            self.setFixedSize(fixedSize, fixedSize)
        self.setData(data)


    def setData(self, data):
        if self.data != data:
            self.data = data
        if self.data:
            self.qr = qrcode.QRCode(
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=0,
            )
            self.qr.add_data(self.data)
            if not self.fixedSize:
                k = len(self.qr.get_matrix())
                self.setMinimumSize(k*5,k*5)
        else:
            self.qr = None

        self.update()


    def paintEvent(self, e):
        if not self.data:
            return

        black = QColor(0, 0, 0, 255)
        white = QColor(255, 255, 255, 255)
        black_pen = QPen(black)
        black_pen.setJoinStyle(Qt.MiterJoin)

        if not self.qr:
            qp = QtGui.QPainter()
            qp.begin(self)
            qp.setBrush(white)
            qp.setPen(white)
            r = qp.viewport()
            qp.drawRect(0, 0, r.width(), r.height())
            qp.end()
            return

        matrix = self.qr.get_matrix()
        k = len(matrix)
        qp = QtGui.QPainter()
        qp.begin(self)
        r = qp.viewport()
        framesize = min(r.width(), r.height())
        boxsize = int((framesize - 2*self.margin)/k)
        if boxsize < 2:
            print('Warning: cannot draw qr code, boxsize too small')
        size = k*boxsize
        left = (framesize - size)/2
        top = (framesize - size)/2
        # Draw white background with margin
        qp.setBrush(white)
        qp.setPen(white)
        qp.drawRect(0, 0, framesize, framesize)
        # Draw qr code
        qp.setBrush(black)
        qp.setPen(black_pen)
        for r in range(k):
            for c in range(k):
                if matrix[r][c]:
                    qp.drawRect(int(left+c*boxsize), int(top+r*boxsize),
                                boxsize - 1, boxsize - 1)
        qp.end()



class QRDialog(WindowModalDialog):

    def __init__(
            self,
            *,
            data,
            parent=None,
            title="",
            show_text=False,
            help_text=None,
            show_copy_text_btn=False,
            config: SimpleConfig,
    ):
        WindowModalDialog.__init__(self, parent, title)
        self.config = config

        vbox = QVBoxLayout()

        qrw = QRCodeWidget(data)
        qr_hbox = QHBoxLayout()
        qr_hbox.addWidget(qrw)
        qr_hbox.addStretch(1)
        vbox.addLayout(qr_hbox)

        help_text = data if show_text else help_text
        if help_text:
            qr_hbox.setContentsMargins(0, 0, 0, 44)
            text_label = WWLabel()
            text_label.setText(help_text)
            vbox.addWidget(text_label)
        hbox = QHBoxLayout()
        hbox.addStretch(1)

        def print_qr():
            filename = getSaveFileName(
                parent=self,
                title=_("Select where to save file"),
                filename="qrcode.png",
                config=self.config,
            )
            if not filename:
                return
            p = qrw.grab()
            p.save(filename, 'png')
            self.show_message(_("QR code saved to file") + " " + filename)

        def copy_image_to_clipboard():
            p = qrw.grab()
            QApplication.clipboard().setPixmap(p)
            self.show_message(_("QR code copied to clipboard"))

        def copy_text_to_clipboard():
            QApplication.clipboard().setText(data)
            self.show_message(_("Text copied to clipboard"))

        b = QPushButton(_("Copy Image"))
        hbox.addWidget(b)
        b.clicked.connect(copy_image_to_clipboard)

        if show_copy_text_btn:
            b = QPushButton(_("Copy Text"))
            hbox.addWidget(b)
            b.clicked.connect(copy_text_to_clipboard)

        b = QPushButton(_("Save"))
        hbox.addWidget(b)
        b.clicked.connect(print_qr)

        b = QPushButton(_("Close"))
        hbox.addWidget(b)
        b.clicked.connect(self.accept)
        b.setDefault(True)

        vbox.addLayout(hbox)
        self.setLayout(vbox)
