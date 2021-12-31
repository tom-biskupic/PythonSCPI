# PythonSCPI

PythonSCPI is a python library for implementing a SCPI device. The library implements parsing of much of the basic IEE488.2-1992 SCPI command languange and provdes a simple callback interface for the application to implement the commands.

Currently PythonSCPI implements:
* Parsing of both simple and compound querys/commands (MEASURE:VOLTAGE? as well as VOLTAGE?)
* Parsing of common program headers such as *IDN? etc although the implementation is left up to the caller
* Parsing of basic program data including numerical data, string data, hex, octal and binary.
* Multiple commands per line separated by semicolon

The parser does not presently support:
* Suffix data such as units (MHz). These will parse ok but will be ignorred.
* Multi-line program data (arbitrary block program data or expression_program_data). This won't parse

## Example

```python

from SCPIParser import 
```
