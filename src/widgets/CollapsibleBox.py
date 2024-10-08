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

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QGraphicsOpacityEffect)
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt, QPropertyAnimation, QAbstractAnimation

from DataFields import Item
from Icons import createIcon

class CollapsibleBox(QWidget):
    def __init__(self, iconName: str, item: Item, config, contentHeader: type, contentWidget: type, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.item = item
        self.config = config
        self.parent = parent
        self.content = contentWidget(self.item, self)
        self.content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.header = QWidget()
        self.header.setStatusTip('Open this collapsible box.')
        self.header.setObjectName('header')
        self.headerLayout = QHBoxLayout(self.header)

        self.arrowLabel = QLabel()
        icon = createIcon(':arrow-right', self.config)
        icon.setAssociatedWidget(self.arrowLabel)
        self.arrowLabel.setPixmap(icon.pixmap(15,15))
        self.arrowLabel.setFixedWidth(15)

        self.iconLabel = QLabel()
        icon = createIcon(iconName, self.config)
        icon.setAssociatedWidget(self.iconLabel)
        self.iconLabel.setPixmap(icon.pixmap(30, 30))
        
        self.idLabel = QLabel(str(item.id))
        separatorLabel = QLabel("-")
        self.nameLabel = QLabel(item.name)

        self.contentHeader = contentHeader(self)

        self.headerLayout.addWidget(self.arrowLabel)
        self.headerLayout.addWidget(self.iconLabel)
        self.headerLayout.addWidget(self.idLabel)
        self.headerLayout.addWidget(separatorLabel)
        self.headerLayout.addWidget(self.nameLabel)
        self.headerLayout.addStretch()
        self.headerLayout.addWidget(self.contentHeader)

        self.header.setFixedHeight(self.header.sizeHint().height())
        self.header.setStyleSheet("""
            QPushButton {
                border: none;
            }
        """)

        self.header.mousePressEvent = self.toggleContent

        self.mainWidget = QWidget()
        self.mainWidget.setObjectName('mainName')
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.content)
        self.mainWidget.setEnabled(self.item.enabled)

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
        self.animation.finished.connect(self.onAnimationFinished)

        self.setStyle()

        # Fade in on box creation.
        opacityEffect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacityEffect)
        self.fadeAnim = QPropertyAnimation(opacityEffect, b'opacity')
        self.fadeAnim.setStartValue(0)
        self.fadeAnim.setEndValue(1)
        self.fadeAnim.setDuration(500)
        self.fadeAnim.start()

    def setStyle(self):
        midColor: QColor = self.parent.palette().color(QPalette.ColorRole.Window)
        brightness = (midColor.red() * 0.299 + midColor.green() * 0.587 + midColor.blue() * 0.114) / 255
        if brightness < 0.5:
            midColor = midColor.lighter(150)
            midlightColor = midColor.lighter(150)
        else:
            midlightColor = midColor.darker(102) # Not joking but darker() is very broken.
            midColor = midlightColor.darker(102)

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
    
    def toggleContent(self, event):
        if self.animation.state() == QAbstractAnimation.State.Running:
            return
        
        if self.content.isVisible():
            # Close the window.
            self.header.setStatusTip('Open this collapsible box.')
            icon = createIcon(':arrow-right', self.config)
            self.animation.setStartValue(self.openedHeight)
            self.animation.setEndValue(self.closedHeight)
            self.animation.start()
        else:
            # Open the window.
            self.header.setStatusTip('Close this collapsible box.')
            icon = createIcon(':arrow-down', self.config)
            self.content.setVisible(True)
            self.animation.setStartValue(self.closedHeight)
            self.animation.setEndValue(self.openedHeight)
            self.animation.start()

        icon.setAssociatedWidget(self.arrowLabel)
        self.arrowLabel.setPixmap(icon.pixmap(15,15))

    def onAnimationFinished(self):
        # Hide the content once the animation finishes.
        if self.animation.endValue() == self.closedHeight:
            self.content.setVisible(False)

    def isUpdated(self):
        return (self.idLabel.text() == str(self.item.id)) \
                and (self.nameLabel.text() == self.item.name) \
                and self.content.isUpdated() \
                and (self.mainWidget.isEnabled() == self.item.enabled)