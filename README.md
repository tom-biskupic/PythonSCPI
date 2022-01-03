# PythonSCPI

PythonSCPI is a python library for implementing a SCPI device. The library implements parsing of much of the basic IEE488.2-1992 SCPI command languange and provdes a simple callback interface for the application to implement the commands.

Currently PythonSCPI implements:
* Parsing of both simple and compound querys/commands (MEASURE:VOLTAGE? as well as VOLTAGE?)
* Parsing of common program headers such as *IDN? etc although the implementation is left up to the caller
* Parsing of basic program data including numerical data, string data, hex, octal and binary.
* Multiple commands per line separated by semicolon
* Abbreviations for command/query header values.

The parser does not presently support:
* Suffix data such as units (MHz). These will parse ok but will be ignorred.
* Multi-line program data (arbitrary block program data or expression_program_data). This won't parse

## Example

The following is a simple example that creates a handler that can be used to set/get the source voltage of a device. The interpreter is configured with the init string of the device which pre-defines the response to the IDN command.

The query method is called to fetch the value of the voltage and the set method sets it.

```python
from scpiparser.CommandInterpreter import CommandInterpreter
from scpiparser.CommandHandler import CommandHandler
from scpiparser.QueryHandler import QueryHandler

class VoltageHandler(QueryHandler,CommandHandler):
    def __init__(self):
        self.someValue = 12.4

    def query(self,program_header):
        return str(self.someValue)

    def set(self,program_header,program_data):
        self.someValue=program_data
        return "Ok"

ci = CommandInterpreter(manufacturer='TestInstrumentMaker',model='TestInstrument1',serial='0',firmware_version='0.1')

vh = VoltageHandler()

ci.register_query_handler("SOURCE:VOLTage",vh)
ci.register_command_handler("SOURCE:VOLTage",vh)

print(ci.process_line("*IDN?"))
print(ci.process_line("SOURCE:VOLTAGE?"))
print(ci.process_line("SOURCE:VOLTAGE 5.4e-3"))
print(ci.process_line("SOURCE:VOLT?"))
```
