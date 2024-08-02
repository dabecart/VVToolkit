# **************************************************************************************************
# @file DataFields.py
# @brief The fields that form a testcase or item. Includes the tools to save and load files.
#
# @project   VVToolkit
# @version   1.0
# @date      2024-08-01
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import QMessageBox

from dataclasses import dataclass, asdict, fields, field
import json
from typing import List
import subprocess
import shlex

@dataclass
class ResultCommand:
    output: str         = field(default="")
    returnCode : int    = field(default=None)

@dataclass
class Item:
    id: int             = field(default=-1)
    name: str           = field(default="Undeclared")
    category: str       = field(default="Undetermined")
    repetitions: int    = field(default=1)
    enabled: bool       = field(default=False)
    runcode: str        = field(default="")
    result : List[ResultCommand]  = field(default_factory=lambda: [])

    def __lt__(self, other):
        return self.id < other.id
    
    def isBeenRun(self) -> bool:
        return len(self.result) > 0

    def run(self, raiseWarning : bool = False):
        if self.isBeenRun():
            if raiseWarning:
                QMessageBox.critical(self, 'Error', f'Item {self.name} contains results and/or configuration. Please, clear it before running it again.')
            return

        for _ in range(self.repetitions):
            commandArgs = shlex.split(self.runcode)
            runResult = subprocess.run(commandArgs, stdout=subprocess.PIPE)
            self.result.append(ResultCommand(output=runResult.stdout.decode('utf-8'),
                                             returnCode=runResult.returncode))
            

def saveItemsToFile(items: List[Item], filename: str) -> None:
    with open(filename, 'w') as file:
        json.dump([asdict(item) for item in items], file)

def loadItemsFromFile(filename: str) -> List[Item]:
    with open(filename, 'r') as file:
        items_dict = json.load(file)
        # Create a set of field names from the dataclass
        item_fields = {field.name for field in fields(Item)}
        items = []
        for item_dict in items_dict:
            # Filter the dictionary to only include valid fields
            filtered_dict = {k: v for k, v in item_dict.items() if k in item_fields}
            # # Add missing fields with None
            # for field in item_fields - filtered_dict.keys():
            #     filtered_dict[field] = None
            items.append(Item(**filtered_dict))
        return items