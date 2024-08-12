# **************************************************************************************************
# @file ContainerWidget.py
# @brief Dummy container which has a transparent background (contrary to the default QWidget 
# background color used by qdarktheme).
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-07
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import QWidget

class ContainerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)