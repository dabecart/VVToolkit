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
import os

from datetime import datetime

class TestResult:
    NOTRUN = 0
    OK = 1
    ERROR = 2
    UNDEFINED = 3
    NOT_ALL_OK = 4

    @classmethod
    def getResultColor(cls, result):
        mapping = {
            TestResult.OK:         '#17e5ae',
            TestResult.ERROR:      '#e51760',
            TestResult.UNDEFINED:  '#f7c90f',
            TestResult.NOT_ALL_OK: '#f7c90f',
        }
        return mapping.get(result, '#000000')

    @classmethod
    def toExcelColor(cls, result):
        mapping = {
            TestResult.OK:         'green',
            TestResult.ERROR:      'red',
            TestResult.UNDEFINED:  'yellow',
            TestResult.NOT_ALL_OK: 'yellow',
        }            
        return mapping.get(result, 'red')

    @classmethod
    def toString(cls, result):
        mapping = {
            TestResult.OK:         'Successful',
            TestResult.ERROR:      'Unsuccessful',
            TestResult.UNDEFINED:  'Undefined result',
            TestResult.NOT_ALL_OK: 'Not all tests were successful',
        }            
        return mapping.get(result, 'Undefined result type')
    
class Operation():
    operations: List[str] =["Same output", "Conditional output"]
    SAME = 0
    COMPARISON = 1

@dataclass(eq=True)
class ResultCommand:
    output: str             = field(default="")
    returnCode: int         = field(default=None)
    executionTime: float    = field(default=0, compare=False)
    timeOfExecution : str   = field(default="", compare=False)

    result: int             = field(default=TestResult.NOTRUN, compare=False)

    def deltaOfExecution(self, startExecutionTime: str):
        t = datetime.strptime(self.timeOfExecution, "%d/%m/%Y %H:%M:%S.%f")
        t0 = datetime.strptime(startExecutionTime, "%d/%m/%Y %H:%M:%S.%f")
        return str(t - t0)

@dataclass
class ValidationCommand:
    operators: ClassVar[List[str]]  = ["==", "<>", "<", ">", "<=", ">=", "contain", "not contain"]

    operation: int      = field(default=Operation.SAME)
    operator: str       = field(default='==')
    operatorVal: str    = field(default='')

    def usesBuildOutput(self):
        return self.operation == Operation.SAME

    def validate(self, originalResult: ResultCommand, testResult: ResultCommand, prevTestResult: TestResult) -> TestResult:
        match self.operation:
            case Operation.SAME:
                currentTestResult = originalResult==testResult
            case Operation.COMPARISON:
                output = testResult.output
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
                    case 'contain':
                        currentTestResult = str(val) in str(output)
                    case "not contain":
                        currentTestResult = str(val) not in str(output)
                    case _:
                        print(f"Undefined operator {self.operator} on validate")
                        currentTestResult = TestResult.ERROR
                        # This will make it so that the result is undefined.
                        prevTestResult = TestResult.UNDEFINED
            case _:
                print(f"Undefined operation {self.operation}")
                currentTestResult = False

        currentTestResult = TestResult.OK if currentTestResult else TestResult.ERROR
        # Set the test result on its class.
        testResult.result = currentTestResult

        if prevTestResult is TestResult.NOTRUN or currentTestResult == prevTestResult:
            return currentTestResult
        else:
            # Not all tests run successfully.
            return TestResult.NOT_ALL_OK

    def toString(self) -> str:
        match self.operation:
            case Operation.SAME:
                ret =  "The test output <b>must be the same</b> as the original output."
            case Operation.COMPARISON:
                match self.operator:
                    case '==':
                        ret =  f"Output must be <b>equal to</b> {self.operatorVal}."
                    case '<>':
                        ret =  f"Output must be <b>different than</b> {self.operatorVal}."
                    case '>':
                        ret =  f"Output must be <b>greater than</b> {self.operatorVal}."
                    case '<':
                        ret =  f"Output must be <b>less than</b> {self.operatorVal}."
                    case '>=':
                        ret =  f"Output must be <b>greater than or equal to</b> {self.operatorVal}."
                    case '<=':
                        ret =  f"Output must be <b>lesser than or equal to</b> {self.operatorVal}."
                    case 'contain':
                        ret =  f"Output <b>must contain</b> {self.operatorVal}."
                    case "not contain":
                        ret =  f"Output <b>must not contain</b> {self.operatorVal}."
                    case _:
                        print(f"Undefined operator {self.operator} on toString")
                        ret = ""
            case _:
                ret =  f"Undefined operation {self.operation} on toString"
        return ret

    # Returns the function before this one changing the color of bold words.
    def validationToString(self, result: TestResult | None = None) -> str:
        # Get the text.
        ret: str = self.toString()
        if result is not None:
            # Add color to signal the reason the test successes or fails.
            ret = ret.replace('<b>', f'<span style="color:{TestResult.getResultColor(result)}; font-weight:bold;">', 1)
            ret = ret.replace('</b>', '</span>', 1)
        return ret
    
    # Similar to before but the text changes depending on the result.
    def resultToString(self, result: TestResult | None = None) -> str:
        # Get the text.
        ret: str = self.toString()

        # Change "must be" for "is" or "is not".
        match result:
            case TestResult.OK:
                ret = ret.replace('must be', '<b>is</b>', 1)
                # If no "must be" is found, then it may be a single "must".
                ret = ret.replace('must', 'does')

            case TestResult.ERROR:
                ret = ret.replace('must be', '<b>is not</b>', 1)
                # If no "must be" is found, then it may be a single "must".
                ret = ret.replace('must not', 'does not')

            case TestResult.UNDEFINED:
                ret = "This test result <b>was not conclusive</b>."
            
            case TestResult.NOT_ALL_OK:
                ret = "This test result had <b>mixed answers</b> and therefore it is not conclusive."
            
            case _:
                print(f"Unexpected result \"{result}\" on resultToString.")

        if result is not None:
            # Add color to signal the reason the test successes or fails.
            ret = ret.replace('<b>', f'<span style="color:{TestResult.getResultColor(result)}; font-weight:bold;">', 2)
            ret = ret.replace('</b>', '</span>', 2)
        return ret

@dataclass(eq=True)
class Item:
    runningDirectory : ClassVar[str]    = ""

    id: int                             = field(default=-1)
    name: str                           = field(default="Undeclared")
    category: str                       = field(default="Undetermined")
    repetitions: int                    = field(default=1)
    enabled: bool                       = field(default=True)
    runcode: str                        = field(default="")
    result: List[ResultCommand]         = field(default_factory=lambda: [])
    validationCmd: ValidationCommand    = field(default_factory=lambda: ValidationCommand())
    
    testResult: int                     = field(default=TestResult.NOTRUN)
    testOutput: List[ResultCommand]     = field(default_factory=lambda: [])
    wasTestRepeated: int                = field(default=0)

    def __lt__(self, other):
        return self.id < other.id
    
    def clearTest(self):
        self.testResult = TestResult.NOTRUN
        self.testOutput.clear()

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

    # May throw a CalledProcessError exception in case the command is not OK.
    def _execute(self, resultOutputSave):
        commandArgs = shlex.split(self.runcode)
        # So that the windowed application doesn't open a terminal to run the code on Windows (nt).
        # Taken from here:
        # https://code.activestate.com/recipes/409002-launching-a-subprocess-without-a-console-window/
        if os.name == 'nt':
            startupInfo = subprocess.STARTUPINFO()
            startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        for _ in range(self.repetitions):
            tOfExec = datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")
            if os.name == 'nt': 
                startTime = perf_counter()
                runResult = subprocess.run(commandArgs,
                                        stdout   = subprocess.PIPE, 
                                        stderr   = subprocess.PIPE,
                                        cwd      = Item.runningDirectory,
                                        startupinfo = startupInfo)
                executionTime = perf_counter() - startTime
            else:
                startTime = perf_counter()
                runResult = subprocess.run(commandArgs,
                                        stdout   = subprocess.PIPE, 
                                        stderr   = subprocess.PIPE,
                                        cwd      = Item.runningDirectory)
                executionTime = perf_counter() - startTime
    
            # Taken from here: 
            # https://stackoverflow.com/questions/24849998/how-to-catch-exception-output-from-python-subprocess-check-output
            if runResult.stderr:
                raise subprocess.CalledProcessError(
                    returncode = runResult.returncode,
                    cmd = runResult.args,
                    stderr = runResult.stderr
                )
            
            resultOutputSave.append(ResultCommand(output=runResult.stdout.decode('utf-8'),
                                                  returnCode=runResult.returncode,
                                                  executionTime=executionTime,
                                                  timeOfExecution=tOfExec))

@dataclass(eq=True)
class TestDataFields:
    name: str      = field(default="")
    project: str   = field(default="")
    date: str      = field(default="", compare=False)
    testCount: str = field(default="", compare=False)
    author: str    = field(default="")
    conductor: str = field(default="")

    def missingFields(self) -> List[str]:
        classDict = asdict(self)
        return [key for key, val in classDict.items() if val == ""]

def areItemsSaved(testDataFields: TestDataFields, items: List[Item], filename: str) -> bool:
    with open(filename, 'r') as file:
        jsonList: List = json.load(file)
        
        testFields = {field.name for field in fields(TestDataFields)}
        # The test fields should be the first on the file.
        filteredDict = {k: v for k, v in jsonList[0].items() if k in testFields}
        testFields = TestDataFields(**filteredDict)
        if testDataFields != testFields:
            return False

        # Create a set of field names from the Item dataclass to filter unexpected arguments.
        itemFields = {field.name for field in fields(Item)}
        for index, itemDict in enumerate(jsonList[1]):
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

def saveItemsToFile(testDataFields: TestDataFields, items: List[Item], filename: str) -> None:
    with open(filename, 'w') as file:
        outputItems = []
        for item in items:
            dictFields = asdict(item)
            # Skip all the test related fields.
            del dictFields['testResult']
            del dictFields['testOutput']
            outputItems.append(dictFields)
            
        json.dump([asdict(testDataFields), outputItems], file)

def saveTestToFile(testDataFields: TestDataFields, items: List[Item], filename: str) -> None:
    with open(filename, 'w') as file:
        json.dump([asdict(testDataFields), [asdict(item) for item in items]], file)

def loadItemsFromFile(filename: str) -> List[Item]:
    with open(filename, 'r') as file:
        jsonList: List = json.load(file)
        
        testFields = {field.name for field in fields(TestDataFields)}
        # The test fields should be the first on the file.
        filteredDict = {k: v for k, v in jsonList[0].items() if k in testFields}
        testFields = TestDataFields(**filteredDict)

        # Create a set of field names from the Item dataclass to filter unexpected arguments.
        itemFields = {field.name for field in fields(Item)}
        items = []
        for itemDict in jsonList[1]:
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
        return (testFields, items)
    
def loadTestFromFile(filename: str):
    with open(filename, 'r') as file:
        jsonList: List = json.load(file)
        
        testFields = {field.name for field in fields(TestDataFields)}
        # The test fields should be the first on the file.
        filteredDict = {k: v for k, v in jsonList[0].items() if k in testFields}
        testFields = TestDataFields(**filteredDict)

        # Create a set of field names from the Item dataclass to filter unexpected arguments.
        itemFields = {field.name for field in fields(Item)}
        items = []
        for itemDict in jsonList[1]:
            # Filter the dictionary to only include valid fields.
            filteredDict = {k: v for k, v in itemDict.items() if k in itemFields}

            # Handle the result field types.
            if 'result' in filteredDict:
                filteredDict['result'] = [ResultCommand(**res) for res in filteredDict['result']]
            if 'validationCmd' in filteredDict:
                filteredDict['validationCmd'] = ValidationCommand(**filteredDict['validationCmd'])
            if 'testOutput' in filteredDict:
                filteredDict['testOutput'] = [ResultCommand(**res) for res in filteredDict['testOutput']]

            appendItem = Item(**filteredDict)
            items.append(appendItem)
        return (testFields, items)