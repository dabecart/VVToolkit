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

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QComboBox, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize

from widgets.CollapsibleBox import CollapsibleBox
from widgets.TestContent import TestContent, TestHeader
from widgets.ContainerWidget import ContainerWidget
from DataFields import Item, TestResult
from tools.ParallelExecution import ParallelLoopExecution, ParallelExecution
from tools.SignalBlocker import SignalBlocker
from widgets.LoadingCircle import LoadingCircle

from Icons import createIcon

from typing import List
from copy import deepcopy
from datetime import datetime

class TestWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.parent = parent
        self.currentTest: List[Item] = []
        self.currentlyRunningTest = False
        self.readOnly = False

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.topBar = ContainerWidget()
        self.topBar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.topBarLayout = QHBoxLayout(self.topBar)

        self.runAllButton = QPushButton("New test")
        icon = createIcon(':run', self.parent.config)
        icon.setAssociatedWidget(self.runAllButton)
        self.runAllButton.setIcon(icon)
        self.runAllButton.setStatusTip("Starts the testing process.")
        self.runAllButton.clicked.connect(lambda: self.runAction('run-all-tests', None))
        self.runAllButton.setFixedWidth(120)
        self.runAllButton.setFixedHeight(30)
        self.runAllButton.setIconSize(QSize(20,20))

        self.clearAllButton = QPushButton("Clear test")
        icon = createIcon(':clear', self.parent.config)
        icon.setAssociatedWidget(self.clearAllButton)
        self.clearAllButton.setIcon(icon)
        self.clearAllButton.setStatusTip("Clears this test.")
        self.clearAllButton.clicked.connect(lambda: self.runAction('clear-all-tests', None))
        self.clearAllButton.setFixedWidth(120)
        self.clearAllButton.setFixedHeight(30)
        self.clearAllButton.setIconSize(QSize(20,20))

        self.categoryCombo = QComboBox()
        self.categoryCombo.setStatusTip("Select the category to filter the test results.")
        self.categoryCombo.setPlaceholderText("Categories")
        self.clearCategoryCombo()
        self.categoryCombo.setFixedHeight(30)
        self.categoryCombo.setMinimumContentsLength(25)
        self.categoryCombo.setEnabled(False)
        self.categoryCombo.currentTextChanged.connect(lambda: self.populateTable(self.categoryCombo.currentText()))

        self.topBarLayout.addWidget(self.runAllButton)
        self.topBarLayout.addWidget(self.clearAllButton)
        self.topBarLayout.addStretch()
        self.topBarLayout.addWidget(self.categoryCombo)

        layout.addWidget(self.topBar)

        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        scrollArea.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(scrollArea)

        self.scrollContent = ContainerWidget()
        scrollArea.setWidget(self.scrollContent)

        self.scrollLayout = QVBoxLayout(self.scrollContent)

        self.scrollLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollLayout.setSpacing(0)
        self.scrollLayout.setContentsMargins(0,0,0,0)

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

            if categoryFilter is None or self._filterItemByCategory(item, categoryFilter):
                icon = self._getIconFromItem(item)
                if icon is None:
                    print(f"Missing test result for item {item.id} on populateTable")
                    continue
                # If set as readOnly, pass a dummy container to not show the rerun button.
                self.scrollLayout.addWidget(
                    CollapsibleBox(icon, item, self.parent.config, 
                                   ContainerWidget if self.readOnly else TestHeader, 
                                   TestContent, self))

    def _getIconFromItem(self, item: Item) -> str:
        match item.testResult:
            case TestResult.OK:
                return ':test-ok'
            case TestResult.ERROR:
                return ':test-error'
            case TestResult.UNDEFINED:
                return ':test-undefined'
            case TestResult.NOT_ALL_OK:
                return ':test-undefined'
            case _:
                return None

    def _filterItemByCategory(self, item: Item, categoryFilter: str) -> bool:
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
        if self.currentlyRunningTest:
            QMessageBox.warning(self, 'Program is currently running tests', 
                    'The program is currently running tests and is busy.\n'
                    'Please, wait till the testing has ended.')
            return

        self.currentlyRunningTest = True

        def onFinishRun(args):
            args.topBar.setEnabled(True)
            self.parent.setEnableToolbars(True)
            with SignalBlocker(self.categoryCombo):
                self.categoryCombo.setEnabled(True)
                self.categoryCombo.setPlaceholderText("Categories")
                self.categoryCombo.setCurrentIndex(0)
            self.currentlyRunningTest = False
            
            # Remove the loading circle from the scroll window.
            widgAtBottomOfScroll = self.scrollLayout.itemAt(self.scrollLayout.count()-1).widget()
            if type(widgAtBottomOfScroll) is LoadingCircle:
                widgAtBottomOfScroll.setParent(None)

            # Remove the LoadingCircle from the upper button bar.
            widgAtTopBar = self.topBarLayout.itemAt(2).widget()
            if type(widgAtTopBar) is LoadingCircle:
                widgAtTopBar.setParent(None)

        def updateFieldsAfterRun(args):
            item: Item = args[0]
            testW: TestWidget = args[1]

            icon = self._getIconFromItem(item)
            if icon is None:
                print(f"Missing test result for item {item.id} on UpdateFieldsAfterRun")
                return
            
            testW.scrollLayout.insertWidget(testW.scrollLayout.count()-1, 
                                            CollapsibleBox(icon, item, testW.parent.config, TestHeader, TestContent, testW))
            testW.parent.statusBar.showMessage(f"Item {item.id} successfully run.", 3000)
            # Add the category to the combo if its not already inside.
            if testW.categoryCombo.findText(item.category) == -1:
                testW.categoryCombo.addItem(item.category)

        if action == 'run-all-tests':
            if self.readOnly:
                self.currentlyRunningTest = False
                return
    
            if self.currentTest:
                reply = QMessageBox.question(self, 'Clear all tests for new test?',
                                            'You are about to begin a new test.\n' 
                                            'For that, you will need to clear the current test results.\n'
                                            'Are you sure you want to CLEAR ALL results for a new test?',
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                            QMessageBox.StandardButton.Yes)
                if reply == QMessageBox.StandardButton.No:
                    self.currentlyRunningTest = False
                    return
                elif reply == QMessageBox.StandardButton.Yes:
                    # This is so it can enter the clear-all function.
                    self.currentlyRunningTest = False
                    self.runAction('clear-all-tests', None, False)
                    self.currentlyRunningTest = True
                else:
                    self.currentlyRunningTest = False
                    return
            
            self.currentTest = deepcopy(self.parent.items)
            funcArg = [[it, self] for it in self.currentTest if it.enabled]

            if funcArg:
                self.parent.statusBar.showMessage(f"Started running {len(funcArg)} tests.", 3000)
            else:
                self.parent.statusBar.showMessage("Nothing to run.", 3000)
                self.currentlyRunningTest = False
                return

            self.parent.projectDataFields.date = datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")
            self.parent.projectDataFields.testCount = len(funcArg)

            # Add loading circle to the right of the two top buttons.
            loadcircle = LoadingCircle(20,20)
            loadcircle.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.topBarLayout.insertWidget(2, loadcircle)

            self.topBar.setEnabled(False)
            self.parent.setEnableToolbars(False)
            with SignalBlocker(self.categoryCombo):
                self.clearCategoryCombo()
                self.categoryCombo.setPlaceholderText("Running...")
                self.categoryCombo.setEnabled(False)

            self.scrollLayout.addWidget(LoadingCircle(60,60))

            self.pex = ParallelLoopExecution(funcArg, lambda args: args[0].test(), lambda args: updateFieldsAfterRun(args), lambda: onFinishRun(self))
            self.pex.run()

        elif action == 'clear-all-tests':
            if self.readOnly:
                self.currentlyRunningTest = False
                return
            
            if len(args) > 0 and args[0]:
                reply = QMessageBox.question(self, 'Clear all tests?',
                                            'You will clear all test results.\nAre you sure about it?',
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                            QMessageBox.StandardButton.Yes)
                if reply == QMessageBox.StandardButton.No:
                    self.currentlyRunningTest = False
                    return
            
            # Remove all items.
            for i in reversed(range(self.scrollLayout.count())): 
                self.scrollLayout.itemAt(i).widget().setParent(None)
            
            if self.currentTest:
                self.currentTest.clear()

            self.categoryCombo.setCurrentIndex(-1)
            self.categoryCombo.setEnabled(False)

            self.currentlyRunningTest = False

        elif action == 'rerun-test':
            if self.readOnly:
                self.currentlyRunningTest = False
                return

            # This item belongs to the self.currentTest (from the deep copy).
            rerunBox: CollapsibleBox = args[0]
            rerunItem: Item = rerunBox.item

            # This item will be set as rerun.
            rerunItem.wasTestRepeated += 1

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
                rerunBox: CollapsibleBox = args[0]
                item: Item = rerunBox.item
                testW: TestWidget = args[1]
                boxWasOpened = rerunBox.content.isVisible()

                icon = self._getIconFromItem(item)
                if icon is None:
                    print(f"Missing test result for item {item.id} on updateBoxAfterRun")
                    return
                
                positionOfOldBox = testW.scrollLayout.indexOf(rerunBox)
                oldBox = testW.scrollLayout.takeAt(positionOfOldBox).widget()
                oldBox.deleteLater()

                newBox = CollapsibleBox(icon, item, testW.parent.config, TestHeader, TestContent, testW)
                if boxWasOpened:
                    newBox.toggleContent(None)

                testW.scrollLayout.insertWidget(positionOfOldBox, newBox)
                testW.parent.statusBar.showMessage(f"Item {item.id} successfully run.", 3000)
                
                # Add the category to the combo if its not already inside.
                if testW.categoryCombo.findText(item.category) == -1:
                    testW.categoryCombo.addItem(item.category)
                
                # Reenable all the GUI elements.
                onFinishRun(testW)

            self.pex = ParallelExecution(lambda: rerunItem.test(), lambda: updateBoxAfterRun([rerunBox, self]))
            self.pex.run()

        elif action == 'populate-table':
            self.currentlyRunningTest = False
            self.populateTable(args[0])

        elif action == 'set-read-only':
            self.currentlyRunningTest = False
            self.readOnly = args[0]
            self.runAllButton.setDisabled(args[0])
            self.clearAllButton.setDisabled(args[0])
            if args[0]:
                with SignalBlocker(self.categoryCombo):
                    self.categoryCombo.setEnabled(True)
                    self.categoryCombo.setCurrentIndex(0)
                    for it in self.currentTest:
                        if self.categoryCombo.findText(it.category) == -1:
                            self.categoryCombo.addItem(it.category)
            else:
                with SignalBlocker(self.categoryCombo):
                    self.clearCategoryCombo()
                    self.categoryCombo.setEnabled(False)

    def clearCategoryCombo(self):
        self.categoryCombo.clear()
        self.categoryCombo.setCurrentIndex(-1)
        self.categoryCombo.addItem('All categories')
        self.categoryCombo.addItem('Only OK')
        self.categoryCombo.addItem('Only ERROR')