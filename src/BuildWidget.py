# **************************************************************************************************
# @file BuildWidget.py
# @brief The build mode interface. Shows all test cases results with pretty accordions and lets you
# run them individually or in bulk.
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-03
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt

from widgets.CollapsibleBox import CollapsibleBox
from DataFields import Item
from tools.ParallelExecution import ParallelLoopExecution
from tools.SignalBlocker import SignalBlocker

from Icons import createIcon

class BuildWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.parent = parent

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.topBar = QWidget()
        topBarLayout = QHBoxLayout(self.topBar)

        self.runAllButton = QPushButton(createIcon(':run', self.parent.config), "Run all")
        self.runAllButton.setToolTip("Runs all test cases without output.")
        self.runAllButton.clicked.connect(lambda : self.runAction('run-all-items', None))
        self.runAllButton.setFixedHeight(30)

        self.clearAllButton = QPushButton(createIcon(':clear', self.parent.config), "Clear all")
        self.clearAllButton.setToolTip("Clears the outputs of all test cases.")
        self.clearAllButton.clicked.connect(lambda : self.runAction('clear-all-items', None))
        self.clearAllButton.setFixedHeight(30)

        self.categoryCombo = QComboBox()
        self.categoryCombo.setToolTip("Select the category to filter the test cases.")
        self.categoryCombo.setCurrentIndex(0)
        self.categoryCombo.setFixedHeight(30)
        self.categoryCombo.currentTextChanged.connect(lambda: self.populateTable(self.categoryCombo.currentText()))

        topBarLayout.addWidget(self.runAllButton)
        topBarLayout.addWidget(self.clearAllButton)
        topBarLayout.addStretch()
        topBarLayout.addWidget(self.categoryCombo)

        layout.addWidget(self.topBar)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        layout.addWidget(self.scrollArea)

        self.scrollContent = QWidget()
        self.scrollArea.setWidget(self.scrollContent)
        self.scrollLayout = QVBoxLayout(self.scrollContent)
        self.scrollLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def populateTable(self, categoryFilter : str | None):
        # Delete all widgets if there are new items or if they are updated. 
        # This is a safety measure for the order and content of the widgets.
        foundAll = True
        for item in self.parent.items:
            found = False
            for i in range(self.scrollLayout.count()):
                widgetItem = self.scrollLayout.itemAt(i).widget()
                if widgetItem.item is item and widgetItem.isUpdated():
                    found = True
                    break
            if not found:
                foundAll = False
                break
        
        if foundAll:
            return
        
        # Remove all items.
        for i in reversed(range(self.scrollLayout.count())): 
            self.scrollLayout.itemAt(i).widget().setParent(None)
        
        # Add all items in order.
        self.parent.items.sort()
        categoriesList = []
        longestSentenceCount = 0
        for item in self.parent.items:
            if categoryFilter is None or self._filterItemByCategory(item, categoryFilter):
                self.scrollLayout.addWidget(CollapsibleBox(':logo', item, self.parent.config, self))
            if item.category not in categoriesList:
                categoriesList.append(item.category)
                if longestSentenceCount < len(item.category):
                    longestSentenceCount = len(item.category)

        # If no category is given, populate the category combo.
        if categoryFilter is None:
            with SignalBlocker(self.categoryCombo):
                self.categoryCombo.clear()
                self.categoryCombo.addItem('All categories')
                self.categoryCombo.addItem('Only enabled')
                self.categoryCombo.addItems(categoriesList)
                self.categoryCombo.setMinimumContentsLength(longestSentenceCount + 10)

    def _filterItemByCategory(self, item : Item, categoryFilter : str) -> bool:
        match categoryFilter:
            case 'All categories':
                return True
            case 'Only enabled':
                return item.enabled
            case _:
                return item.category == categoryFilter


    def runAction(self, action, actionStack, *args):
        def onFinishRun(args):
            args.topBar.setEnabled(True)
            self.parent.setEnableToolbars(True)

        def updateFieldsAfterRun(args):
            box : CollapsibleBox = args[0]
            item : Item = box.item
            buildWidget : BuildWidget = args[1]

            box.outputCmdText.setText(item.result[0].output)
            box.outputReturnValue.setText(f"Return: {item.result[0].returnCode}\nExecution time: {item.result[0].executionTime:.2f} ms")
            box.outputCmdIndexCombo.setPlaceholderText("None")
            box.outputCmdIndexCombo.setCurrentIndex(0)
            box.outputCmdIndexCombo.setEnabled(True)
            buildWidget.parent.statusBar.showMessage(f"Item {item.id} successfully run.", 3000)

        if action == 'run-item':
            box : CollapsibleBox = args[0]
            item : Item = box.item

            if not item.enabled or item.repetitions <= 0:
                return

            if item.hasBeenRun():
                QMessageBox.critical(None, 'Error', f'Item {item.id}: \"{item.name}\" contains results and/or configuration.\nPlease, clear it before running it again.')
                return

            self.topBar.setEnabled(False)
            self.parent.setEnableToolbars(False)
            box.outputCmdIndexCombo.setPlaceholderText("Running...")
            box.outputCmdIndexCombo.setCurrentIndex(-1)
            box.outputCmdIndexCombo.setEnabled(False)

            runArgs = [[box, self]]
            self.pex = ParallelLoopExecution(runArgs, lambda args: args[0].item.run(), lambda args: updateFieldsAfterRun(args), lambda : onFinishRun(self))
            self.pex.run()

        elif action == 'run-all-items':
            boxes = []
            for i in range(self.scrollLayout.count()):
                widget : CollapsibleBox = self.scrollLayout.itemAt(i).widget()
                if widget.item.enabled and widget.item.repetitions > 0:
                    boxes.append([widget, self])
            
            self.topBar.setEnabled(False)
            self.parent.setEnableToolbars(False)
            for args in boxes:
                box = args[0]
                box.outputCmdIndexCombo.setPlaceholderText("Running...")
                box.outputCmdIndexCombo.setCurrentIndex(-1)
                box.outputCmdIndexCombo.setEnabled(False)

            self.pex = ParallelLoopExecution(boxes, lambda args: args[0].item.run(), lambda args: updateFieldsAfterRun(args), lambda : onFinishRun(self))
            self.pex.run()

        elif action == 'clear-item':
            box : CollapsibleBox = args[0]
            item : Item = box.item

            if not item.enabled:
                return
            
            item.result.clear()
            box.outputReturnValue.clear()
            box.outputCmdText.clear()
            box.outputCmdIndexCombo.setCurrentIndex(-1)
            box.outputCmdIndexCombo.setEnabled(False)

        elif action == 'clear-all-items':
            reply = QMessageBox.question(self, 'Clear all items?',
                                        'You will clear all outputs.\nAre you sure about it?',
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.No:
                return
            
            for i in range(self.scrollLayout.count()):
                self.runAction('clear-item', actionStack, self.scrollLayout.itemAt(i).widget()) 

        elif action == 'populate-table':
                self.populateTable(None)