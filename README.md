# PyFyzz: Python Package Analyzer and Fuzzer

PyFyzz is a powerful tool designed to analyze Python packages, generate detailed insights into their structure, and fuzz test their methods and functions. By automatically generating and applying various inputs to the methods/functions within a package, PyFyzz helps identify potential vulnerabilities or areas where the code might fail when exposed to unexpected inputs.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Command-Line Options](#command-line-options)
  - [Example Usage](#example-usage)
- [Components](#components)
  - [Package Analysis](#package-analysis)
  - [Fuzz Testing](#fuzz-testing)
  - [Result Exporting](#result-exporting)
- [Data Classes](#data-classes)
  - [ParameterInfo](#parameterinfo)
  - [MethodInfo](#methodinfo)
  - [ClassInfo](#classinfo)
  - [ModuleInfo](#moduleinfo)
  - [PackageInfo](#packageinfo)
  - [TestCase](#testcase)
  - [MethodResult](#methodresult)
  - [FuzzResult](#fuzzresult)
- [Contributing](#contributing)
- [License](#license)

## Features

 - **Package Analysis**: Analyze a Python package or module to identify its classes, methods, functions, and their respective parameters.
 - **Fuzz Testing**: Automatically generate various inputs for methods and functions, testing their robustness against unexpected inputs.
 - **Result Exporting**: Export detailed analysis and fuzzing results to JSON or YAML format for further processing or documentation.
 - **Configurable Options**: Optionally ignore private methods/functions and choose the output format for the results.

## Installation

To install PyFyzz, you can clone the repository and install the dependencies:

```bash
git clone https://github.com/yourusername/pyfyzz.git
cd pyfyzz
pip install -r requirements.txt
```

## Usage

### Command-Line Options

- `--package_name` / `-p`: The name of the Python package to analyze (required).
- `--output_format` / `-o`: The format for the output file (`json` or `yaml`) (required).
- `--ignore_private` / `-i`: Optional flag to ignore methods or functions that begin with `_` or `__`.

### Example Usage

Analyze a package named `mypackage` and export the results to a YAML file, ignoring private methods/functions:

```bash
python -m pyfyzz.main -p mypackage -o yaml -i
 ```

Analyze a package named `mypackage` and export the results to a JSON file, including all methods/functions:

```bash
python -m pyfyzz.main -p mypackage -o json
```

## Components

### Package Analysis

The package analysis is performed by the `PythonPackageAnalyzer` class, which inspects the specified package/module and gathers information about its structure. This includes identifying classes, methods, functions, parameters, and their types.

### Fuzz Testing

The fuzzing process is handled by the `Fuzzer` class, which generates random inputs for the identified methods/functions and executes them to identify potential issues. The results of the fuzzing process are then collected, summarized, and can be exported for further analysis.

### Result Exporting

The `FileExporter` class is responsible for exporting the analysis and fuzzing results to JSON or YAML files. These files contain structured data that can be easily consumed by other tools or used for documentation purposes.

## Data Classes

The following data classes are used to structure the analysis and fuzzing results:

### ParameterInfo

```python
@dataclass
class ParameterInfo:
    name: str
    kind: str
    default: Optional[str] = None
    param_type: Optional[str] = None
```
 - **name**: The name of the parameter.
 - **kind**: The kind of the parameter (e.g., positional, keyword).
 - **default**: The default value of the parameter, if any.
 - **param_type**: The expected type of the parameter.

### MethodInfo

```python
@dataclass
class MethodInfo:
    name: str
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
```
- **name**: The name of the method.
- **parameters**: A list of `ParameterInfo` objects representing the parameters of the method.
- **return_type**: The expected return type of the method.

### ClassInfo

```python
@dataclass
class ClassInfo:
    name: str
    methods: Dict[str, List[ParameterInfo]] = field(default_factory=dict)
```
- **name**: The name of the class.
- **methods**: A dictionary mapping method names to `MethodInfo` objects.

### ModuleInfo
```python
@dataclass
class ModuleInfo:
    name: str
    classes: Dict[str, Dict[str, List[ParameterInfo]]] = field(default_factory=dict)
    functions: List[str] = field(default_factory=list)
```
- **name**: The name of the module.
- **classes**: A dictionary mapping class names to `ClassInfo` objects.
- **functions**: A list of function names within the module.

### PackageInfo
```python
@dataclass
class PackageInfo:
    name: str
    modules: Dict[str, Dict[str, Dict[str, List[ParameterInfo]]]] = field(default_factory=dict)
```
- **name**: The name of the package.
- **modules**: A dictionary mapping module names to `ModuleInfo` objects.

### TestCase

```python
@dataclass
class TestCase:
    inputs: Dict[str, any]
    return_value: Optional[any] = None
    exception: Optional[str] = None
```
- **inputs**: A dictionary of inputs used during the fuzzing process.
- **return_value**: The return value of the method/function when executed with the given inputs.
- **exception**: Any exception encountered during the execution.

### MethodResult

```python
@dataclass
class MethodResult:
    method_name: str
    test_cases: List[TestCase] = field(default_factory=list)
```
- **method_name**: The name of the method/function being tested.
- **test_cases**: A list of `TestCase` objects representing each test case executed.

### FuzzResult

```python
@dataclass
class FuzzResult:
    package_name: str
    method_results: List[MethodResult] = field(default_factory=list)
```

- **package_name**: The name of the package being fuzzed.
- **method_results**: A list of `MethodResult` objects representing the results of fuzzing each method/function.

## Contributing

Contributions are welcome! Please fork the repository, make your changes, and submit a pull request. Ensure your code follows best practices and includes tests where applicable.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.