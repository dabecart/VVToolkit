# **************************************************************************************************
# @file SettingsWindow.py
# @brief Little popup window to configure the program.
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-01
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QCheckBox, QDialog, QPushButton
)

from widgets.CollapsibleBox import CollapsibleBox

from PyQt6.QtCore import Qt
from dataclasses import dataclass, field, fields 
import qdarktheme
from Icons import TrackableIcon

@dataclass
class ProgramConfig:
    validateCommands: bool = field(default=False)
    colorTheme      : str  = field(default="dark")

class SettingsWindow(QDialog):
    def __init__(self, config: ProgramConfig, parent = None):
        super().__init__(parent)
        self.parent = parent

        self.setWindowTitle('Settings')
        self.resize(300, 200)

        parentGeo = self.parent.geometry()
        childGeo = self.geometry()
        self.move(
            parentGeo.center().x() - childGeo.width() // 2,
            parentGeo.center().y() - childGeo.height() // 2
        )

        # Create a copy of the original config and modify that one. When "Apply" is pressed, pass 
        # the configuration to the original.
        self.originalConfig = config
        self.config = ProgramConfig(**config.__dict__)
        
        layout = QVBoxLayout()

        optionsLayout = QFormLayout()
        layout.addLayout(optionsLayout)

        # Dark and light theme buttons
        self.darkTheme = QPushButton("Dark")
        self.darkTheme.setCheckable(True)
        self.darkTheme.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.darkTheme.clicked.connect(lambda: self.changeTheme("dark"))

        self.lightTheme = QPushButton("Light")
        self.lightTheme.setCheckable(True)
        self.lightTheme.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lightTheme.clicked.connect(lambda: self.changeTheme("light"))

        if self.config.colorTheme == "dark":
            self.darkTheme.setChecked(True)
            self.lightTheme.setChecked(False)
        else:
            self.darkTheme.setChecked(False)
            self.lightTheme.setChecked(True)

        colorThemeLayout = QHBoxLayout()
        colorThemeLayout.addWidget(self.darkTheme)
        colorThemeLayout.addWidget(self.lightTheme)

        self.validateCommandsCheck = QCheckBox()
        self.validateCommandsCheck.setChecked(config.validateCommands)

        optionsLayout.addRow('Color theme', colorThemeLayout)
        optionsLayout.addRow('Validate input code', self.validateCommandsCheck)

        # Add Apply and Cancel buttons
        buttonsLayout = QHBoxLayout()
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.discardChanges)
        self.applyButton = QPushButton('Apply')
        self.applyButton.clicked.connect(self.applyChanges)

        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.cancelButton)
        buttonsLayout.addWidget(self.applyButton)
        
        layout.addLayout(buttonsLayout)
    
        self.setLayout(layout)

    def changeTheme(self, theme):
        self.config.colorTheme = theme

        if self.config.colorTheme == "dark":
            self.darkTheme.setChecked(True)
            self.lightTheme.setChecked(False)
        else:
            self.darkTheme.setChecked(False)
            self.lightTheme.setChecked(True)

        self.applyTheme()

    def applyChanges(self):
        for field in fields(self.config):
            setattr(self.originalConfig, field.name, getattr(self.config, field.name))
        
        self.applyTheme()

        # Close the window.
        self.accept()

    def discardChanges(self):
        for field in fields(self.config):
            setattr(self.config, field.name, getattr(self.originalConfig, field.name))

        self.applyTheme()

        # Close the window.
        self.close()

    def applyTheme(self):
        qdarktheme.setup_theme(self.config.colorTheme)
        TrackableIcon.recolorAllIcons(self.config)
        for collaps in self.parent.findChildren(CollapsibleBox):
            collaps.setStyle()