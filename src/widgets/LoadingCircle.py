# **************************************************************************************************
# @file LoadingCircle.py
# @brief Little spinning circle that pops while loading something.
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-11
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import (QLabel, QGraphicsView, QGraphicsScene, QGraphicsProxyWidget, QSizePolicy)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, Qt
from PyQt6.QtGui import QPainter
from math import erf

from Icons import createIcon

class LoadingCircle(QGraphicsView):
    def __init__(self, sizeX: int, sizeY: int):
        super(LoadingCircle, self).__init__()

        self.setStyleSheet("border-width: 0px; background-color: transparent;")
        # Give a little margin so that it's not scrollable.
        self.setFixedHeight(sizeY+10)

        scene = QGraphicsScene(self)
        self.setScene(scene)
        scene.setSceneRect(0, 0, sizeX, sizeY)  # Match scene size to view size

        label = QLabel("")
        label.setPixmap(createIcon(':loading').pixmap(sizeX,sizeY))

        self.proxy = QGraphicsProxyWidget()
        self.proxy.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Center the proxy widget in the scene
        self.proxy.setPos((sizeX - self.proxy.boundingRect().width()) / 2, 
                          (sizeY - self.proxy.boundingRect().height()) / 2)
        self.proxy.setWidget(label)
        self.proxy.setTransformOriginPoint(self.proxy.boundingRect().center())
        scene.addItem(self.proxy)

        self.setRenderHints(self.renderHints() | QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSceneRect(0, 0, sizeX, sizeY)  # Set the view's scene rect to match

        self.anim = QPropertyAnimation(self.proxy, b"rotation")
        # Loop indefinitely.
        self.anim.setLoopCount(-1)
        
        curve = QEasingCurve()
        # This behemoth of a function comes from integrating f(x) = 0.4 + 0.6*exp(-22.2222*(-0.5 + x)^2)
        # It's a gaussian curve with a little continuous value added. This is the rotatory speed of 
        # the circle. To calculate its angular position, this function is integrated. Then the 
        # primitive F(x) is normalized between [0,1]: (F(x) - F(0)) / (F(1) - F(0))
        curve.setCustomType(lambda x: 0.180206 + 0.639588*x + 0.180361*erf(4.71405*(-0.5 + x)))
        self.anim.setEasingCurve(curve)
        self.anim.setStartValue(0)
        self.anim.setEndValue(360)
        self.anim.setDuration(2000)
        self.anim.start()