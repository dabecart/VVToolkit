class UndoRedo:
    gui = None
    undoStack = []
    redoStack = []
    cmdCalledFromHere : bool = False

    @staticmethod
    def setGUI(gui):
        UndoRedo.gui = gui

    @staticmethod
    def addAction(buffer : str, arg):
        if buffer == 'undo':
            # A new action has been added.
            UndoRedo.undoStack.append(arg)
            if not UndoRedo.cmdCalledFromHere:
                # Clear the redo buffer if the action is not coming from a undo/redo operation.
                UndoRedo.redoStack.clear()
        elif buffer == 'redo':
            UndoRedo.redoStack.append(arg)

    @staticmethod
    def undo():
        if not UndoRedo.undoStack:
            UndoRedo.gui.statusBar.showMessage("Nothing to undo.", 3000)
            return
        action, *item = UndoRedo.undoStack.pop()
        UndoRedo.cmdCalledFromHere = True
        UndoRedo.gui.currentWidget.runAction(action, 'redo', *item)
        UndoRedo.cmdCalledFromHere = False

    @staticmethod
    def redo():
        if not UndoRedo.redoStack:
            UndoRedo.gui.statusBar.showMessage("Nothing to redo.", 3000)
            return
        action, *item = UndoRedo.redoStack.pop()
        UndoRedo.cmdCalledFromHere = True
        UndoRedo.gui.currentWidget.runAction(action, 'undo', *item)
        UndoRedo.cmdCalledFromHere = False