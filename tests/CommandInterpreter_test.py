import unittest

from context import CommandInterpreter

from unittest.mock import patch
from unittest.mock import mock_open, Mock, MagicMock

class CommandInterpreterTest(unittest.TestCase):

    def test_idn_defaults(self):
        fixture = CommandInterpreter("TestOrg","TestModel")
        self.assertEqual(fixture.process_line("*IDN?"),"TestOrg,TestModel,0,0\n")

    def test_idn(self):
        fixture = CommandInterpreter("TestOrg","TestModel","12.0","1.0")
        self.assertEqual(fixture.process_line("*IDN?"),"TestOrg,TestModel,12.0,1.0\n")

    def test_no_query_handler(self):
        fixture = CommandInterpreter()
        self.assertEqual(fixture.process_line("something?"),"Invalid query\n")

    def test_syntax_error(self):
        fixture = CommandInterpreter()
        self.assertEqual(fixture.process_line("This is crap")[0:19],"No terminal matches")

    def test_empty(self):
        fixture = CommandInterpreter()
        self.assertEqual(fixture.process_line("\t\t\t  "),"\n")

    def test_user_query_handler(self):
        mock_handler = Mock()
        fixture = CommandInterpreter()
        mock_handler.query.return_value = "12.4"
        fixture.register_query_handler("VOLT",mock_handler)
        self.assertEqual(fixture.process_line("VOLT?"),"12.4\n")
        mock_handler.query.assert_called_with("VOLT")

    def test_compound_user_query_handler(self):
        mock_handler = Mock()
        fixture = CommandInterpreter()
        mock_handler.query.return_value = "12.4"
        fixture.register_query_handler("VOLT:MEASURE",mock_handler)
        self.assertEqual(fixture.process_line("VOLT:MEASURE?"),"12.4\n")
        mock_handler.query.assert_called_with("VOLT:MEASURE")

    def test_user_set_handler_hex(self):
        self._test_user_set_handler("#h1234abcd",0x1234abcd)

    def test_user_set_handler_float(self):
        self._test_user_set_handler("12.4",12.4)

    def test_user_set_handler_float2(self):
        self._test_user_set_handler("-12.4e-5",-12.4e-5)

    def test_user_set_handler_binary(self):
        self._test_user_set_handler("#b11001111",0b11001111)

    def test_user_set_handler_octal(self):
        self._test_user_set_handler("#q01234",0o01234)

    def test_user_set_handler_single_quoted_string(self):
        self._test_user_set_handler("\'hello\'",'hello')

    def test_user_set_handler_single_quoted_string_escaping(self):
        self._test_user_set_handler("\'hello \'\'Dolly\'\'\'",'hello \'Dolly\'')

    def test_user_set_handler_double_quoted_string(self):
        self._test_user_set_handler("\"hello\"",'hello')

    def test_user_set_handler_double_quoted_string_escaping(self):
        self._test_user_set_handler("\"hello \"\"Dolly\"\"\"",'hello \"Dolly\"')

    def _test_user_set_handler(self,string_value,expected_value):
        mock_handler = Mock()
        fixture = CommandInterpreter()
        mock_handler.set.return_value = "Ok"
        fixture.register_command_handler("SOMFUNC",mock_handler)
        self.assertEqual(fixture.process_line("SOMFUNC "+string_value),"Ok\n")
        mock_handler.set.assert_called_with("SOMFUNC",expected_value)

    # def test_user_set_handler_with_suffix(self):
    #     mock_handler = Mock()
    #     fixture = CommandInterpreter()
    #     mock_handler.set.return_value = "Ok"
    #     fixture.register_command_handler("SOMFUNC",mock_handler)
    #     self.assertEqual(fixture.process_line("SOMFUNC 12.4MHz"),"Ok\n")
    #     mock_handler.set.assert_called_with("SOMFUNC",12.4)

    def test_multiple_commands(self):
        mock_handler1 = Mock()
        mock_handler2 = Mock()
        fixture = CommandInterpreter()
        mock_handler1.set.return_value = "Ok"
        mock_handler2.set.return_value = "Ok"
        fixture.register_command_handler("SOMFUNC",mock_handler1)
        fixture.register_command_handler("SOMEOTHERFUNC",mock_handler2)
        self.assertEqual(fixture.process_line("SOMFUNC 12.4; SOMEOTHERFUNC 10.0"),"Ok\nOk\n")
        mock_handler1.set.assert_called_with("SOMFUNC",12.4)
        mock_handler2.set.assert_called_with("SOMEOTHERFUNC",10.0)

    def test_multiple_queries_with_context(self):
        mock_handler1 = Mock()
        mock_handler2 = Mock()
        fixture = CommandInterpreter()
        mock_handler1.query.return_value = "10.0"
        mock_handler2.query.return_value = "12.0"
        fixture.register_query_handler("SOURCE:VOLTAGE",mock_handler1)
        fixture.register_query_handler("SOURCE:CURRENT",mock_handler2)
        self.assertEqual(fixture.process_line("SOURCE:VOLTAGE?; CURRENT?"),"10.0\n12.0\n")
        mock_handler1.query.assert_called_with("SOURCE:VOLTAGE")
        mock_handler2.query.assert_called_with("SOURCE:CURRENT")

    def test_multiple_commands_with_context(self):
        mock_handler1 = Mock()
        mock_handler2 = Mock()
        fixture = CommandInterpreter()
        mock_handler1.set.return_value = "Ok"
        mock_handler2.set.return_value = "Ok"
        fixture.register_command_handler("SOURCE:VOLTAGE",mock_handler1)
        fixture.register_command_handler("SOURCE:CURRENT",mock_handler2)
        self.assertEqual(fixture.process_line("SOURCE:VOLTAGE 12.4; CURRENT 10.0"),"Ok\nOk\n")
        mock_handler1.set.assert_called_with("SOURCE:VOLTAGE",12.4)
        mock_handler2.set.assert_called_with("SOURCE:CURRENT",10.0)

    def test_multiple_commands_with_context_override(self):
        mock_handler1 = Mock()
        mock_handler2 = Mock()
        fixture = CommandInterpreter()
        mock_handler1.set.return_value = "Ok"
        mock_handler2.set.return_value = "Ok"
        fixture.register_command_handler("SOURCE:VOLTAGE",mock_handler1)
        fixture.register_command_handler("OUTPUT:ENABLE",mock_handler2)
        self.assertEqual(fixture.process_line("SOURCE:VOLTAGE 12.4;:OUTPUT:ENABLE 1"),"Ok\nOk\n")
        mock_handler1.set.assert_called_with("SOURCE:VOLTAGE",12.4)
        mock_handler2.set.assert_called_with("OUTPUT:ENABLE",1)

if __name__ == '__main__':
    unittest.main()
