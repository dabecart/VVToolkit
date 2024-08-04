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
from typing import List, ClassVar
import subprocess
import shlex    # To easily parse the arguments for a console.
from time import perf_counter
from ast import literal_eval
from re import sub

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

class TestResult:
    OK = 1
    ERROR = 2
    UNDEFINED = 3

class Operation():
    operations : List[str] =["Same output", "Conditional output"]
    SAME = 0
    COMPARISON = 1

@dataclass
class ValidationCommand:
    operators: ClassVar[List[str]]  = ["==", "<>", "<", ">", "<=", ">="]

    operation: int  = field(default=Operation.SAME)
    operator: str   = field(default='==')
    operatorVal : str = field(default='')   

    def validate(self, a : ResultCommand, b : ResultCommand, prevTestResult : TestResult) -> TestResult:
        match self.operation:
            case Operation.SAME:
                currentTestResult = a==b
            case Operation.COMPARISON:
                output = b.output
                val = self.operatorVal

                # Parse as a string literal if it's inside "".
                if self.operatorVal.startswith('"') and self.operatorVal.endswith('"'):
                    try:
                        val = str(literal_eval(self.operatorVal))
                    except:
                        pass
                else:
                    # Check if it's an integer number
                    try:
                        val = int(val)
                        output = int(output)
                    except ValueError:
                        # Check if it's a float number
                        try:
                            val = float(val)
                            output = float(output)
                        except ValueError:
                            # If it's not a string nor a number, just remove the special characters
                            # that cannot be added without the ""s from the output.
                            output = sub(r'[\x00-\x1F\x7F]', '', output)

                match self.operator:
                    case '==':
                        currentTestResult = output == val
                    case '<>':
                        currentTestResult = output != val
                    case '>':
                        currentTestResult = output > val
                    case '<':
                        currentTestResult = output < val
                    case '>=':
                        currentTestResult = output >= val
                    case '<=':
                        currentTestResult = output <= val
                    case _:
                        print(f"Undefined operator {self.operator} on validate")
                        currentTestResult = False
            case _:
                print(f"Undefined operation {self.operation}")
                currentTestResult = TestResult.ERROR

        currentTestResult = TestResult.OK if currentTestResult else TestResult.ERROR
        if prevTestResult is None or currentTestResult == prevTestResult:
            return currentTestResult
        else:
            return TestResult.UNDEFINED

    def toString(self):
        match self.operation:
            case Operation.SAME:
                return "Outputs must be the same."
            case Operation.COMPARISON:
                match self.operator:
                    case '==':
                        return f"Output must be equal to {self.operatorVal}."
                    case '<>':
                        return f"Output must be different than {self.operatorVal}."
                    case '>':
                        return f"Output must be greater than {self.operatorVal}."
                    case '<':
                        return f"Output must be less than {self.operatorVal}."
                    case '>=':
                        return f"Output must be greater than or equal to {self.operatorVal}."
                    case '<=':
                        return f"Output must be lesser than or equal to {self.operatorVal}."
                    case _:
                        print(f"Undefined operator {self.operator} on toString")
                        currentTestResult = False
            case _:
                return f"Undefined operation {self.operation} on toString"

@dataclass(eq=True)
class Item:
    id: int                             = field(default=-1)
    name: str                           = field(default="Undeclared")
    category: str                       = field(default="Undetermined")
    repetitions: int                    = field(default=1)
    enabled: bool                       = field(default=False)
    runcode: str                        = field(default="")
    result : List[ResultCommand]        = field(default_factory=lambda: [])
    validationCmd : ValidationCommand   = field(default_factory=lambda: ValidationCommand())
    
    testResult : int                    = field(default=None)
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

def areItemsSaved(items : List[Item], filename : str) -> bool:
    with open(filename, 'r') as file:
        # Create a set of field names from the dataclass
        itemFields = {field.name for field in fields(Item)}

        itemsDict = json.load(file)
        for index, itemDict in enumerate(itemsDict):
            # Filter the dictionary to only include valid fields
            filteredDict = {k: v for k, v in itemDict.items() if k in itemFields}
            # Handle the result field types.
            if 'result' in filteredDict:
                filteredDict['result'] = [ResultCommand(**res) for res in filteredDict['result']]
            if 'validationCmd' in filteredDict:
                filteredDict['validationCmd'] = ValidationCommand(**filteredDict['validationCmd'])
            appendItem = Item(**filteredDict)

            if appendItem != items[index]:
                return False
        return True

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
        # Create a set of field names from the dataclass
        itemFields = {field.name for field in fields(Item)}
        items = []

        itemsDict = json.load(file)
        for itemDict in itemsDict:
            # Filter the dictionary to only include valid fields
            filteredDict = {k: v for k, v in itemDict.items() if k in itemFields}
            # Handle the result field types.
            if 'result' in filteredDict:
                filteredDict['result'] = [ResultCommand(**res) for res in filteredDict['result']]
            if 'validationCmd' in filteredDict:
                filteredDict['validationCmd'] = ValidationCommand(**filteredDict['validationCmd'])
            
            appendItem = Item(**filteredDict)
            
            # Clean the item before saving it.
            if appendItem.repetitions < 0:
                appendItem.repetitions = 0
            if appendItem.result:
                appendItem.result = appendItem.result[:appendItem.repetitions] 
            if appendItem.testOutput:
                appendItem.testOutput = appendItem.testOutput[:appendItem.repetitions] 
            
            items.append(appendItem)
        return items