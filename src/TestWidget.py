# **************************************************************************************************
# @file TestWidget.py
# @brief The test mode interface. Runs all testcases and compares them with the output generated on
# build mode.
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-04
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt

from widgets.CollapsibleBox import CollapsibleBox
from widgets.TestContent import TestContent, TestHeader
from DataFields import Item, TestResult
from tools.ParallelExecution import ParallelLoopExecution, ParallelExecution
from tools.SignalBlocker import SignalBlocker

from Icons import createIcon

from typing import List
from copy import deepcopy

class TestWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.parent = parent
        self.currentTest : List[Item] = []

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.topBar = QWidget()
        topBarLayout = QHBoxLayout(self.topBar)

        self.runAllButton = QPushButton(createIcon(':run', self.parent.config), "Run all")
        self.runAllButton.setStatusTip("Starts the testing process.")
        self.runAllButton.clicked.connect(lambda : self.runAction('run-all-tests', None))
        self.runAllButton.setFixedHeight(30)

        self.clearAllButton = QPushButton(createIcon(':clear', self.parent.config), "Clear all")
        self.clearAllButton.setStatusTip("Clears this test.")
        self.clearAllButton.clicked.connect(lambda : self.runAction('clear-all-tests', None))
        self.clearAllButton.setFixedHeight(30)

        self.categoryCombo = QComboBox()
        self.categoryCombo.setStatusTip("Select the category to filter the test results.")
        self.categoryCombo.setPlaceholderText("Categories")
        self.categoryCombo.setCurrentIndex(-1)
        self.categoryCombo.addItem('All categories')
        self.categoryCombo.addItem('Only OK')
        self.categoryCombo.addItem('Only ERROR')
        self.categoryCombo.setFixedHeight(30)
        self.categoryCombo.setMinimumContentsLength(25)
        self.categoryCombo.setEnabled(False)
        self.categoryCombo.currentTextChanged.connect(lambda: self.populateTable(self.categoryCombo.currentText()))

        topBarLayout.addWidget(self.runAllButton)
        topBarLayout.addWidget(self.clearAllButton)
        topBarLayout.addStretch()
        topBarLayout.addWidget(self.categoryCombo)

        layout.addWidget(self.topBar)

        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        layout.addWidget(scrollArea)

        self.scrollContent = QWidget()
        scrollArea.setWidget(self.scrollContent)
        self.scrollLayout = QVBoxLayout(self.scrollContent)
        self.scrollLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def populateTable(self, categoryFilter):
        if not self.currentTest:
            return

        # Remove all items.
        for i in reversed(range(self.scrollLayout.count())): 
            self.scrollLayout.itemAt(i).widget().setParent(None)
        
        # Add all items in order.
        self.currentTest.sort()
        for item in self.currentTest:
            if not item.enabled:
                continue

            if self._filterItemByCategory(item, categoryFilter):
                icon = self._getIconFromItem(item)
                if icon is None:
                    print(f"Missing test result for item {item.id}")
                    continue
                self.scrollLayout.addWidget(CollapsibleBox(icon, item, self.parent.config, TestHeader, TestContent, self))

    def _getIconFromItem(self, item : Item) -> str:
        match item.testResult:
            case TestResult.OK:
                return ':test-ok'
            case TestResult.ERROR:
                return ':test-error'
            case TestResult.UNDEFINED:
                return ':test-undefined'
            case _:
                return None

    def _filterItemByCategory(self, item : Item, categoryFilter : str) -> bool:
        match categoryFilter:
            case 'All categories':
                return True
            case 'Only OK':
                return item.testResult == TestResult.OK
            case 'Only ERROR':
                return item.testResult == TestResult.ERROR
            case _:
                return item.category == categoryFilter

    def runAction(self, action, actionStack, *args):
        def onFinishRun(args):
            args.topBar.setEnabled(True)
            self.parent.setEnableToolbars(True)
            with SignalBlocker(self.categoryCombo):
                self.categoryCombo.setEnabled(True)
                self.categoryCombo.setPlaceholderText("Categories")
                self.categoryCombo.setCurrentIndex(0)

        def updateFieldsAfterRun(args):
            item : Item = args[0]
            testW : TestWidget = args[1]

            icon = self._getIconFromItem(item)
            if icon is None:
                print(f"Missing test result for item {item.id}")
                return
            
            testW.scrollLayout.addWidget(CollapsibleBox(icon, item, testW.parent.config, TestHeader, TestContent, testW))
            testW.parent.statusBar.showMessage(f"Item {item.id} successfully run.", 3000)
            # Add the category to the combo if its not already inside.
            if testW.categoryCombo.findText(item.category) == -1:
                testW.categoryCombo.addItem(item.category)

        if action == 'run-all-tests':
            funcArg = []
            if not self.currentTest:
                self.currentTest = deepcopy(self.parent.items)

            for it in self.currentTest:
                # Run only tests without results or with wrong results and test that are enabled.
                if it.enabled and it.testResult != TestResult.OK:
                    funcArg.append([it, self])
            
            if funcArg:
                self.parent.statusBar.showMessage(f"Started running {len(funcArg)} tests.", 3000)
            else:
                self.parent.statusBar.showMessage("Nothing to run.", 3000)
                return

            self.topBar.setEnabled(False)
            self.parent.setEnableToolbars(False)
            with SignalBlocker(self.categoryCombo):
                self.categoryCombo.setPlaceholderText("Running...")
                self.categoryCombo.setCurrentIndex(-1)
                self.categoryCombo.setEnabled(False)

            self.pex = ParallelLoopExecution(funcArg, lambda args: args[0].test(), lambda args: updateFieldsAfterRun(args), lambda : onFinishRun(self))
            self.pex.run()

        elif action == 'clear-all-tests':
            reply = QMessageBox.question(self, 'Clear all tests?',
                                        'You will clear all test results.\nAre you sure about it?',
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.No:
                return
            
            # Remove all items.
            for i in reversed(range(self.scrollLayout.count())): 
                self.scrollLayout.itemAt(i).widget().setParent(None)
            
            if self.currentTest:
                self.currentTest.clear()

            self.categoryCombo.setCurrentIndex(-1)
            self.categoryCombo.setEnabled(False)

        elif action == 'rerun-test':
            # This item belongs to the self.currentTest (from the deep copy).
            rerunBox : CollapsibleBox = args[0]
            rerunItem : Item = rerunBox.item

            # Disable the box.
            rerunBox.setEnabled(False)

            # Clear the test results.
            rerunItem.clearTest()

            self.topBar.setEnabled(False)
            self.parent.setEnableToolbars(False)
            with SignalBlocker(self.categoryCombo):
                self.categoryCombo.setPlaceholderText("Running...")
                self.categoryCombo.setCurrentIndex(-1)
                self.categoryCombo.setEnabled(False)

            def updateBoxAfterRun(args):
                rerunBox : CollapsibleBox = args[0]
                item : Item = rerunBox.item
                testW : TestWidget = args[1]

                icon = self._getIconFromItem(item)
                if icon is None:
                    print(f"Missing test result for item {item.id}")
                    return
                
                positionOfOldBox = testW.scrollLayout.indexOf(rerunBox)
                oldBox = testW.scrollLayout.takeAt(positionOfOldBox).widget()
                oldBox.deleteLater()

                testW.scrollLayout.insertWidget(positionOfOldBox, CollapsibleBox(icon, item, testW.parent.config, TestHeader, TestContent, testW))
                testW.parent.statusBar.showMessage(f"Item {item.id} successfully run.", 3000)
                # Add the category to the combo if its not already inside.
                if testW.categoryCombo.findText(item.category) == -1:
                    testW.categoryCombo.addItem(item.category)
                
                # Reenable all the GUI elements.
                onFinishRun(testW)

            self.pex = ParallelExecution(lambda: rerunItem.test(), lambda: updateBoxAfterRun([rerunBox, self]))
            self.pex.run()

        elif action == 'populate-table':
                self.populateTable(None)