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
from PyQt6.QtCore import Qt, QSize

from widgets.CollapsibleBox import CollapsibleBox
from widgets.BuildContent import BuildContent, BuildHeader
from DataFields import Item
from tools.ParallelExecution import ParallelLoopExecution, ParallelExecution
from tools.SignalBlocker import SignalBlocker
from tools.UndoRedo import UndoRedo
from widgets.ContainerWidget import ContainerWidget

from Icons import createIcon

from copy import deepcopy
from subprocess import CalledProcessError

class BuildWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.parent = parent

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.runAllButton = QPushButton("Run all")
        self.runAllButton.setStatusTip("Runs all test cases displayed onscreen without output.")
        self.runAllButton.clicked.connect(lambda: self.runAction('run-all-items', None))
        self.runAllButton.setFixedWidth(120)
        self.runAllButton.setFixedHeight(30)
        self.runAllButton.setIconSize(QSize(20,20))

        self.clearAllButton = QPushButton("Clear all")
        self.clearAllButton.setStatusTip("Clears the outputs of all test cases.")
        self.clearAllButton.clicked.connect(lambda: self.runAction('clear-all-items', None))
        self.clearAllButton.setFixedWidth(120)
        self.clearAllButton.setFixedHeight(30)
        self.clearAllButton.setIconSize(QSize(20,20))

        self.categoryCombo = QComboBox()
        self.categoryCombo.setStatusTip("Select the category to filter the test cases.")
        self.categoryCombo.addItem('All categories')
        self.categoryCombo.setFixedHeight(30)
        self.categoryCombo.setMinimumContentsLength(25)
        self.categoryCombo.currentTextChanged.connect(lambda: self.populateTable(self.categoryCombo.currentText()))

        self.showDisabled = False
        self.showHideDisabledButton = QPushButton("")
        self.showHideDisabledButton.setStatusTip("Hide or show disabled test cases.")
        self.showHideDisabledButton.setFixedHeight(30)
        self.showHideDisabledButton.clicked.connect(self.showHideDisabledButtonClicked)

        icons = [
            [self.runAllButton,             ':run'],
            [self.clearAllButton,           ':clear'],
            [self.showHideDisabledButton,   ':build-show']
        ]
        for widg in icons:
            newIcon = createIcon(widg[1], self.parent.config)
            newIcon.setAssociatedWidget(widg[0])
            widg[0].setIcon(newIcon)

        self.topBar = ContainerWidget()
        topBarLayout = QHBoxLayout(self.topBar)
        topBarLayout.addWidget(self.runAllButton)
        topBarLayout.addWidget(self.clearAllButton)
        topBarLayout.addStretch()
        topBarLayout.addWidget(self.categoryCombo)
        topBarLayout.addWidget(self.showHideDisabledButton)

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

    def showHideDisabledButtonClicked(self):
        self.showDisabled = not self.showDisabled
        self.populateTable(self.categoryCombo.currentText())

        if self.showDisabled :
            newIcon = createIcon(':build-hide', self.parent.config)
        else:
            newIcon = createIcon(':build-show', self.parent.config)

        newIcon.setAssociatedWidget(self.showHideDisabledButton)
        self.showHideDisabledButton.setIcon(newIcon)

    def populateTable(self, categoryFilter: str | None):
        # Delete all widgets if there are new items or if they are updated. 
        # This is a safety measure for the order and content of the widgets.
        itemsThatShouldBeShown = []
        for item in self.parent.items:
            # If a category filter is being given, check that the item belongs to the shown 
            # category.
            if categoryFilter is not None and not self._filterItemByCategory(item, categoryFilter):
                continue
            # Pass of the disabled items if the visualization of disabled items is disabled.
            if not self.showDisabled and not item.enabled:
                continue
            itemsThatShouldBeShown.append(item)

        shownWidgets = []
        shownItems = []
        for i in range(self.scrollLayout.count()):
            widget = self.scrollLayout.itemAt(i).widget()
            shownWidgets.append(widget)
            shownItems.append(widget.item)
        
        # If the list aren't the same length, there are more or less items shown than there are items
        # to be shown, therefore, update the GUI.
        if len(itemsThatShouldBeShown) == len(shownWidgets):
            allFound = True
            for it in itemsThatShouldBeShown:
                # Update if an item to be shown is not already shown.
                if it not in shownItems:
                    allFound = False
                    break

                # Find the widget associated with this item. Check if its fields are updated.
                for wid in shownWidgets:
                    if it is wid.item:
                        if not wid.isUpdated():
                            allFound = False
                        break

                if not allFound: break

            if allFound: return
        
        # Remove all items.
        for i in reversed(range(self.scrollLayout.count())): 
            self.scrollLayout.itemAt(i).widget().setParent(None)
        
        # Add all items in order.
        self.parent.items.sort()
        categoriesList = []
        for item in self.parent.items:
            # Filter if the item is enabled or not and showDisabled is set.
            if self.showDisabled or (not self.showDisabled and item.enabled):
                # Filter by category.
                if categoryFilter is None or self._filterItemByCategory(item, categoryFilter):
                    self.scrollLayout.addWidget(CollapsibleBox(':logo', item, self.parent.config, BuildHeader, BuildContent, self))
            if item.category not in categoriesList:
                categoriesList.append(item.category)

        # If no category is given, populate the category combo.
        if categoryFilter is None:
            with SignalBlocker(self.categoryCombo):
                self.categoryCombo.clear()
                self.categoryCombo.addItem('All categories')
                self.categoryCombo.addItems(categoriesList)

    def _filterItemByCategory(self, item: Item, categoryFilter: str) -> bool:
        match categoryFilter:
            case 'All categories':
                return True
            case _:
                return item.category == categoryFilter

    def runAction(self, action: str, actionStack: str | None, *args):
        def onException(e: Exception):
            detailMessage = "Details:\n"
            if type(e) is CalledProcessError:
                detailMessage += "Command arguments: "
                for arg in e.cmd:
                    detailMessage += str(arg) + " "
                detailMessage += f'\nReturn code: {e.returncode}\nError output: {e.stderr.decode("utf-8")}'
            else:
                detailMessage += str(e)
            
            QMessageBox.critical(self, 'Fatal error while running test', 
                    f'A fatal error occurred. {detailMessage}')
            
            onFinishRun()
        
        def onFinishRun():
            self.topBar.setEnabled(True)
            self.parent.setEnableToolbars(True)

        def updateFieldsAfterRun(args):
            content: BuildContent = args
            item: Item = content.item

            content.outputCmdText.setText(item.result[0].output)
            content.outputReturnValue.setText(f"Return: {item.result[0].returnCode}\nExecution time: {item.result[0].executionTime:.2f} ms")
            content.outputCmdIndexCombo.setPlaceholderText("None")
            content.outputCmdIndexCombo.setCurrentIndex(0)
            content.outputCmdIndexCombo.setEnabled(True)
            self.parent.statusBar.showMessage(f"Item {item.id} successfully run.", 3000)

        if action == 'run-item':
            content: BuildContent = args[0]
            item: Item = content.item

            if not item.enabled or item.repetitions <= 0:
                return

            if item.hasBeenRun():
                QMessageBox.critical(None, 'Error', f'Item {item.id}: \"{item.name}\" contains results and/or configuration.\nPlease, clear it before running it again.')
                return

            self.topBar.setEnabled(False)
            self.parent.setEnableToolbars(False)
            content.outputCmdIndexCombo.setPlaceholderText("Running...")
            content.outputCmdIndexCombo.setCurrentIndex(-1)
            content.outputCmdIndexCombo.setEnabled(False)

            def singleRunFinishFunction():
                updateFieldsAfterRun(content)
                onFinishRun()

            self.pex = ParallelExecution(lambda: content.item.run(), singleRunFinishFunction, onException)
            self.pex.run()

        elif action == 'run-all-items':
            boxes = []
            for i in range(self.scrollLayout.count()):
                content: BuildContent = self.scrollLayout.itemAt(i).widget().content
                # Only run those that are enabled and are shown on screen.
                if content.item.isEnabled() and self._filterItemByCategory(content.item, self.categoryCombo.currentText()):
                    boxes.append(content)
            
            self.topBar.setEnabled(False)
            self.parent.setEnableToolbars(False)
            for args in boxes:
                args.outputCmdIndexCombo.setPlaceholderText("Running...")
                args.outputCmdIndexCombo.setCurrentIndex(-1)
                args.outputCmdIndexCombo.setEnabled(False)

            self.pex = ParallelLoopExecution(boxes, lambda args: args.item.run(), updateFieldsAfterRun, onFinishRun, onException)
            self.pex.run()

        elif action == 'clear-item':
            content: BuildContent = args[0]
            item: Item = content.item

            if not item.enabled:
                return
            
            if actionStack is not None:
                resultsCopy = deepcopy(item.result)

            item.result.clear()
            content.outputReturnValue.clear()
            content.outputCmdText.clear()
            content.outputCmdIndexCombo.setCurrentIndex(-1)
            content.outputCmdIndexCombo.setEnabled(False)

        elif action == 'clear-all-items':
            reply = QMessageBox.question(self, 'Clear all items?',
                                        'You will clear all outputs.\nAre you sure about it?',
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.No:
                return
            
            for i in range(self.scrollLayout.count()):
                content = self.scrollLayout.itemAt(i).widget().content
                # Only clean those shown on screen.
                if self._filterItemByCategory(content.item, self.categoryCombo.currentText()):
                    self.runAction('clear-item', None, content) 

        elif action == 'populate-table':
            self.populateTable(args[0])

        elif action == 'set-results':
            item: Item = args[0].item
            item.result = args[1]
            updateFieldsAfterRun([args[0], self])

        if actionStack is not None:
            if action == 'run-item' or action == 'set-results':
                UndoRedo.addAction(actionStack, ('clear-item', args[0]))
            elif action == 'clear-item':
                UndoRedo.addAction(actionStack, ('set-results', args[0], resultsCopy))