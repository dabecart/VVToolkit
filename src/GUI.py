# **************************************************************************************************
# @file GUI.py
# @brief Main window with common menus to all this program modes. 
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
    QMainWindow, QLabel, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QIcon, QPalette

from typing import Optional

from DataFields import loadItemsFromFile, saveItemsToFile;
from SettingsWindow import ProgramConfig, SettingsWindow
from Icons import createIcon
from SetupWidget import SetupWidget

class ItemTable(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Verification and Validation Toolkit")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(':logo'))

        # Stores the configuration of the program.
        self.config = ProgramConfig()
        # Items read from the file.
        self.items = []
        # Field to store if the file is not saved.
        self.unsavedChanges = False
        # Field to save the currently opened file.
        self.currentFile: Optional[str] = None

        # Check if the color is closer to black (dark mode) or white (light mode)
        color = self.palette().color(QPalette.ColorRole.Window)
        brightness = (color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114) / 255
        self.config.colorTheme = "dark" if  brightness < 0.5 else "light"

        # Menu Bar
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&File')

        newAction = fileMenu.addAction('&New...')
        newAction.setShortcut("Ctrl+N")
        newAction.setStatusTip("Create a new file")
        newAction.triggered.connect(self.newFile)

        openAction = fileMenu.addAction('&Open...')
        openAction.setShortcut("Ctrl+O")
        openAction.setStatusTip("Open a file")
        openAction.triggered.connect(self.openFile)

        saveAction = fileMenu.addAction('&Save')
        saveAction.setShortcut("Ctrl+S")
        saveAction.setStatusTip("Save the current file")
        saveAction.triggered.connect(self.saveFile)

        closeFileAction = fileMenu.addAction('&Close file')
        closeFileAction.setShortcut("Ctrl+W")
        closeFileAction.setStatusTip("Close the current file")
        closeFileAction.triggered.connect(self.closeFile)

        fileMenu.addSeparator()

        quitAction = fileMenu.addAction('&Quit')
        quitAction.setShortcut("Ctrl+Q")
        quitAction.setStatusTip("Quit the application")
        quitAction.triggered.connect(self.close)

        editMenu = menubar.addMenu('&Edit')

        # Set up undo action
        self.undoStack = []
        undoAction = editMenu.addAction('&Undo')
        undoAction.setShortcut("Ctrl+Z")
        undoAction.setStatusTip("Undo the last operation")
        undoAction.triggered.connect(self.undo)

        # Set up redo action
        self.redoStack = []
        redoAction = editMenu.addAction('&Redo')
        redoAction.setShortcut("Ctrl+Y")
        redoAction.setStatusTip("Redo the last operation")
        redoAction.triggered.connect(self.redo)

        editMenu.addSeparator()

        addItemAction = editMenu.addAction('&Add item')
        addItemAction.setShortcut("Alt+N")
        addItemAction.setStatusTip("Add an item to the list")
        addItemAction.triggered.connect(lambda : self.centralWidget().runAction('item-add', self.undoStack))

        removeItemAction = editMenu.addAction('&Remove item')
        removeItemAction.setShortcut("Del")
        removeItemAction.setStatusTip("Remove an item from the list")
        removeItemAction.triggered.connect(lambda : self.centralWidget().runAction('item-remove', self.undoStack))

        duplicateItemAction = editMenu.addAction('&Duplicate item')
        duplicateItemAction.setShortcut("Alt+D")
        duplicateItemAction.setStatusTip("Duplicate an item from the list")
        duplicateItemAction.triggered.connect(lambda : self.centralWidget().runAction('item-duplicate', self.undoStack))

        settingsMenu = menubar.addMenu('&Settings')
        programSettAction = settingsMenu.addAction('&Program settings')
        programSettAction.setShortcut("Ctrl+R")
        programSettAction.setStatusTip("Configure the program behavior.")
        programSettAction.triggered.connect(self.changeConfig)

        helpMenu = menubar.addMenu('&Help')
        aboutAction = helpMenu.addAction('&About')
        aboutAction.setShortcut("Ctrl+H")
        aboutAction.setStatusTip("Get help and info about this program.")

        # Add icons to all actions.
        self.actionsIcons = [
            [newAction,             ':file-new'],
            [openAction,            ':file-open'],
            [saveAction,            ':file-save'],
            [quitAction,            ':quit'],
            [undoAction,            ':edit-undo'],
            [redoAction,            ':edit-redo'],
            [addItemAction,         ':item-add'],
            [removeItemAction,      ':item-remove'],    
            [duplicateItemAction,   ':item-duplicate'],        
            [programSettAction,     ':settings-program'],    
            [aboutAction,           ':help-about']
        ]
        self.redrawIcons(self.config)

        # Tool bar
        fileToolBar = self.addToolBar('File')
        fileToolBar.addAction(newAction)
        fileToolBar.addAction(openAction)
        fileToolBar.addAction(saveAction)

        editToolBar = self.addToolBar('Edit')
        editToolBar.addAction(undoAction)
        editToolBar.addAction(redoAction)

        settingsToolBar = self.addToolBar('Edit')
        settingsToolBar.addAction(programSettAction)

        # Bottom status bar
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Ready", 3000)
        self.statusBarPermanent = QLabel("")
        self.statusBar.addPermanentWidget(self.statusBarPermanent)

        self.setupWidget = SetupWidget(self)
        self.setupWidget.hide()
        self.setCentralWidget(self.setupWidget)

    def changeConfig(self):
        settingsWindow = SettingsWindow(self.config, self)
        settingsWindow.exec()

    def redrawIcons(self, programConfig : ProgramConfig):
        for act in self.actionsIcons:
            act[0].setIcon(createIcon(act[1], programConfig))

    def newFile(self):
        if self.unsavedChanges:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         'You have unsaved changes. Do you want to save them?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                                         QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                self.saveFile()

        self.currentFile = "Unnamed.json"
        self.centralWidget().runAction('populate-table', None)

        self.statusBar.showMessage("New file created", 3000)

        self.unsavedChanges = True

        self.centralWidget().show()

    def openFile(self):
        if self.unsavedChanges:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         'You have unsaved changes. Do you want to save them?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                                         QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                self.saveFile()

        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'JSON Files (*.json)')
        if fileName:
            try:
                self.items = loadItemsFromFile(fileName)
                self.currentFile = fileName
                self.centralWidget().runAction('populate-table', None)

                self.statusBarPermanent.setText(f"Current file: <b>{self.currentFile}</b>")

                self.statusBar.showMessage("File opened", 3000)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Could not open file: {e}')
        
            self.centralWidget().show()

    def saveFile(self):
        if not self.currentFile:
            QMessageBox.warning(self, 'No File', 'No file selected. Please open a file first.')
            return False

        try:
            if self.currentFile == "Unnamed.json":
                fileName, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'JSON Files (*.json)')
                if fileName:
                    self.currentFile = fileName
                else:
                    return False

            saveItemsToFile(self.items, self.currentFile)
            self.unsavedChanges = False
            self.statusBarPermanent.setText(f"Current file: <b>{self.currentFile}</b>")
            self.statusBar.showMessage("File saved", 3000)
            return True
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not save file: {e}')
        return False

    def closeFile(self):
        if self.unsavedChanges:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         'You have unsaved changes. Do you want to save them?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                                         QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                if not self.saveFile():
                    return

        # Hide the whole window pane.
        self.centralWidget().hide()
        self.currentFile = None
        self.unsavedChanges = False

        self.statusBar.showMessage("File closed", 3000)

    def closeEvent(self, event):
        if self.unsavedChanges:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         'You have unsaved changes. Do you want to save them?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                                         QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.StandardButton.Yes:
                if not self.saveFile():
                    event.ignore()
                    return
        event.accept()

    def undo(self):
        if not self.undoStack:
            self.statusBar.showMessage("Nothing to undo.", 3000)
            return
        action, item = self.undoStack.pop()
        self.centralWidget().runAction(action, self.redoStack, item)

    def redo(self):
        if not self.redoStack:
            self.statusBar.showMessage("Nothing to redo.", 3000)
            return
        action, item = self.redoStack.pop()
        self.centralWidget().runAction(action, self.undoStack, item)