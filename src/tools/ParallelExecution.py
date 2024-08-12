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

    exceptionSignal = pyqtSignal(Exception)
    finishedSignal = pyqtSignal()
    
    def __init__(self, runFunction, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.runFunction = runFunction

    @pyqtSlot()
    def run(self):
        try:
            # Run the function.
            self.runFunction()
            # Signal that the task is finished
            self.finishedSignal.emit()
        except Exception as e:
            # If an error happens, it will call the errorSignal.
            self.exceptionSignal.emit(e)
            return
        

class ParallelExecution():
    def __init__(self, runFunction, onFinishFunction, onException = None) -> None:
        self.runFunction = runFunction
        self.onFinishFunction = onFinishFunction
        self.onException = onException
        self.exceptionOccurred = False

        self.thread = QThread()
        self.worker = Worker(self.runFunction)
        self.worker.moveToThread(self.thread)
        
        # Connect the signals
        self.worker.finishedSignal.connect(self.thread.quit)
        self.worker.finishedSignal.connect(self.worker.deleteLater)

        self.worker.exceptionSignal.connect(self.thread.quit)
        self.worker.exceptionSignal.connect(self.worker.deleteLater)

        self.thread.finished.connect(self.thread.deleteLater)

        if self.onFinishFunction is not None:
            self.thread.finished.connect(self.finishFunction)
        if self.onException is not None:
            self.worker.exceptionSignal.connect(self.exceptionFunction)
        
        # Connect the start of thread to the run function of the worker.
        self.thread.started.connect(self.worker.run)

    pyqtSlot()
    def finishFunction(self):
        if not self.exceptionOccurred:
            self.onFinishFunction()

    pyqtSlot(Exception)
    def exceptionFunction(self, e: Exception):
        self.exceptionOccurred = True
        self.onException(e)

    def run(self):
        # Start the thread.
        self.thread.start()

class ParallelLoopExecution():
    def __init__(self, loopItems, runFunction, onFinishFunction, onLoopFinished, onException = None) -> None:
        self.loopItems = loopItems
        self.runFunction = runFunction
        self.onFinishFunction = onFinishFunction
        self.onLoopFinished = onLoopFinished
        self.onException = onException
        self.exceptionOccurred = False

    def finishedFunction(self, item):
        # This function gets called when the exception calls for the loop to be exited. This if 
        # statement keeps the next item to be processed.
        if not self.exceptionOccurred:
            self.onFinishFunction(item)
            # When the thread finishes, call for the next item.
            self.run()

    pyqtSlot(Exception)
    def exceptionFunction(self, e: Exception):
        self.exceptionOccurred = True
        self.onException(e)

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

        self.worker.exceptionSignal.connect(self.thread.quit)
        self.worker.exceptionSignal.connect(self.worker.deleteLater)
        
        self.thread.finished.connect(self.thread.deleteLater)
        if self.onFinishFunction is not None:
            # If all went OK, run the finish function when the thread is closed. That way the thread
            # won't be destroyed whilst running. This function passes to the next item in the list.
            # If it were to continue running on the next item whilst the other thread was running 
            # it would raise an exception because it would be deleted without it being stopped.
            self.thread.finished.connect(lambda: self.finishedFunction(item))

        if self.onException is not None:
            # On exception the whole loop halts. In this case, the thread will get closed 
            # automatically and it doesn't have the problem as before as there won't be any more 
            # items being processed.
            self.worker.exceptionSignal.connect(self.exceptionFunction)
        
        # Connect the start of thread to the run function of the worker.
        self.thread.started.connect(self.worker.run)
        # Start the thread.
        self.thread.start()