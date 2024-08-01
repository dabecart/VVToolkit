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
from dataclasses import dataclass, field, fields 

@dataclass
class ProgramConfig:
    validateCommands : bool = field(default=False)
    colorTheme       : str  = field(default="dark")

class SettingsWindow(QDialog):
    def __init__(self, config : ProgramConfig, parent = None):
        super().__init__(parent)
        self.parentWindow = parent

        self.setWindowTitle('Settings')
        self.resize(300, 200)

        parentGeo = self.parentWindow.geometry()
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

        colorThemeLayout = QHBoxLayout()

        # Dark and light theme buttons
        self.darkTheme = QPushButton("Dark")
        self.darkTheme.clicked.connect(self.changeToDarkTheme)
        self.lightTheme = QPushButton("Light")
        self.lightTheme.clicked.connect(self.changeToLightTheme)

        colorThemeLayout.addWidget(self.darkTheme)

        colorThemeLayout.addWidget(self.lightTheme)

        optionsLayout.addRow('Color theme', colorThemeLayout)

        self.validateCommandsCheck = QCheckBox()
        self.validateCommandsCheck.setChecked(config.validateCommands)

        optionsLayout.addRow('Validate input code', self.validateCommandsCheck)

        layout.addLayout(optionsLayout)

        # Add Apply and Cancel buttons
        buttonsLayout = QHBoxLayout()
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.discardChanges)
        self.apply_button = QPushButton('Apply')
        self.apply_button.clicked.connect(self.applyChanges)

        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.cancel_button)
        buttonsLayout.addWidget(self.apply_button)
        
        layout.addLayout(buttonsLayout)
    
        self.setLayout(layout)

    def changeToDarkTheme(self):
        self.config.colorTheme = "dark"
        self.parentWindow.redrawIcons(self.config)

    def changeToLightTheme(self):
        self.config.colorTheme = "light"
        self.parentWindow.redrawIcons(self.config)

    def applyChanges(self):
        self.config.validateCommands = self.validateCommandsCheck.isChecked()

        for field in fields(self.config):
            setattr(self.originalConfig, field.name, getattr(self.config, field.name))
        
        self.parentWindow.redrawIcons(self.config)

        # Close the window.
        self.accept()

    def discardChanges(self):
        self.parentWindow.redrawIcons(self.originalConfig)
        # Close the window.
        self.close()