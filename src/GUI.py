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

from typing import Optional, List

from DataFields import Item, TestDataFields
import DataFields
from Icons import createIcon

from SettingsWindow import ProgramConfig, SettingsWindow
from ProjectSettingsWindow import ProjectSettingsWindow
from AboutWindow import AboutWindow
from SetupWidget import SetupWidget
from BuildWidget import BuildWidget
from TestWidget import TestWidget
from tools.UndoRedo import UndoRedo
import tools.TestExporter as Exporter

from widgets.ContainerWidget import ContainerWidget

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Verification and Validation Toolkit")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(':logo'))

        # Stores the configuration of the program.
        self.config = ProgramConfig()
        # The project configuration.
        self.projectDataFields : TestDataFields = TestDataFields()
        # Items read from the file.
        self.items : List[Item] = []
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
        newAction.setStatusTip("Create a new file.")
        newAction.triggered.connect(self.newFile)

        openAction = fileMenu.addAction('&Open...')
        openAction.setShortcut("Ctrl+O")
        openAction.setStatusTip("Open a file.")
        openAction.triggered.connect(self.openFile)

        saveAction = fileMenu.addAction('&Save')
        saveAction.setShortcut("Ctrl+S")
        saveAction.setStatusTip("Save the current file.")
        saveAction.triggered.connect(self.saveFile)

        closeFileAction = fileMenu.addAction('&Close file')
        closeFileAction.setShortcut("Ctrl+W")
        closeFileAction.setStatusTip("Close the current file.")
        closeFileAction.triggered.connect(self.closeFile)

        fileMenu.addSeparator()

        importAction = fileMenu.addAction('&Import test results')
        importAction.setStatusTip("Import a test results file (.vvt).")
        importAction.triggered.connect(self.importTests)

        exportAction = fileMenu.addAction('&Export test results')
        exportAction.setStatusTip("Exports the current test results as .vvt and .xlsl files.")
        exportAction.triggered.connect(self.exportTests)

        fileMenu.addSeparator()

        quitAction = fileMenu.addAction('&Quit')
        quitAction.setShortcut("Ctrl+Q")
        quitAction.setStatusTip("Quit the application.")
        quitAction.triggered.connect(self.close)

        self.editMenu = self.menubar.addMenu('&Edit')

        # Configure undo/redo.
        UndoRedo.setGUI(self)

        # Set up undo action
        undoAction = self.editMenu.addAction('&Undo')
        undoAction.setShortcut("Ctrl+Z")
        undoAction.setStatusTip("Undo the last operation.")
        undoAction.triggered.connect(UndoRedo.undo)

        # Set up redo action
        redoAction = self.editMenu.addAction('&Redo')
        redoAction.setShortcut("Ctrl+Y")
        redoAction.setStatusTip("Redo the last operation.")
        redoAction.triggered.connect(UndoRedo.redo)

        self.editMenu.addSeparator()

        addItemAction = self.editMenu.addAction('&Add item')
        addItemAction.setShortcut("Alt+N")
        addItemAction.setStatusTip("Add an item to the list.")
        addItemAction.triggered.connect(lambda : self.currentWidget.runAction('item-add', 'undo'))

        removeItemAction = self.editMenu.addAction('&Remove item')
        removeItemAction.setShortcut("Del")
        removeItemAction.setStatusTip("Remove an item from the list.")
        removeItemAction.triggered.connect(lambda : self.currentWidget.runAction('item-remove', 'undo'))

        duplicateItemAction = self.editMenu.addAction('&Duplicate item')
        duplicateItemAction.setShortcut("Alt+D")
        duplicateItemAction.setStatusTip("Duplicate an item from the list.")
        duplicateItemAction.triggered.connect(lambda : self.currentWidget.runAction('item-duplicate', 'undo'))

        self.editMenu.addSeparator()

        projectSettings = self.editMenu.addAction('&Project settings')
        projectSettings.setShortcut("Alt+.")
        projectSettings.setStatusTip("Set the project and test configuration.")
        projectSettings.triggered.connect(self.changeProjectSettings)

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
        aboutAction.triggered.connect(self.showAboutWindow)

        # Add icons to all actions.
        actionsIcons = [
            [newAction,             ':file-new'         ],
            [openAction,            ':file-open'        ],
            [saveAction,            ':file-save'        ],
            [importAction,          ':file-import'      ],
            [exportAction,          ':file-export'      ],
            [quitAction,            ':quit'             ],
            [undoAction,            ':edit-undo'        ],
            [redoAction,            ':edit-redo'        ],
            [projectSettings,       ':edit-settings'    ],   
            [addItemAction,         ':item-add'         ],
            [removeItemAction,      ':item-remove'      ],    
            [duplicateItemAction,   ':item-duplicate'   ],
            [programSettAction,     ':settings-program' ],    
            [aboutAction,           ':help-about'       ],
            [self.setupModeAction,  ':mode-setup'       ],
            [self.buildModeAction,  ':mode-build'       ],
            [self.testModeAction,   ':mode-test'        ],
        ]

        # Create the icons and set them to the actions. These icons will automatically update during
        # a color theme change.
        for act in actionsIcons:
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
        settingsToolBar.addAction(projectSettings)
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

    def changeMode(self, mode : str | None):
        if mode is None:
            self.centralWidget().hide()
            # Disable some of the actions.
            for act in self.editMenu.actions():
                act.setEnabled(False)    
            # Reenable the buttons in test mode if the file was closed (they will be hidden).
            self.testWidget.runAction('set-read-only', None, False)
        else:
            # Enable some of the actions.
            for act in self.editMenu.actions():
                act.setEnabled(True)    
            self.centralWidget().show()

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
                self.buildWidget.runAction('populate-table', None, self.buildWidget.categoryCombo.currentText())
                self.changeMenuBarWidgetButton(self.buildModeAction, True)
            case 'test':
                self.centralWidget().setCurrentIndex(2)
                self.currentWidget = self.testWidget
                self.changeMenuBarWidgetButton(self.testModeAction, True)
            case None:
                self.changeMenuBarWidgetButton(self.setupModeAction, None)
                self.changeMenuBarWidgetButton(self.buildModeAction, None)
                self.changeMenuBarWidgetButton(self.testModeAction,  None)

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

    def changeProjectSettings(self):
        projectSettings = ProjectSettingsWindow(self.projectDataFields, self.currentFile.endswith(".vvt"), self)
        projectSettings.exec()

    def showAboutWindow(self):
        about = AboutWindow(self)
        about.exec()

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

        self.currentWidget.runAction('populate-table', None, None)

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
            itemsData = DataFields.loadItemsFromFile(fileName)
            self.projectDataFields = itemsData[0]
            self.items = itemsData[1]
            
            self.currentFile = fileName

            self.changeMode('setup')

            self.setupWidget.runAction('populate-table', None)
            self.buildWidget.runAction('populate-table', None, None)

            self.statusBarPermanent.setText(f"Current file: <b>{self.currentFile}</b>")

            self.statusBar.showMessage("File opened.", 3000)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not open file: {e}')
    
    def saveFile(self):
        if not self.currentFile:
            QMessageBox.warning(self, 'No File', 'No file selected. Please open a file first.')
            return False
        
        if self.currentFile.endswith(".vvt"):
            QMessageBox.warning(self, 'Cannot save .vvt files', 
                                'The currently opened file is an output test file with the results of a previously run test.\n'
                                'This file is read only and therefore it cannot be saved.\n'
                                'You may open its original <b>.vvf</b> file to rerun again the test.')
            return False

        try:
            if self.currentFile == "Unnamed.vvf":
                fileName, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'VVF Files (*.vvf)')
                if fileName:
                    self.currentFile = fileName
                else:
                    return False

            DataFields.saveItemsToFile(self.projectDataFields, self.items, self.currentFile)
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
        self.currentFile = None

        # Delete items.
        self.items.clear()
        self.testWidget.runAction('clear-all-tests', None, False)

        self.changeMode(None)

        self.statusBar.showMessage("File closed.", 3000)

        self.statusBarPermanent.clear()

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
        if not self.currentFile or self.currentFile.endswith(".vvt"):
            return False
        return (self.currentFile == 'file_not_saved.vvf') or not DataFields.areItemsSaved(self.projectDataFields, self.items, self.currentFile)
    
    def importTests(self):
        if self.testWidget.currentTest or self.testWidget.currentlyRunningTest:
             QMessageBox.warning(self, 'Import error', 
                                 'There is an unsaved test on the TEST mode.\n'
                                 'Export it and clear it before importing again.')
             return

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

        try:
            fileName, _ = QFileDialog.getOpenFileName(self, 'Import Test File', '', 'VVT Files (*.vvt)')
            if not fileName:
                return 

            self.currentFile = fileName

            testData = DataFields.loadTestFromFile(fileName)
            self.projectDataFields = testData[0]
            self.testWidget.currentTest = testData[1]

            # While importing a test file, you may not exit to other modes.
            self.changeMode('test')
            self.changeMenuBarWidgetButton(self.setupModeAction, None)
            self.changeMenuBarWidgetButton(self.buildModeAction, None)

            self.testWidget.runAction('populate-table', None, None)
            self.testWidget.runAction('set-read-only', None, True)

            self.statusBar.showMessage("Test file imported.", 3000)
            self.statusBarPermanent.setText(f"Current file: <b>{self.currentFile}</b>")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not import test file: {e}')
        return False

    def exportTests(self):
        if not self.testWidget.currentTest:
             QMessageBox.warning(self, 'Export error', 
                                 'There is no test to export.\n'
                                 'Run it first and try to export again.')
             return False
        
        if self.testWidget.currentlyRunningTest:
             QMessageBox.warning(self, 'Export error', 
                                 'A test is currently being run.\n'
                                 'Wait for it to end and export it again.')
             return False
        
        try:
            fileName, _ = QFileDialog.getSaveFileName(self, 'Export Test File', '', 'VVT Files (*.vvt)')
            if not fileName:
                return False
            
            DataFields.saveTestToFile(self.projectDataFields, self.testWidget.currentTest, fileName)

            Exporter.replacePlaceholders(fileName.split('.')[0] + ".xlsx", self.projectDataFields, self.testWidget.currentTest)

            self.statusBar.showMessage("Test file exported.", 3000)
            return True
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not export test file: {e}')
        return False
        
