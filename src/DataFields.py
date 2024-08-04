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

class TestResult:
    OK = 1
    ERROR = 2
    UNDEFINED = 3

@dataclass
class ResultCommand:
    output: str             = field(default="")
    returnCode : int        = field(default=None)
    executionTime : float   = field(default=0)

    def __eq__(self, value: object) -> bool:
        if type(value) is not ResultCommand:
            return False
        
        outputSame = self.output == value.output
        returnSame = self.returnCode == value.returnCode
        return outputSame and returnSame

@dataclass
class ValidationCommand:
    operation: str  = field(default='same')
    operator: str   = field(default='==')
    operatorVal : str = field(default='')   

    def validate(self, a : ResultCommand, b : ResultCommand, prevTestResult : TestResult) -> TestResult:
        match self.operation:
            case 'same':
                currentTestResult = TestResult.OK if a==b else TestResult.ERROR
            case _:
                print(f"Undefined operation {self.operation}")
                currentTestResult = TestResult.ERROR

        if prevTestResult is None or currentTestResult == prevTestResult:
            return currentTestResult
        else:
            return TestResult.UNDEFINED

    def toString(self):
        match self.operation:
            case 'same':
                return "Outputs must be the same."
            case _:
                return "Undefined operation {self.operation}"

@dataclass
class Item:
    id: int                             = field(default=-1)
    name: str                           = field(default="Undeclared")
    category: str                       = field(default="Undetermined")
    repetitions: int                    = field(default=1)
    enabled: bool                       = field(default=False)
    runcode: str                        = field(default="")
    result : List[ResultCommand]        = field(default_factory=lambda: [])
    validationCmd : ValidationCommand   = field(default_factory=lambda: ValidationCommand())
    
    testResult : TestResult             = field(default=None)
    testOutput : List[ResultCommand]    = field(default_factory=lambda: [])

    def __lt__(self, other):
        return self.id < other.id
    
    def hasBeenRun(self) -> bool:
        return len(self.result) == self.repetitions
    
    def hasBeenTested(self) -> bool:
        return len(self.testOutput) == self.repetitions
    
    def isEnabled(self) -> bool:
        return self.enabled and self.repetitions > 0

    def run(self):
        if not self.hasBeenRun():
            self._execute(self.result)
            
    def test(self):
        if not self.result:
            print("Cannot test without results!")
            return
        
        if self.hasBeenTested():
            return
        
        # Run the commands.
        self._execute(self.testOutput)
        # Test them against the results.
        for result, test in zip(self.result, self.testOutput):
            self.testResult = self.validationCmd.validate(result, test, self.testResult)

    def _execute(self, resultOutputSave):
        commandArgs = shlex.split(self.runcode)
        for _ in range(self.repetitions):
            startTime = perf_counter()
            runResult = subprocess.run(commandArgs, stdout=subprocess.PIPE)
            executionTime = perf_counter() - startTime
            resultOutputSave.append(ResultCommand(output=runResult.stdout.decode('utf-8'),
                                                  returnCode=runResult.returncode,
                                                  executionTime=executionTime))
            
def saveItemsToFile(items: List[Item], filename: str) -> None:
    with open(filename, 'w') as file:
        for item in items:
            dictFields = asdict(item)
            # Skip all the test related fields.
            del dictFields['testResult']
            del dictFields['testOutput']
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
            if 'validationCmd' in filtered_dict:
                filtered_dict['validationCmd'] = ValidationCommand(**filtered_dict['validationCmd'])
            
            appendItem = Item(**filtered_dict)
            
            # Clean the item before saving it.
            if appendItem.repetitions < 0:
                appendItem.repetitions = 0
            if appendItem.result:
                appendItem.result = appendItem.result[:appendItem.repetitions] 
            if appendItem.testResult:
                appendItem.testResult = appendItem.testResult[:appendItem.repetitions] 

            items.append(appendItem)
        return items