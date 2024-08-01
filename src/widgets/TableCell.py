# **************************************************************************************************
# @file TableCell.py
# @brief A table cell with a reference to the associated Item. 
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-01
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import QTableWidgetItem

class TableCell(QTableWidgetItem):
    def __init__(self, content, associatedItem=None):
        super().__init__(content)

        # Each table cell will have a reference to the item, that way is easier to access to it
        # using the default callbacks of PyQt6.
        self.associatedItem = associatedItem
