# **************************************************************************************************
# @file SetupWidget.py
# @brief The window widget shown during SETUP mode.
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
    QTableWidget, QCheckBox, QVBoxLayout, QWidget, QHeaderView,
    QLabel, QFormLayout, QSplitter, QHBoxLayout, QPushButton, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QIntValidator

from copy import deepcopy
from typing import Optional

from DataFields import Item

from tools.UndoRedo import UndoRedo
from widgets.LabeledEditLine import LabeledLineEdit
from widgets.CodeTextField import CodeTextField
from widgets.TableCell import TableCell

from Icons import createIcon
from tools.SignalBlocker import SignalBlocker

class SetupWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create the main splitter
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(self.splitter)

        # Create a widget for the buttons
        buttonWidget = QWidget()
        buttonLayout = QHBoxLayout(buttonWidget)

        self.addButton = QPushButton(createIcon(':item-add', "green"), "Add Item")
        self.addButton.setStatusTip('Add a new item to the table.')
        self.addButton.clicked.connect(lambda : self.runAction('item-add', 'undo'))
        self.addButton.setFixedHeight(30)

        self.removeButton = QPushButton(createIcon(':item-remove', "red"), "Remove Item")
        self.removeButton.setStatusTip('Remove the selected item from the table.')
        self.removeButton.clicked.connect(lambda : self.runAction('item-remove', 'undo'))
        self.removeButton.setFixedHeight(30)

        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.removeButton)
        buttonLayout.addStretch()

        # Create the table widget
        self.tableWidget = QTableWidget()
        
        # Create a vertical layout for the table and buttons
        tableLayout = QVBoxLayout()
        tableLayout.addWidget(buttonWidget)
        tableLayout.addWidget(self.tableWidget)

        tableContainer = QWidget()
        tableContainer.setLayout(tableLayout)

        self.splitter.addWidget(tableContainer)
        
        # Set table properties
        self.tableWidget.verticalHeader().setVisible(False)  # Remove row numbers
        # self.tableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # self.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # Enable sorting
        self.tableWidget.setSortingEnabled(True)

        self.tableWidget.horizontalHeader().setSortIndicatorShown(True)
        self.tableWidget.horizontalHeader().setSectionsClickable(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        # This is so the sorting arrow doesn't get blended with the background in dark mode.
        if self.parent.config.colorTheme == "dark":
            self.tableWidget.setStyleSheet("""
            QHeaderView::section {
                background-color: #666666;
            }
            """)
        
        # Connect cell click to show details
        self.currentRow = 0
        self.tableWidget.cellClicked.connect(self.showDetails)
        self.tableWidget.cellChanged.connect(self.updateDetailsFromTable)
        self.tableWidget.currentCellChanged.connect(self.updateDetailsFromSelection)
        self.tableWidget.resizeEvent = self.onResizeWindow
        self.tableWidget.viewport().installEventFilter(self)

        # Create the details widget with a header
        self.detailsWidget = QWidget()
        self.splitter.addWidget(self.detailsWidget)
        
        # Create a form layout for the details widget
        self.formLayout = QFormLayout()
        self.detailsWidget.setLayout(self.formLayout)

        # Initially hide the details widget
        self.detailsWidget.hide()

        # Add a header to the details widget
        header = QLabel("Item Details")
        header.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        self.formLayout.addRow(header)

        # Add fields to the form layout
        self.idField = LabeledLineEdit(validator=QIntValidator())
        self.idField.lineEdit.textChanged.connect(self.validateID)
        self.idField.setStatusTip('Set the ID/order of execution of this test case.')
        self.formLayout.addRow("ID:", self.idField)

        self.nameField = LabeledLineEdit()
        self.nameField.setStatusTip('Set the name of this test case.')
        self.formLayout.addRow("Name:", self.nameField)

        self.categoryField = LabeledLineEdit()
        self.categoryField.setStatusTip('Set the group this test case belong to.')
        self.formLayout.addRow("Category:", self.categoryField)

        self.repetitionsField = LabeledLineEdit(validator=QIntValidator())
        self.repetitionsField.setStatusTip('Set the number of times this test\' code will be run for.')
        self.formLayout.addRow("Repetitions:", self.repetitionsField)

        self.enabledField = QCheckBox()
        self.enabledField.setStatusTip('Enables/disables this test case during the build process.')
        self.formLayout.addRow("Enabled:", self.enabledField)

        self.codeField = CodeTextField()
        self.codeField.setStatusTip('Set the code to run for this test case.')
        self.formLayout.addRow("Command:", self.codeField)

        # Connect changes in the detail fields to update the table
        self.idField.lineEdit.textEdited.connect(self.updateTableFromDetails)
        self.nameField.lineEdit.textEdited.connect(self.updateTableFromDetails)
        self.categoryField.lineEdit.textEdited.connect(self.updateTableFromDetails)
        self.repetitionsField.lineEdit.textEdited.connect(self.updateTableFromDetails)
        self.enabledField.toggled.connect(self.updateTableFromDetails)
        self.codeField.textChanged.connect(self.updateTableFromDetails)
    
    def populateTable(self):
        self.tableWidget.setRowCount(len(self.parent.items))
        self.tableWidget.setColumnCount(5)
        columnHeaders = ["ID", "Name", "Category", "Repetitions", "Enabled"]
        columnStatusTips = ['The ID/order of execution of this test case.',
            'The name or descriptor of this test case.',
            'The group of this test case.',
            'The number of times the code of this test case will be run.',
            'Enables/disables this test case during the build process.']
        
        for col, header in enumerate(columnHeaders):
            item = QTableWidgetItem(header)
            item.setStatusTip(columnStatusTips[col])
            self.tableWidget.setHorizontalHeaderItem(col, item)

        for row, item in enumerate(self.parent.items):
            self.tableWidget.setItem(row, 0, TableCell(str(item.id), item))
            self.tableWidget.setItem(row, 1, TableCell(item.name, item))
            self.tableWidget.setItem(row, 2, TableCell(item.category, item))
            self.tableWidget.setItem(row, 3, TableCell(str(item.repetitions), item))
            
            checkbox = QCheckBox()
            checkbox.setChecked(item.enabled)
            checkbox.stateChanged.connect(lambda state, associatedItem=item: self.updateEnabledCheckboxFromTable(associatedItem, state))
            self.tableWidget.setCellWidget(row, 4, checkbox)

        # This gives some time to the UI to update.
        QTimer.singleShot(0, self.updateColumnWidth)

        # When opening, the cells get populated and think that a change has happened. Not the case.
        self.parent.unsavedChanges = False

    def onResizeWindow(self, event):
        self.updateColumnWidth()
        event.accept()

    def updateColumnWidth(self):
        columnWidthPercentages = [0.05, 0.5, 0.2, 0.15, 0.1]
        tableWidth = self.tableWidget.viewport().width()
        for i, width in enumerate(columnWidthPercentages):
            self.tableWidget.setColumnWidth(i, int(tableWidth * width))

    def showDetails(self, row, column = -1):
        self.currentRow = row
        item = self.getItemByRow(row)
        if item is None:
            return

        # To disable the updateTableFromDetails call on 'textEdited' change. 
        with SignalBlocker(self.idField, self.nameField, self.categoryField, self.repetitionsField, self.enabledField, self.codeField):
            self.idField.setText(str(item.id))
            self.nameField.setText(item.name)
            self.categoryField.setText(item.category)
            self.repetitionsField.setText(str(item.repetitions))
            self.enabledField.setChecked(item.enabled)
            self.codeField.setText(item.runcode)

        self.detailsWidget.show()

        # Highlight the entire row
        self.tableWidget.selectRow(row)

        # Add warning labels for empty fields
        self.checkEmptyFields()

    def checkEmptyFields(self):
        self.idField.clearError()
        self.nameField.clearError()
        self.categoryField.clearError()
        self.repetitionsField.clearError()

        if not self.idField.text():
            self.idField.setError("ID cannot be empty.")
        if not self.nameField.text():
            self.nameField.setError("Name cannot be empty.")
        if not self.categoryField.text():
            self.categoryField.setError("Category cannot be empty.")
        if not self.repetitionsField.text():
            self.repetitionsField.setError("Repetitions cannot be empty.")

    def updateDetailsFromSelection(self, currentRow, currentColumn, previousRow, previousColumn):
        # Ensure a valid row is selected
        if currentRow != -1 and currentRow < len(self.parent.items):
            with SignalBlocker(self.tableWidget):
                self.showDetails(currentRow, currentColumn)
        else:
            self.detailsWidget.hide()

    def updateDetailsFromTable(self, row, column):
        if row != self.currentRow:
            return
        
        with SignalBlocker(self.tableWidget):
            item = self.getItemByRow(row)
            if item is None:
                return
            
            if column == 0:
                inputID = self.tableWidget.item(row, column).text()
                if self.checkIDOk(inputID) == 0: 
                    item.id = int(self.tableWidget.item(row, column).text())
                else:
                    # Restore the original value
                    self.tableWidget.item(row, column).setText(str(item.id))
            elif column == 1:
                if not self.tableWidget.item(row, column).text():
                    self.tableWidget.item(row, column).setText(item.name)
                else:
                    item.name = self.tableWidget.item(row, column).text()
            elif column == 2:
                if not self.tableWidget.item(row, column).text():
                    self.tableWidget.item(row, column).setText(item.category)
                else:
                    item.category = self.tableWidget.item(row, column).text()
            elif column == 3:
                try:
                    inputInt = int(self.tableWidget.item(row, column).text())
                except ValueError:
                    inputInt = None

                if inputInt is not None and inputInt >= 0:
                    item.repetitions = inputInt
                    # If the number of repetitions is different, clear results.
                    if len(item.result) != item.repetitions:
                        item.result.clear()
                else:
                    self.tableWidget.item(row, column).setText(str(item.repetitions))
            
        self.parent.unsavedChanges = True
        
    def updateTableFromDetails(self):
        # Update error messages.
        self.checkEmptyFields()

        item = self.getItemByRow(self.currentRow)
        if item is None:
            return
        
        inputID = self.idField.text()
        if inputID != str(item.id):
            if self.checkIDOk(inputID) == 0: 
                item.id = inputID
            else:
                self.idField.setError("This field must be a number.")
                return

        item.name = self.nameField.text()
        
        item.category = self.categoryField.text()

        try:
            item.repetitions = int(self.repetitionsField.text())
            # If the number of repetitions is different, clear results.
            if len(item.result) != item.repetitions:
                item.result.clear()
        except ValueError:
            self.repetitionsField.setError("This field must be a number.")
            return        
        
        item.enabled = self.enabledField.isChecked()

        inputRunCode = self.codeField.getCommand(self.parent.config.validateCommands)
        if inputRunCode is None:
            self.parent.statusBar.showMessage("The code is not safe so it's been discarded.", 3000)
        else:
            # The code has changed, remove the results.
            if inputRunCode != item.runcode:
                item.result.clear()
            item.runcode = inputRunCode

        self.tableWidget.item(self.currentRow, 0).setText(str(item.id))
        self.tableWidget.item(self.currentRow, 1).setText(item.name)
        self.tableWidget.item(self.currentRow, 2).setText(item.category)
        self.tableWidget.item(self.currentRow, 3).setText(str(item.repetitions))
        self.tableWidget.cellWidget(self.currentRow, 4).setChecked(item.enabled)
        
        self.parent.unsavedChanges = True

    def updateEnabledCheckboxFromTable(self, associatedItem, state):
        associatedItem.enabled = (state == Qt.CheckState.Checked.value)
        self.enabledField.setChecked(associatedItem.enabled)

        # Get the row index by searching for the associatedItem on the table.
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row,0).text() == str(associatedItem.id):
                # Update the row when clicking on the checkbox.
                self.currentRow = row
                self.showDetails(row)

    # Check that the ID is not being used.
    def checkIDOk(self, newID) -> int:
        if type(newID) is str:
            try:
                newID = int(newID)
            except ValueError:
                return 1

        if newID < 0: return 3

        for item in self.parent.items:
            if item.id == newID:
                return 2
        return 0

    def validateID(self):
        newID = self.idField.text()
        if newID == str(self.getItemByRow(self.currentRow).id):
            self.idField.clearError()
            return 
        
        match self.checkIDOk(newID):
            case 0: self.idField.clearError()
            case 1: self.idField.setError("This ID is not a number.")
            case 2: self.idField.setError("This ID is already in use.")
            case 3: self.idField.setError("The ID must be positive or zero.")

    def deselectAll(self):
        self.tableWidget.clearSelection()
        self.detailsWidget.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.deselectAll()
        super().keyPressEvent(event)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.MouseButtonPress and source is self.tableWidget.viewport():
            if not self.tableWidget.indexAt(event.pos()).isValid():
                self.deselectAll()
        return super().eventFilter(source, event)

    def addItem(self, newItem):
        # Find the maximum current ID
        if newItem is None:
            newItem = Item()
            newItem.id = max(item.id for item in self.parent.items) + 1 if self.parent.items else 0
        elif type(newItem) is Item:
            pass
        else:
            raise Exception(f"Unexpected type received ({type(newItem)})")

        self.parent.items.append(newItem)
        self.tableWidget.setRowCount(len(self.parent.items))
        row = self.tableWidget.rowCount() - 1
        self.tableWidget.setItem(row, 0, TableCell(str(newItem.id), newItem))
        self.tableWidget.setItem(row, 1, TableCell(newItem.name, newItem))
        self.tableWidget.setItem(row, 2, TableCell(newItem.category, newItem))
        self.tableWidget.setItem(row, 3, TableCell(str(newItem.repetitions), newItem))
        checkbox = QCheckBox()
        checkbox.setChecked(newItem.enabled)
        checkbox.stateChanged.connect(lambda state, associatedItem=newItem: self.updateEnabledCheckboxFromTable(associatedItem, state))
        self.tableWidget.setCellWidget(row, 4, checkbox)
        self.tableWidget.scrollToBottom()

        self.parent.unsavedChanges = True

        return newItem

    def removeItem(self, selectedItem):
        # If no item is passed, try to get the selected item from the table.
        if selectedItem is None:
            selectedItem = self.tableWidget.selectedItems()
            if selectedItem:
                selectedItemID = int(selectedItem[0].text())
                for it in self.parent.items:
                    if it.id == selectedItemID:
                        selectedItem = it
                        break
            else:
                self.parent.statusBar.showMessage("Nothing to remove.", 3000)
                return

        # Get the row of the item from the table by its ID.
        for i in range(self.tableWidget.rowCount()):
            if int(self.tableWidget.item(i, 0).text()) == selectedItem.id:
                self.tableWidget.removeRow(i)
                selectedTableItem = self.tableWidget.selectedItems()
                # If the deleted item is the one currently selected, hide the details pane.
                if selectedTableItem and selectedTableItem[0].row() == i:
                    self.detailsWidget.hide()
                break

        self.parent.items.remove(selectedItem)
        self.parent.unsavedChanges = True
        return selectedItem

    def duplicateItem(self):
        selectedItem = self.tableWidget.selectedItems()
        if selectedItem:
            row = selectedItem[0].row()
            
            item = self.getItemByRow(row)
            if item is None:
                return None
            
            dupeItem = deepcopy(item)
            dupeItem.id = max(it.id for it in self.parent.items) + 1 if self.parent.items else 0
            self.addItem(dupeItem)

            self.parent.unsavedChanges = True
            
            return dupeItem
        return None

    def runAction(self, action : str, actionStack : str | None, *args):
        if action == 'item-add':
            item = self.addItem(None if len(args) == 0 else args[0])

        elif action == 'item-remove':
            item = self.removeItem(None if len(args) == 0 else args[0])

        elif action == 'item-duplicate':
            item = self.duplicateItem()
            if item is None: 
                # Nothing got duplicated.
                return

        elif action == 'populate-table':
            with SignalBlocker(self.tableWidget, self.detailsWidget):
                self.populateTable()
        else:
            print(f'Action "{action}" is not recognizable')

        if actionStack is not None:
            if action == 'item-add' or action == 'item-duplicate':
                UndoRedo.addAction(actionStack, ('item-remove', item))
            elif action == 'item-remove':
                UndoRedo.addAction(actionStack, ('item-add', item))

    def getItemByRow(self, row : int) -> Optional[Item]:
        return self.tableWidget.item(row, 0).associatedItem