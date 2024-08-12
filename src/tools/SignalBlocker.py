# **************************************************************************************************
# @file SignalBlocker.py
# @brief Used to create a context to block all other signals on critical sections of code.
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-01
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

class SignalBlocker:
    def __init__(self, *widgets):
        self.widgets = widgets

    def __enter__(self):
        for widget in self.widgets:
            widget.blockSignals(True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for widget in self.widgets:
            widget.blockSignals(False)
