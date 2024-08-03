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

from dataclasses import dataclass, asdict, fields, field
import json
from typing import List
import subprocess
import shlex    # To easily parse the arguments for a console.
from time import perf_counter

@dataclass
class ResultCommand:
    output: str             = field(default="")
    returnCode : int        = field(default=None)
    executionTime : float   = field(default=0)

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
    
    def hasBeenRun(self) -> bool:
        return len(self.result) > 0
    
    def isEnabled(self) -> bool:
        return self.enabled and self.repetitions > 0

    def run(self):
        commandArgs = shlex.split(self.runcode)
        for _ in range(self.repetitions):
            startTime = perf_counter()
            runResult = subprocess.run(commandArgs, stdout=subprocess.PIPE)
            executionTime = perf_counter() - startTime
            self.result.append(ResultCommand(output=runResult.stdout.decode('utf-8'),
                                             returnCode=runResult.returncode,
                                             executionTime=executionTime))
            
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
            # Handle the result field.
            if 'result' in filtered_dict:
                filtered_dict['result'] = [ResultCommand(**res) for res in filtered_dict['result']]
            items.append(Item(**filtered_dict))
        return items