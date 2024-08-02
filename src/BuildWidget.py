from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QComboBox)
from PyQt6.QtCore import Qt

from widgets.CollapsibleBox import CollapsibleBox
from DataFields import Item

from Icons import createIcon

class BuildWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.parent = parent

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        topBar = QWidget()
        topBarLayout = QHBoxLayout(topBar)

        self.runAllButton = QPushButton(createIcon(':run', self.parent.config), "Run all")
        self.runAllButton.setToolTip("Runs all test cases without an output.")
        self.runAllButton.clicked.connect(lambda : self.runAction('run-all-items', None))
        self.runAllButton.setFixedHeight(30)

        self.clearAllButton = QPushButton(createIcon(':clear', self.parent.config), "Clear all")
        self.clearAllButton.setToolTip("Clears the outputs of all test cases.")
        self.clearAllButton.clicked.connect(lambda : self.runAction('clear-all-items', None))
        self.clearAllButton.setFixedHeight(30)

        self.categoryCombo = QComboBox()
        self.categoryCombo.setToolTip("Select the category to filter the test cases.")
        self.categoryCombo.addItem('All categories')
        self.categoryCombo.setCurrentIndex(0)
        self.categoryCombo.setFixedHeight(30)

        topBarLayout.addWidget(self.runAllButton)
        topBarLayout.addWidget(self.clearAllButton)
        topBarLayout.addStretch()
        topBarLayout.addWidget(self.categoryCombo)

        layout.addWidget(topBar)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        layout.addWidget(self.scrollArea)

        self.scrollContent = QWidget()
        self.scrollArea.setWidget(self.scrollContent)
        self.scrollLayout = QVBoxLayout(self.scrollContent)
        self.scrollLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def populateTable(self):
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
            box = CollapsibleBox(':logo', item, self.parent.config, self)
            self.scrollLayout.addWidget(box)
            if item.category not in categoriesList:
                categoriesList.append(item.category)
                if longestSentenceCount < len(item.category):
                    longestSentenceCount = len(item.category)

        self.categoryCombo.addItems(categoriesList)
        self.categoryCombo.setMinimumContentsLength(longestSentenceCount + 10)

    def runAction(self, action, actionStack, *args):
        if action == 'run-item':
            box : CollapsibleBox = args[0]
            item : Item = box.item
            item.run(raiseWarning=True)
            box.outputCmdText.setText(item.result[0].output)

        elif action == 'clear-item':
            box : CollapsibleBox = args[0]
            item : Item = box.item
            item.result.clear()
            box.outputCmdText.setText("")

        elif action == 'run-all-items':
            for i in range(self.scrollLayout.count()):
                self.runAction('run-item', actionStack, self.scrollLayout.itemAt(i).widget()) 

        elif action == 'clear-all-items':
            for i in range(self.scrollLayout.count()):
                self.runAction('clear-item', actionStack, self.scrollLayout.itemAt(i).widget()) 

        elif action == 'populate-table':
                self.populateTable()