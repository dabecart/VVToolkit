# **************************************************************************************************
# @file TestContent.py
# @brief Content and header of the CollapsibleBox for the test mode. 
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-04
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QComboBox, QPushButton, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QPixmap, QColor, QIcon, QStandardItem, QStandardItemModel

from DataFields import Item
from widgets.CodeTextField import CodeTextField
from widgets.ContainerWidget import ContainerWidget
from DataFields import TestResult

from Icons import createIcon

class TestContent(QWidget):
    def __init__(self, item : Item, parent = None) -> None:
        super().__init__(parent)

        self.item = item
        self.parent = parent

        contentLayout = QVBoxLayout(self)
        contentLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        inputCommandLabel = QLabel("Input:")
        self.inputCmdText = CodeTextField()
        self.inputCmdText.setReadOnly(True)
        self.inputCmdText.setText(self.item.runcode)
        self.inputCmdText.setStatusTip("The code that runs for this test case.")
        
        self.outputCmdIndexCombo = QComboBox()
        self.outputCmdIndexCombo.setStatusTip("Select which of the iterations to show.")
        self.outputCmdIndexCombo.setPlaceholderText("None")
        self.outputCmdIndexCombo.setMinimumHeight(30)
        self.outputCmdIndexCombo.setMinimumWidth(self.outputCmdIndexCombo.sizeHint().width() + 16)

        # Add a little colored dot along with the output number to signal the output result.
        ouputCmdIndexComboContent = [(str(i), self.item.testOutput[i].result) for i in range(self.item.repetitions)]
        model = QStandardItemModel(self.outputCmdIndexCombo)
        for text, result in ouputCmdIndexComboContent:
            color = QColor(TestResult.getResultColor(result))

            # Create a pixmap with a colored dot.
            pixmap = QPixmap(20, 20)
            pixmap.fill(QColor("transparent"))

            painter = QPainter(pixmap)
            painter.setBrush(color)
            painter.setPen(color)
            painter.drawEllipse(3, 3, 14, 14)
            painter.end()

            # Create the QStandardItem with the icon and text.
            model.appendRow(QStandardItem(QIcon(pixmap), text))
        
        self.outputCmdIndexCombo.setModel(model)
        
        if self.item.hasBeenRun():
            self.outputCmdIndexCombo.setCurrentIndex(0)
        else:
            self.outputCmdIndexCombo.setCurrentIndex(-1)
            self.outputCmdIndexCombo.setEnabled(False)
        self.outputCmdIndexCombo.currentTextChanged.connect(self.onOutputCmdIndexChanged)

        rerunStr = ""
        if self.item.wasTestRepeated > 0:
            plural = "s" if self.item.wasTestRepeated>1 else ""
            rerunStr = f"This test was repeated {self.item.wasTestRepeated} time{plural}."
        checkModeLabel = QLabel(f"Checking Mode: {self.item.validationCmd.validationToString(self.item.testResult)} {rerunStr}")

        # Visual separator (horizontal line).
        horizontalSeparator = QFrame(self)
        horizontalSeparator.setFrameShape(QFrame.Shape.HLine)
        horizontalSeparator.setFrameShadow(QFrame.Shadow.Sunken)

        testOutputCommandLabel = QLabel("Test output:")
        self.testOutputReturnValue = QLabel("")

        testOutputHeader = ContainerWidget()
        testOutputHeaderLayout = QHBoxLayout(testOutputHeader)
        testOutputHeaderLayout.setContentsMargins(0,0,0,0)
        testOutputHeaderLayout.addWidget(testOutputCommandLabel)
        testOutputHeaderLayout.addWidget(self.outputCmdIndexCombo)
        testOutputHeaderLayout.addStretch()
        testOutputHeaderLayout.addWidget(self.testOutputReturnValue)

        self.testOutputCmdText = QTextEdit()
        self.testOutputCmdText.setStatusTip('The output generated by this test case.')
        self.testOutputCmdText.setReadOnly(True)

        self.testOutputCmdValidation = QLabel()

        contentLayout.addWidget(inputCommandLabel)
        contentLayout.addWidget(self.inputCmdText)
        contentLayout.addWidget(checkModeLabel)
        contentLayout.addWidget(horizontalSeparator)
        contentLayout.addWidget(testOutputHeader)
        contentLayout.addWidget(self.testOutputCmdText)
        contentLayout.addWidget(self.testOutputCmdValidation)

        if self.item.validationCmd.usesBuildOutput():
            outputCommandLabel = QLabel("Original output:")
            self.outputReturnValue = QLabel("")

            outputHeader = ContainerWidget()
            outputHeaderLayout = QHBoxLayout(outputHeader)
            outputHeaderLayout.setContentsMargins(0,0,0,0)
            outputHeaderLayout.addWidget(outputCommandLabel)
            outputHeaderLayout.addStretch()
            outputHeaderLayout.addWidget(self.outputReturnValue)

            self.outputCmdText = QTextEdit()
            self.outputCmdText.setStatusTip('The original output generated by this test case.')
            self.outputCmdText.setReadOnly(True)

            contentLayout.addWidget(outputHeader)
            contentLayout.addWidget(self.outputCmdText)

        # Populate the test output boxes.
        self.updateReturnValues(0)

    def updateReturnValues(self, index):
        # This will update the text on the output commands and the result.
        if self.item.hasBeenTested():
            self.testOutputCmdText.setText(self.item.testOutput[index].output)
            self.testOutputReturnValue.setText(f"Return: {self.item.testOutput[index].returnCode}\nExecution time: {self.item.testOutput[index].executionTime:.2f} ms")
            self.testOutputCmdValidation.setText(f"Test results: {self.item.validationCmd.resultToString(self.item.testOutput[index].result)}")

        if self.item.validationCmd.usesBuildOutput() and self.item.hasBeenRun():
            self.outputCmdText.setText(self.item.result[index].output)
            self.outputReturnValue.setText(f"Return: {self.item.result[index].returnCode}\nExecution time: {self.item.result[index].executionTime:.2f} ms")

    def isUpdated(self):
        # Legacy code to match BuildContent.py
        return True
    
    def onOutputCmdIndexChanged(self, text):
        try:
            index = int(text)
        except ValueError:
            return
        
        self.updateReturnValues(index)

class TestHeader(QWidget):
    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        # CollapsibleBox type.
        self.parent = parent

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        self.refreshButton = QPushButton(self)
        self.refreshButton.setStatusTip('Repeats this test case.')
        self.refreshButton.setIcon(createIcon(':test-refresh', self.parent.config))
        self.refreshButton.setFixedSize(35, 35)
        self.refreshButton.setIconSize(QSize(30,30))
        self.refreshButton.clicked.connect(lambda : self.parent.parent.runAction('rerun-test', 'undo', self.parent))

        layout.addWidget(self.refreshButton)
