# **************************************************************************************************
# @file Main.py
# @brief Entry point for the program.
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-01
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

import sys
from GUI import GUI
from PyQt6.QtWidgets import QApplication
import qdarktheme

if __name__ == "__main__":
    app = QApplication(sys.argv)

    qss = """
    ContainerWidget {
        background-color: transparent;
    }
    """
    qdarktheme.setup_theme("auto", additional_qss=qss)

    window = GUI()
    window.show()
    sys.exit(app.exec())