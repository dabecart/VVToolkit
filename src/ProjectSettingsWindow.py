# **************************************************************************************************
# @file ProjectSettingsWindow.py
# @brief Little popup window to configure the project settings.
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-10
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QDialog, QPushButton, QLineEdit
)
from DataFields import TestDataFields

class ProjectSettingsWindow(QDialog):
    def __init__(self, testDataFields: TestDataFields, readOnly: bool, parent = None):
        super().__init__(parent)
        self.parentWindow = parent
        self.dataFields = testDataFields

        self.setWindowTitle('Project Settings')
        self.resize(300, 200)

        parentGeo = self.parentWindow.geometry()
        childGeo = self.geometry()
        self.move(
            parentGeo.center().x() - childGeo.width() // 2,
            parentGeo.center().y() - childGeo.height() // 2
        )
        
        layout = QVBoxLayout()

        formLayout = QFormLayout()
        layout.addLayout(formLayout)

        self.nameField = QLineEdit()
        self.nameField.setStatusTip('Set the name for this test file.')
        self.nameField.setText(self.dataFields.name)
        self.nameField.setDisabled(readOnly)
        formLayout.addRow("Name:", self.nameField)

        self.projectField = QLineEdit()
        self.projectField.setStatusTip('Set the name of the project.')
        self.projectField.setText(self.dataFields.project)
        self.projectField.setDisabled(readOnly)
        formLayout.addRow("Project:", self.projectField)

        self.authorField = QLineEdit()
        self.authorField.setStatusTip('Set the name of the author of this test file.')
        self.authorField.setText(self.dataFields.author)
        self.authorField.setDisabled(readOnly)
        formLayout.addRow("Author:", self.authorField)

        self.conductorField = QLineEdit()
        self.conductorField.setStatusTip('Set the name of the person conducting this test.')
        self.conductorField.setText(self.dataFields.conductor)
        self.conductorField.setDisabled(readOnly)
        formLayout.addRow("Conductor:", self.conductorField)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch()
        if readOnly:
            okButton = QPushButton('Ok')
            okButton.clicked.connect(self.close)
            buttonsLayout.addWidget(okButton)
        else:
            # Add Apply and Cancel buttons
            cancelButton = QPushButton('Cancel')
            cancelButton.clicked.connect(self.discardChanges)
            applyButton = QPushButton('Apply')
            applyButton.setDefault(True)
            applyButton.clicked.connect(self.applyChanges)

            buttonsLayout.addWidget(cancelButton)
            buttonsLayout.addWidget(applyButton)
        
        layout.addLayout(buttonsLayout)
    
        self.setLayout(layout)

    def applyChanges(self):
        self.dataFields.name = self.nameField.text()
        self.dataFields.project = self.projectField.text()
        self.dataFields.author = self.authorField.text()
        self.dataFields.conductor = self.conductorField.text()

        # Close the window.
        self.accept()

    def discardChanges(self):
        # Close the window.
        self.close()