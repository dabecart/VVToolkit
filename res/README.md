Resources taken from [Industrial Sharp UI Icons Collection](https://www.svgrepo.com/collection/industrial-sharp-ui-icons/), under MIT license.

# Generate the resource pack

You'll need the following module installed in Python to run the next command, so install it using:

```
$ python3 -m pip install pyside6
```

To create the resource pack (*taken from [here](https://stackoverflow.com/questions/66099225/how-can-resources-be-provided-in-pyqt6-which-has-no-pyrcc)*):

```
$ pyside6-rcc res/res.qrc | sed '0,/PySide6/s//PyQt6/' > src/ResourcePacket.py
```

And import as a module into the Python file.