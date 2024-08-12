# **************************************************************************************************
# @file AboutWindow.py
# @brief Little popup window to show information about this program.
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-10
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

__program_name__ = "Validation and Verification Toolkit"
__version__ = "1.0.0"
__author__ = "@dabecart"

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QDialog, QPushButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap

from Icons import createIcon

class AboutWindow(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parentWindow = parent

        self.setWindowTitle('About')
        self.resize(300, 200)

        parentGeo = self.parentWindow.geometry()
        childGeo = self.geometry()
        self.move(
            parentGeo.center().x() - childGeo.width() // 2,
            parentGeo.center().y() - childGeo.height() // 2
        )
        
        layout = QVBoxLayout()

        contentLayout = QHBoxLayout()
        layout.addLayout(contentLayout)

        logoLabel = QLabel()
        logoLabel.setPixmap(createIcon(':logo', parent.config).pixmap(100,100))
        logoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contentLayout.addWidget(logoLabel)

        textLayout = QVBoxLayout()
        textLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        textLayout.setSpacing(5)
        contentLayout.addLayout(textLayout)

        programLabel    = QLabel(f"<b>{__program_name__}</b>")
        versionLabel    = QLabel(f"Version {__version__}")
        authorLabel     = QLabel(f"Author: {__author__}")
        webpageLabel    = QLabel('Visit the author\'s <a href="https://www.dabecart.net/en/">webpage</a>')
        webpageLabel.setOpenExternalLinks(True)
        githubLabel     = QLabel('... or this project\'s <a href="https://github.com/dabecart/VVToolkit">Github</a>!')
        githubLabel.setOpenExternalLinks(True)

        textLayout.addWidget(programLabel)
        textLayout.addWidget(versionLabel)
        textLayout.addWidget(authorLabel)
        textLayout.addWidget(webpageLabel)
        textLayout.addWidget(githubLabel)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch()
        okButton = QPushButton('Ok')
        okButton.clicked.connect(self.close)
        buttonsLayout.addWidget(okButton)
        
        layout.addLayout(buttonsLayout)
    
        self.setLayout(layout)