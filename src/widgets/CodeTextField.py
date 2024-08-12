# **************************************************************************************************
# @file CodeTextField.py
# @brief Textfield to input code to run by the program. 
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-01
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import Qt, QRegularExpression
import re
from typing import Optional

class CodeTextField(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set a new console font family but keep the current size
        self.setFont(QFont("Courier New", self.font().pointSize()))
        self.highlighter = BashHighlighter(self.document())
        
    def getCommand(self, validateCommand: bool) -> Optional[str]:
        commandText = self.toPlainText().strip()
        if validateCommand and not self._validateCommand(commandText):
            return None
        return commandText

    def _validateCommand(self, command) -> bool:
        # Basic validation to disallow dangerous commands
        exclussionPatterns = [r'\brm\b', r'\bsudo\b', r'&&', r'\|\|', r';']
        for pattern in exclussionPatterns:
            if re.search(pattern, command):
                return False
        return True
    
class BashHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlightingRules = []

        # Command name format (assuming command name is the first word in a line)
        commandNameFormat = QTextCharFormat()
        commandNameFormat.setForeground(QColor(Qt.GlobalColor.magenta))
        pattern = QRegularExpression("^\\s*\\b\\w+\\b")
        self.highlightingRules.append((pattern, commandNameFormat))

        # Keyword format
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(Qt.GlobalColor.blue))
        keywordFormat.setFontWeight(QFont.Weight.Bold)
        keywords = ["if", "then", "fi", "for", "while", "do", "done", "echo", "exit"]
        for keyword in keywords:
            pattern = QRegularExpression(f"\\b{keyword}\\b")
            self.highlightingRules.append((pattern, keywordFormat))

        # Comment format
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(Qt.GlobalColor.green))
        pattern = QRegularExpression("#[^\n]*")
        self.highlightingRules.append((pattern, commentFormat))

        # String format
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(Qt.GlobalColor.red))
        pattern = QRegularExpression("\".*\"")
        self.highlightingRules.append((pattern, stringFormat))

        # Inline $ format
        inlineVarFormat = QTextCharFormat()
        inlineVarFormat.setForeground(QColor(Qt.GlobalColor.yellow))
        pattern = QRegularExpression("\\$\\w+")
        self.highlightingRules.append((pattern, inlineVarFormat))

    # Overridden function.
    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern.globalMatch(text)
            while expression.hasNext():
                match = expression.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
        self.setCurrentBlockState(0)