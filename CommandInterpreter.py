
from lark import Lark


class CommandInterpreter:

    SCPI_GRAMMAR = """
        start: program_message_unit ( PROGRAM_MESSAGE_SEPARATOR program_message_unit )*
        program_message_unit: command_message_unit | query_message_unit
        command_message_unit: command_program_header ( program_data ( PROGRAM_DATA_SEPARATOR program_data )*)?
        query_message_unit: query_program_header ( program_data (PROGRAM_DATA_SEPARATOR program_data )*)?
        program_data :  character_program_data 
                        | DECIMAL_NUMERIC_PROGRAM_DATA suffix_program_data?
                        | NON_DECIMAL_NUMERIC_DATA
                        | STRING_PROGRAM_DATA
                        | suffix_program_data
                        
        //              | arbitrary_block_program_data
        //              | expression_program_data
                        
        command_program_header: simple_command_program_header 
                                | compound_command_program_header 
                                | common_command_program_header
                                
        simple_command_program_header: PROGRAM_MNEMONIC
        
        compound_command_program_header: ":"? PROGRAM_MNEMONIC ( ":" PROGRAM_MNEMONIC )+
        common_command_program_header: "*" PROGRAM_MNEMONIC
        
        query_program_header:   simple_query_program_header
                                | compound_query_program_header
                                | common_query_program_header
                                
        simple_query_program_header: PROGRAM_MNEMONIC "?"
        compound_query_program_header: ":"? PROGRAM_MNEMONIC (":" PROGRAM_MNEMONIC)+ "?"
        common_query_program_header: "*" PROGRAM_MNEMONIC "?"
        
        
        character_program_data: PROGRAM_MNEMONIC
        
        suffix_program_data: "/" (suffix_prog_data_with_mult | suffix_prog_data_without_mul ("/"|".")? )*
        
        suffix_prog_data_with_mult: SUFFIX_MULT (SUFFIX_UNIT "-"? _DIGIT)?
        suffix_prog_data_without_mul: SUFFIX_UNIT ("-"? _DIGIT)?
        
        SUFFIX_MULT: "EX"|"PE"|"T"|"G"|"MA"|"K"|"M"|"U"|"N"|"P"|"F"|"A"
        
        SUFFIX_UNIT: PROGRAM_MNEMONIC
        
        NON_DECIMAL_NUMERIC_DATA: "#" ( "H"|"h" _HEX_DIGIT+ ) 
                                    | ("Q"|"q" "0".."7"+ )
                                    | ("B"|"b" ("0"|"1"))+
                                    
        
        STRING_PROGRAM_DATA: _SINGLE_QUOTED_STRING | _DOUBLE_QUOTED_STRING
        _SINGLE_QUOTED_STRING: "\'" ( "\'\'" | /[^']/ )* "\'"
        _DOUBLE_QUOTED_STRING: "\"" ( "\"\"" | /[^\\"]/ )* "\""
        
        DECIMAL_NUMERIC_PROGRAM_DATA: _MANTISSA ( _EXPONENT )?
        _MANTISSA: ("+"|"-")? ( _DIGIT* "." _DIGIT+) | (_DIGIT+ "." _DIGIT*)
        _EXPONENT: ("E"|"e") ("+"|"-")? _DIGIT+
        _DIGIT: "0".."9"
        _HEX_DIGIT: "a".."f"|"A".."F"|"0".."9"
        
        PROGRAM_MESSAGE_SEPARATOR : ";"
        PROGRAM_DATA_SEPARATOR : ","
        PROGRAM_MNEMONIC : /[A-Za-z]+[A-Za-z0-9_]*/
        
        %import common.WS_INLINE
        %import common.DECIMAL
        %ignore WS_INLINE
    """

    def __init__(self):
        self.parser = Lark(self.SCPI_GRAMMAR, parser='lalr', lexer="standard")
        pass

    def process_line(self, command_string):
        return self.parser.parse(command_string)


ci = CommandInterpreter()
print ci.process_line("*IDN?")
print ci.process_line("*RST")
