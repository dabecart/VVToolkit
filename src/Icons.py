# **************************************************************************************************
# @file Icons.py
# @brief Tools to generate icons from the res_pack.py file in res folder and color SVG icons on 
# runtime.
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-01
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtGui import QPixmap, QImage, QPainter, QIcon
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, QFile, Qt

from typing import Union

from SettingsWindow import ProgramConfig

import ResourcePacket

def createIcon(icon_path : str, theme : Union[ProgramConfig, str]):
    if type(theme) is ProgramConfig:
        color : str = theme.colorTheme
    elif type(theme) is str:
        color : str = theme
    else:
        raise Exception(f"Unexpected type ({type(theme)})")

    match color:
        case 'light':
            color = "black"
        case 'dark':
            color = "white"
    return QIcon(recolor_svg(icon_path, color))

def recolor_svg(icon_path, color):
    # Load the SVG data from the resource
    file = QFile(icon_path)
    if not file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
        raise FileNotFoundError(f"SVG file not found: {icon_path}")
    
    svg_data = file.readAll().data().decode('utf-8')
    file.close()

    # Modify the SVG data to change the fill color
    colored_svg_data = svg_data.replace('fill="#000000"', f'fill="{color}"')
    
    # Convert the modified SVG data to QByteArray
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    buffer.write(colored_svg_data.encode('utf-8'))
    buffer.close()

    # Load the modified SVG data into QSvgRenderer
    renderer = QSvgRenderer(byte_array)
    
    # Create a QImage to render the SVG onto
    image = QImage(renderer.defaultSize(), QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)  # Fill with transparency

    # Render the SVG onto the QImage
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    # Convert QImage to QPixmap for display
    pixmap = QPixmap.fromImage(image)
    return pixmap