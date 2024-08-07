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
    QMainWindow, QLabel, QMessageBox, QFileDialog, QSizePolicy, QToolBar, QStackedWidget
)
from PyQt6.QtGui import QIcon, QPalette, QActionGroup

from typing import Optional

from DataFields import loadItemsFromFile, saveItemsToFile, areItemsSaved
from SettingsWindow import ProgramConfig, SettingsWindow
from Icons import createIcon
from SetupWidget import SetupWidget
from BuildWidget import BuildWidget
from TestWidget import TestWidget
from tools.UndoRedo import UndoRedo

from widgets.ContainerWidget import ContainerWidget

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Verification and Validation Toolkit")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(':logo'))

        # Stores the configuration of the program.
        self.config = ProgramConfig()
        # Items read from the file.
        self.items = []
        # Field to save the currently opened file.
        self.currentFile: Optional[str] = None
        # Mode of the current program.
        self.currentMode : str = None
        # The currently shown widget on the center of the GUI.
        self.currentWidget = None

        # Check if the color is closer to black (dark mode) or white (light mode)
        color = self.palette().color(QPalette.ColorRole.Window)
        brightness = (color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114) / 255
        self.config.colorTheme = "dark" if  brightness < 0.5 else "light"

        # Menu Bar
        self.menubar = self.menuBar()

        fileMenu = self.menubar.addMenu('&File')

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

        editMenu = self.menubar.addMenu('&Edit')

        # Configure undo/redo.
        UndoRedo.setGUI(self)

        # Set up undo action
        undoAction = editMenu.addAction('&Undo')
        undoAction.setShortcut("Ctrl+Z")
        undoAction.setStatusTip("Undo the last operation")
        undoAction.triggered.connect(UndoRedo.undo)

        # Set up redo action
        redoAction = editMenu.addAction('&Redo')
        redoAction.setShortcut("Ctrl+Y")
        redoAction.setStatusTip("Redo the last operation")
        redoAction.triggered.connect(UndoRedo.redo)

        editMenu.addSeparator()

        addItemAction = editMenu.addAction('&Add item')
        addItemAction.setShortcut("Alt+N")
        addItemAction.setStatusTip("Add an item to the list")
        addItemAction.triggered.connect(lambda : self.currentWidget.runAction('item-add', 'undo'))

        removeItemAction = editMenu.addAction('&Remove item')
        removeItemAction.setShortcut("Del")
        removeItemAction.setStatusTip("Remove an item from the list")
        removeItemAction.triggered.connect(lambda : self.currentWidget.runAction('item-remove', 'undo'))

        duplicateItemAction = editMenu.addAction('&Duplicate item')
        duplicateItemAction.setShortcut("Alt+D")
        duplicateItemAction.setStatusTip("Duplicate an item from the list")
        duplicateItemAction.triggered.connect(lambda : self.currentWidget.runAction('item-duplicate', 'undo'))

        settingsMenu = self.menubar.addMenu('&Settings')
        programSettAction = settingsMenu.addAction('&Program settings')
        programSettAction.setShortcut("Ctrl+R")
        programSettAction.setStatusTip("Configure the program behavior.")
        programSettAction.triggered.connect(self.changeConfig)
        
        settingsMenu.addSeparator()

        self.setupModeAction = settingsMenu.addAction('&SETUP mode')
        self.setupModeAction.setStatusTip("Change to SETUP mode.")
        self.setupModeAction.triggered.connect(lambda : self.changeMode('setup'))
        self.setupModeAction.setCheckable(True)

        self.buildModeAction = settingsMenu.addAction('&BUILD mode')
        self.buildModeAction.setStatusTip("Change to BUILD mode.")
        self.buildModeAction.triggered.connect(lambda : self.changeMode('build'))
        self.buildModeAction.setCheckable(True)

        self.testModeAction = settingsMenu.addAction('&TEST mode')
        self.testModeAction.setStatusTip("Change to TEST mode.")
        self.testModeAction.triggered.connect(lambda : self.changeMode('test'))
        self.testModeAction.setCheckable(True)

        actionGroup = QActionGroup(self)
        actionGroup.setExclusive(True)
        actionGroup.addAction(self.setupModeAction)
        actionGroup.addAction(self.buildModeAction)
        actionGroup.addAction(self.testModeAction)

        helpMenu = self.menubar.addMenu('&Help')
        aboutAction = helpMenu.addAction('&About')
        aboutAction.setShortcut("F1")
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
            [aboutAction,           ':help-about'],
            [self.setupModeAction,       ':mode-setup'],
            [self.buildModeAction,       ':mode-build'],
            [self.testModeAction,        ':mode-test'],
        ]

        # Create the icons and set them to the actions. These icons will automatically update during
        # a color theme change.
        for act in self.actionsIcons:
            newIcon = createIcon(act[1], self.config)
            newIcon.setAssociatedWidget(act[0])
            act[0].setIcon(newIcon)

        # Tool bar
        fileToolBar = self.addToolBar('File')
        fileToolBar.setMovable(False)
        fileToolBar.addAction(newAction)
        fileToolBar.addAction(openAction)
        fileToolBar.addAction(saveAction)

        editToolBar = self.addToolBar('Edit')
        editToolBar.setMovable(False)
        editToolBar.addAction(undoAction)
        editToolBar.addAction(redoAction)

        settingsToolBar = self.addToolBar('Settings')
        settingsToolBar.setObjectName('Settings Toolbar')
        settingsToolBar.setMovable(False)
        settingsToolBar.addAction(programSettAction)

        # Spacer to move the MODE buttons to the right.
        spacer = ContainerWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        settingsToolBar.addWidget(spacer)

        settingsToolBar.addAction(self.setupModeAction)
        settingsToolBar.addAction(self.buildModeAction)
        settingsToolBar.addAction(self.testModeAction)

        # Bottom status bar
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Ready.", 3000)
        self.statusBarPermanent = QLabel("")
        self.statusBar.addPermanentWidget(self.statusBarPermanent)

        self.setupWidget = SetupWidget(self)
        self.buildWidget = BuildWidget(self)
        self.testWidget  = TestWidget(self)

        centralWidget = QStackedWidget()
        centralWidget.addWidget(self.setupWidget)
        centralWidget.addWidget(self.buildWidget)
        centralWidget.addWidget(self.testWidget)
        self.setCentralWidget(centralWidget)
        self.centralWidget().hide()

        self.changeMode(None)

    def setEnableToolbars(self, enable : bool):
        self.menubar.setEnabled(enable)
        toolbars = self.findChildren(QToolBar)
        for t in toolbars:
            t.setEnabled(enable)

    def changeMode(self, mode : str):
        if mode is not None and self.currentMode == mode:
            return
        
        if mode == 'test':
            if self.unsavedChanges():
                QMessageBox.warning(self, 'Save the file first', 
                                    'Save the file first before changing to test mode.')
                return

            for it in self.items:
                if not it.hasBeenRun():
                    reply = QMessageBox.question(self, 'Run all tests', 
                            'You have to run all tests on build mode before changing to test mode.\n'
                            'Do you want to change to build mode?',
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                            QMessageBox.StandardButton.Yes)
                    if reply == QMessageBox.StandardButton.Yes:
                        self.changeMode('build')
                    return

        self.changeMenuBarWidgetButton(self.setupModeAction, False)
        self.changeMenuBarWidgetButton(self.buildModeAction, False)
        self.changeMenuBarWidgetButton(self.testModeAction, False)

        match mode:
            case 'setup': 
                self.centralWidget().setCurrentIndex(0)
                self.currentWidget = self.setupWidget
                self.changeMenuBarWidgetButton(self.setupModeAction, True)
            case 'build': 
                self.centralWidget().setCurrentIndex(1)
                self.currentWidget = self.buildWidget
                self.currentWidget.runAction('populate-table', None)
                self.changeMenuBarWidgetButton(self.buildModeAction, True)
            case 'test':
                self.centralWidget().setCurrentIndex(2)
                self.currentWidget = self.testWidget
                self.changeMenuBarWidgetButton(self.testModeAction, True)
            case None:
                self.changeMenuBarWidgetButton(self.setupModeAction, None)
                self.changeMenuBarWidgetButton(self.buildModeAction, None)
                self.changeMenuBarWidgetButton(self.testModeAction,  None)
                return

        self.currentMode = mode

    def changeMenuBarWidgetButton(self, action, selected : bool | None):
        if selected is None:
            action.setEnabled(False)
        else:
            action.setEnabled(True)
            action.setChecked(selected)

    def changeConfig(self):
        settingsWindow = SettingsWindow(self.config, self)
        settingsWindow.exec()

    def newFile(self):
        if self.unsavedChanges():
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         'You have unsaved changes. Do you want to save them?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                                         QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                self.saveFile()

        self.currentFile = "file_not_saved.vvf"

        self.changeMode('setup')

        self.currentWidget.runAction('populate-table', None)

        self.statusBar.showMessage("New file created.", 3000)

        self.centralWidget().show()

    def openFile(self):
        if self.unsavedChanges():
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         'You have unsaved changes. Do you want to save them?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                                         QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                self.saveFile()

        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'VVF Files (*.vvf)')
        if not fileName:
            return 
        
        try:
            self.items = loadItemsFromFile(fileName)
            self.currentFile = fileName

            self.changeMode('setup')

            self.currentWidget.runAction('populate-table', None)

            self.statusBarPermanent.setText(f"Current file: <b>{self.currentFile}</b>")

            self.statusBar.showMessage("File opened.", 3000)

            self.centralWidget().show()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not open file: {e}')
    
    def saveFile(self):
        if not self.currentFile:
            QMessageBox.warning(self, 'No File', 'No file selected. Please open a file first.')
            return False

        try:
            if self.currentFile == "Unnamed.vvf":
                fileName, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'VVF Files (*.vvf)')
                if fileName:
                    self.currentFile = fileName
                else:
                    return False

            saveItemsToFile(self.items, self.currentFile)
            self.statusBarPermanent.setText(f"Current file: <b>{self.currentFile}</b>")
            self.statusBar.showMessage("File saved.", 3000)
            return True
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not save file: {e}')
        return False

    def closeFile(self):
        if self.unsavedChanges():
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

        self.changeMode(None)

        self.statusBar.showMessage("File closed.", 3000)

    def closeEvent(self, event):
        if self.unsavedChanges():
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

    def unsavedChanges(self) -> bool:
        if self.currentFile:
            return (self.currentFile == 'file_not_saved.vvf') or not areItemsSaved(self.items, self.currentFile)
        return False