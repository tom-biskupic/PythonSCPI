
from lark import Lark,Token
if __package__:
    from .QueryHandler import QueryHandler
    from .CommandHandler import PrintHandler
    from .QueryHandler import IDNHandler
else:
    from QueryHandler import QueryHandler
    from CommandHandler import PrintHandler
    from QueryHandler import IDNHandler


class CommandInterpreter:

    SCPI_GRAMMAR = """
        start: program_message_unit ( PROGRAM_MESSAGE_SEPARATOR WS_INLINE? program_message_unit )*
        program_message_unit: command_message_unit | query_message_unit
        command_message_unit: command_program_header [ WS_INLINE program_data ( PROGRAM_DATA_SEPARATOR program_data )*]
        query_message_unit: query_program_header ( WS_INLINE program_data (PROGRAM_DATA_SEPARATOR program_data )*)?
        
        program_data :  character_program_data 
                        | DECIMAL_NUMERIC_PROGRAM_DATA suffix_program_data?
                        | NON_DECIMAL_NUMERIC_DATA
                        | STRING_PROGRAM_DATA
                        | suffix_program_data
                        
        //              | arbitrary_block_program_data
        //              | expression_program_data
                        
        command_program_header: WS_INLINE? simple_command_program_header 
                                | compound_command_program_header 
                                | common_command_program_header
                                
        simple_command_program_header: PROGRAM_MNEMONIC
        
        compound_command_program_header: ":"? PROGRAM_MNEMONIC ( ":" PROGRAM_MNEMONIC )+
        common_command_program_header: "*" PROGRAM_MNEMONIC
        
        query_program_header:   WS_INLINE? simple_query_program_header
                                | compound_query_program_header
                                | common_query_program_header
                                
        simple_query_program_header: PROGRAM_MNEMONIC "?"
        compound_query_program_header: ":"? PROGRAM_MNEMONIC (":" PROGRAM_MNEMONIC)+ "?"
        common_query_program_header: "*" PROGRAM_MNEMONIC "?"
        
        
        character_program_data: PROGRAM_MNEMONIC
        
        suffix_program_data: WS_INLINE? "/"? (suffix_program_data_middle ( ("/"|".") suffix_program_data_middle )*)?
        suffix_program_data_middle: (suffix_prog_data_with_mult | suffix_prog_data_without_mult)
        suffix_prog_data_with_mult: SUFFIX_MULT (PROGRAM_MNEMONIC "-"? _DIGIT)?
        suffix_prog_data_without_mult: PROGRAM_MNEMONIC ("-"? _DIGIT)?
        
        SUFFIX_MULT: "EX"|"PE"|"T"|"G"|"MA"|"K"|"M"|"U"|"N"|"P"|"F"|"A"
        
        SUFFIX_UNIT: /[a-zA-Z]{1,4}/
        
        NON_DECIMAL_NUMERIC_DATA: "#" (( "H"|"h" _HEX_DIGIT+ ) | ( "Q"|"q" _OCTAL_DIGIT+ ) | ( "B"|"b" _BINARY_DIGIT+ ))
                                    
        
        STRING_PROGRAM_DATA: ( SINGLE_QUOTED_STRING | DOUBLE_QUOTED_STRING )
        SINGLE_QUOTED_STRING: "\'" ( "\'\'" | /[^']/ )* "\'"
        DOUBLE_QUOTED_STRING: "\\"" ( "\\"\\"" | /[^\\"]/ )* "\\""
        
        DECIMAL_NUMERIC_PROGRAM_DATA: MANTISSA WS? EXPONENT?
        MANTISSA: ("+"|"-")? ( _DIGIT* "." _DIGIT+) | (_DIGIT+ ("." _DIGIT*)? )
        EXPONENT: ("E"|"e") WS? ("+"|"-")? _DIGIT+
        _DIGIT: "0".."9"
        _HEX_DIGIT: "a".."f"|"A".."F"|"0".."9"
        _BINARY_DIGIT: "0".."1"
        _OCTAL_DIGIT: "0".."7"
        
        PROGRAM_MESSAGE_SEPARATOR: WS_INLINE? ";"
        PROGRAM_DATA_SEPARATOR : WS_INLINE? "," WS_INLINE?
        PROGRAM_MNEMONIC : /[A-Za-z]+[A-Za-z0-9_]*/
                
        %import common.WS_INLINE
        %import common.WS
        %import common.DECIMAL
        %import common.NEWLINE
        %ignore WS_INLINE
        %ignore WS
    """

    
    #
    # The manufacturer, model, serial and firmware values are used to build the 
    # response to the IDN command. This can be handled by the application by overridding
    # the IDN handler also
    #
    def __init__(self,manufacturer='Runcible Software Pty Ltd',model='Not Defined',serial='0',firmware_version='0'):
        # print(self.SCPI_GRAMMAR)
        # self.parser = Lark(self.SCPI_GRAMMAR, parser='earley', lexer="standard")
        self.parser = Lark(self.SCPI_GRAMMAR)
        self.command_handlers = {}
        self.query_handlers = {}
        self.register_query_handler("IDN",IDNHandler(manufacturer,model,serial,firmware_version))
        pass

    def register_command_handler(self,key,handler):
        self.command_handlers[key] = handler

    def register_query_handler(self,key,handler):
        self.query_handlers[key] = handler


    def process_line(self, command_string):
        parse_tree = self.parser.parse(command_string)
        results = ""
        for command in parse_tree.children:
            if not isinstance(command,Token):
                results += self._process(command.children[0]) + "\n"
        return results

    def _process(self,command):
        if command.data == 'query_message_unit':
            return self._process_query(command.children[0].children[0])
        else:
            return self._process_command(command)

    def _process_query(self,command):
        # print("Query = "+str(command))
        query_name = ""  
        if command.data == 'compound_query_program_header':
            query_name = self._join_compound_name(command.children)
        elif command.data == 'common_query_program_header':
            # print("Processing common query - \""+str(command.children[0])+"\"")
            query_name = str(command.children[0])
        else:
            query_name = command.children[0].children[0]

        if query_name in self.query_handlers:
            # print("Processing query - "+query_name)
            handler = self.query_handlers[query_name]
            return handler.query(query_name)
        else:
            # print("No handler for query "+query_name)
            return "Invalid query"

    def _process_command(self,command):
        # print("Command = "+str(command))
        header = command.children[0].children[0]
        if header.data == 'compound_command_program_header':
            command_name = self._join_compound_name(header.children)
        else:
            command_name = header.children[0].value

        if command_name in self.command_handlers:
            # print("Processing command - "+command_name)
            handler = self.command_handlers[command_name]

            if command.children[2].data == 'program_data':
                arg = self._parse_program_data(command.children[2])
            else:
                arg = "no Idea"
            return handler.set(command_name,arg)
        else:
            print("No handler for query "+command_name)
            return "Invalid query"

    def _parse_program_data(self,program_data):
        # print(program_data)
        arg_type = program_data.children[0].type
        arg_value = program_data.children[0].value
        if arg_type == 'DECIMAL_NUMERIC_PROGRAM_DATA':
            return float(arg_value)
        elif arg_type == 'NON_DECIMAL_NUMERIC_DATA':
            return self._parse_non_decimal(arg_value)
        elif arg_type == 'STRING_PROGRAM_DATA':
            string_body = arg_value[1:len(arg_value)-1]
            if arg_value[0] == '\'':
                string_body = string_body.replace('\'\'','\'')
            else:
                string_body = string_body.replace('\"\"','\"')
            return string_body
        else:
            return arg_value

    def _parse_non_decimal(self,arg_value):
        value_body = arg_value[2:len(arg_value)]
        type_char = arg_value[1].upper()
        if  type_char == 'H':
            as_hex_string = "0x"+value_body
            return int(as_hex_string,16)
        elif type_char == 'B':
            as_binary_string = "0b"+value_body
            return int(as_binary_string,2)
        elif type_char == 'Q':
            as_octal_string = "0o"+value_body
            return int(as_octal_string,8)

    def _join_compound_name(self,names):
        # print("Names "+names)
        compound_name=""
        for name in names:
            if compound_name != '':
                compound_name += ":"
            compound_name += name
        return compound_name

#ci = CommandInterpreter()
# ci.register_command_handler("SOURCE:VOLTAGE",PrintHandler())

# print(ci.process_line("*IDN?"))
# # print(ci.process_line("*RST"))
# print(ci.process_line(":VOLT:MEAS?"))
# # print(ci.process_line("*SRE 128"))
# # print(ci.process_line(":SENSe:TINTerval:ARM:ESTOP:LAYer1:TIMer 10.0MHz"))
# # print(ci.process_line(":STAT:OPER:PTR 0; NTR 16"))
#print(ci.process_line("SOURCE:VOLTAGE 2.0e-2"))
