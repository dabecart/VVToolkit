# **************************************************************************************************
# @file CollapsibleBox.py
# @brief A simple widget/accordion that can be collapsed. 
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-02
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QComboBox, QLineEdit, QPushButton)
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import Qt, QPropertyAnimation, QAbstractAnimation, QSize

from DataFields import Item
from widgets.CodeTextField import CodeTextField
from Icons import createIcon

class CollapsibleBox(QWidget):
    def __init__(self, iconName : str, item : Item, config, parent=None):
        super().__init__(parent)

        self.item = item
        self.config = config
        self.parent = parent

        self.header = QWidget()
        self.header.setObjectName('header')
        self.headerLayout = QHBoxLayout(self.header)

        self.arrowLabel = QLabel()
        self.arrowLabel.setPixmap(createIcon(':arrow-right', self.config).pixmap(15,15))
        self.arrowLabel.setFixedWidth(15)
        self.iconLabel = QLabel()
        self.iconLabel.setPixmap(createIcon(iconName).pixmap(24, 24))
        self.idLabel = QLabel(str(item.id))
        self.nameLabel = QLabel(item.name)

        self.runButton = QPushButton(self)
        self.runButton.setIcon(createIcon(':run', self.config))
        self.runButton.setFixedSize(35, 35)
        self.runButton.setIconSize(QSize(30,30))
        self.runButton.clicked.connect(lambda : self.parent.runAction('run-item', None, self))

        self.clearButton = QPushButton(self)
        self.clearButton.setIcon(createIcon(':clear', self.config))
        self.clearButton.setFixedSize(35, 35)
        self.clearButton.setIconSize(QSize(30,30))
        self.clearButton.clicked.connect(lambda : self.parent.runAction('clear-item', None, self))

        self.headerLayout.addWidget(self.arrowLabel)
        self.headerLayout.addWidget(self.iconLabel)
        self.headerLayout.addWidget(self.idLabel)
        self.headerLayout.addWidget(self.nameLabel)
        self.headerLayout.addStretch()
        self.headerLayout.addWidget(self.clearButton)
        self.headerLayout.addWidget(self.runButton)

        self.header.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 50);
            }
        """)

        self.header.mousePressEvent = self.toggle_content

        self.content = QWidget()
        self.contentLayout = QVBoxLayout(self.content)
        self.contentLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        inputCommandLabel = QLabel("Input:")
        inputCmdText = CodeTextField()
        inputCmdText.setText(self.item.runcode)
        inputCmdText.setReadOnly(True)
        outputCommandLabel = QLabel("Output:")
        self.outputCmdText = QTextEdit()
        self.outputCmdText.setReadOnly(True)

        checkModeLabel = QLabel("Checking Mode:")
        self.checkModeCombo = QComboBox()
        self.checkModeCombo.addItems(["Same output", "Conditional output"])
        self.checkModeCombo.currentTextChanged.connect(self.on_checking_mode_changed)

        self.operatorCombo = QComboBox()
        self.operatorCombo.addItems(["==", "<>", "<", ">", "<=", ">="])
        self.operatorCombo.setVisible(False)

        self.operatorValueEdit = QLineEdit()
        self.operatorValueEdit.setVisible(False)

        checkModeWidget = QWidget()
        checkModeLayout = QHBoxLayout(checkModeWidget)
        checkModeLayout.addWidget(checkModeLabel)
        checkModeLayout.addWidget(self.checkModeCombo)
        checkModeLayout.addWidget(self.operatorCombo)
        checkModeLayout.addWidget(self.operatorValueEdit)

        self.contentLayout.addWidget(inputCommandLabel)
        self.contentLayout.addWidget(inputCmdText)
        self.contentLayout.addWidget(outputCommandLabel)
        self.contentLayout.addWidget(self.outputCmdText)
        self.contentLayout.addWidget(checkModeWidget)

        self.header.setFixedHeight(self.header.sizeHint().height())

        self.mainWidget = QWidget()
        self.mainWidget.setObjectName('mainName')
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.content)

        self.mainWidget.setLayout(self.main_layout)
        
        self.selfLayout = QVBoxLayout()
        self.selfLayout.addWidget(self.mainWidget)
        self.selfLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.selfLayout)

        # Calculate the animation heights.
        self.content.setVisible(True)
        self.openedHeight = self.mainWidget.sizeHint().height()
        self.content.setVisible(False)
        self.closedHeight = self.mainWidget.sizeHint().height()
        self.mainWidget.setMaximumHeight(self.closedHeight)

        self.animation = QPropertyAnimation(self.mainWidget, b"maximumHeight")
        self.animation.setDuration(250)
        self.animation.finished.connect(self.on_animation_finished)

        midColor = self.palette().color(QPalette.ColorRole.Button)
        midlightColor = midColor.lighter(150)
        self.setStyleSheet(f"""
            #header {{
                background-color: {midlightColor.name()};
                border: 1px solid #ccc;
                padding: 2px;
                border-radius: 4px;
            }}
            #mainName {{
                background-color: {midColor.name()};
                border: 1px solid #ccc;
                border-radius: 4px;
            }}
        """)
    
    def isUpdated(self):
        return (self.idLabel.text() == str(self.item.id)) and (self.nameLabel.text() == self.item.name)

    def toggle_content(self, event):
        if self.animation.state() == QAbstractAnimation.State.Running:
            return
        
        if self.content.isVisible():
            # Close the window.
            self.arrowLabel.setPixmap(createIcon(':arrow-right', self.config).pixmap(15,15))
            self.animation.setStartValue(self.openedHeight)
            self.animation.setEndValue(self.closedHeight)
            self.animation.start()
        else:
            # Open the window.
            self.arrowLabel.setPixmap(createIcon(':arrow-down', self.config).pixmap(15,15))
            self.content.setVisible(True)
            self.animation.setStartValue(self.closedHeight)
            self.animation.setEndValue(self.openedHeight)
            self.animation.start()

    def on_animation_finished(self):
        # Hide the content once the animation finishes.
        if self.animation.endValue() == self.closedHeight:
            self.content.setVisible(False)

    def on_checking_mode_changed(self, text):
        if text == "Conditional output":
            self.operatorCombo.setVisible(True)
            self.operatorValueEdit.setVisible(True)
            self.mainWidget.setMaximumHeight(self.mainWidget.sizeHint().height())
        else:
            self.operatorCombo.setVisible(False)
            self.operatorValueEdit.setVisible(False)
            self.mainWidget.setMaximumHeight(self.openedHeight)