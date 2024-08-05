# **************************************************************************************************
# @file ParallelExecution.py
# @brief All GUI changes must be done on the core that's running PyQt. For time expensive processes, 
# it may freeze the screen, which is not good. This class aids by moving the process to another 
# thread while leaving free the main core. 
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-03
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtCore import pyqtSignal, QObject, pyqtSlot, QThread

class Worker(QObject):

    finishedSignal = pyqtSignal()
    
    def __init__(self, runFunction, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.runFunction = runFunction

    @pyqtSlot()
    def run(self):
        # Run the function.
        self.runFunction()
        # Signal that the task is finished
        self.finishedSignal.emit()

class ParallelExecution():
    def __init__(self, runFunction, onFinishFunction) -> None:
        self.runFunction = runFunction
        self.onFinishFunction = onFinishFunction

        self.thread = QThread()
        self.worker = Worker(self.runFunction)
        self.worker.moveToThread(self.thread)
        
        # Connect the signals
        self.worker.finishedSignal.connect(self.thread.quit)
        self.worker.finishedSignal.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        if self.onFinishFunction is not None:
            self.thread.finished.connect(self.onFinishFunction)
        
        # Connect the start of thread to the run function of the worker.
        self.thread.started.connect(self.worker.run)
        
    def run(self):
        # Start the thread.
        self.thread.start()

class ParallelLoopExecution():
    def __init__(self, loopItems, runFunction, onFinishFunction, onLoopFinished) -> None:
        self.loopItems = loopItems
        self.runFunction = runFunction
        self.onFinishFunction = onFinishFunction
        self.onLoopFinished = onLoopFinished
    
    def run(self):
        self._runItem(self._getNextItem())

    def _getNextItem(self):
        if self.loopItems:
            return self.loopItems.pop(0)
        return None

    def _runItem(self, item):
        if item is None: 
            self.onLoopFinished()
            return

        self.thread = QThread()
        self.worker = Worker(lambda: self.runFunction(item))
        self.worker.moveToThread(self.thread)
        
        # Connect the signals
        self.worker.finishedSignal.connect(self.thread.quit)
        self.worker.finishedSignal.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        if self.onFinishFunction is not None:
            self.thread.finished.connect(lambda: self.onFinishFunction(item))
            # When the thread finishes, call for the next item.
            self.thread.finished.connect(self.run)
        
        # Connect the start of thread to the run function of the worker.
        self.thread.started.connect(self.worker.run)
        # Start the thread.
        self.thread.start()