
from lark import Lark,Token
from lark.exceptions import UnexpectedInput

if __package__:
    from .QueryHandler import QueryHandler
    from .CommandHandler import PrintHandler
    from .QueryHandler import IDNHandler
    from .HandlerMap import HandlerMap
else:
    from QueryHandler import QueryHandler
    from CommandHandler import PrintHandler
    from QueryHandler import IDNHandler
    from HandlerMap import HandlerMap

class ParserContext:
    def __init__(self):
        self.is_first = True
        self.command_scope = ""
    def get_is_first(self):
        return self.is_first
    def set_is_first(self,value):
        self.is_first = value
    def get_command_scope(self):
        return self.command_scope
    def set_command_scope(self,value):
        self.command_scope = value

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
                        
        command_program_header: WS_INLINE? SIMPE_COMMAND_PROGRAM_HEADER 
                                | COMPOUND_COMMAND_PROGRAM_HEADER 
                                | COMMON_COMMAND_PROGRAM_HEADER
                                
        SIMPE_COMMAND_PROGRAM_HEADER: PROGRAM_MNEMONIC
        
        COMPOUND_COMMAND_PROGRAM_HEADER: ":"? PROGRAM_MNEMONIC ( ":" PROGRAM_MNEMONIC )+
        COMMON_COMMAND_PROGRAM_HEADER: "*" PROGRAM_MNEMONIC
        
        query_program_header:   WS_INLINE? SIMPLE_QUERY_PROGRAM_HEADER
                                | COMPOUND_QUERY_PROGRAM_HEADER
                                | COMMON_QUERY_PROGRAM_HEADER
                                
        SIMPLE_QUERY_PROGRAM_HEADER: PROGRAM_MNEMONIC "?"
        COMPOUND_QUERY_PROGRAM_HEADER: ":"? PROGRAM_MNEMONIC (":" PROGRAM_MNEMONIC)+ "?"
        COMMON_QUERY_PROGRAM_HEADER: "*" PROGRAM_MNEMONIC "?"
        
        
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
        self.command_handlers = HandlerMap()
        self.query_handlers = HandlerMap()
        self.register_query_handler("*IDN",IDNHandler(manufacturer,model,serial,firmware_version))
        pass

    def register_command_handler(self,key,handler):
        self.command_handlers.register_handler(key,handler)

    def register_query_handler(self,key,handler):
        self.query_handlers.register_handler(key,handler)

    def process_line(self, command_string):
        if not command_string or command_string.isspace():
            return "\n"
        try:
            parse_tree = self.parser.parse(command_string)
        except UnexpectedInput as err:
            return str(err) + err.get_context(text=command_string,span=200)
        results = ""
        context = ParserContext()
        for command in parse_tree.children:
            if not isinstance(command,Token):
                results += self._process(command.children[0],context) + "\n"
                context.set_is_first(False)
        return results

    def _process(self,command,context):
        if command.data == 'query_message_unit':
            return self._process_query(command.children[0].children[0],context)
        else:
            return self._process_command(command,context)

    def _process_query(self,query,context):
        # print("Query = "+str(command))
        query_name = query.value[:-1]
        if context.get_is_first():
            query_parts = query_name.split(":")
            context.set_command_scope(":".join(query_parts[:-1]))

        if not context.get_is_first() and context.get_command_scope() and query_name[0] != ":":
            query_name = context.get_command_scope() + ":" + query_name

        handler = self.query_handlers.find_handler(query_name)
        if handler:
            return handler.query(query_name)
        else:
            # print("No handler for query "+query_name)
            return "Invalid query"

    def _process_command(self,command,context):
        # print("Command = "+str(command))
        header_token = command.children[0].children[0]
        command_name = header_token.value
        if context.get_is_first():
            query_parts = command_name.split(":")
            context.set_command_scope(":".join(query_parts[:-1]))

        if not context.get_is_first() and context.get_command_scope() and command_name[0] != ":":
            command_name = context.get_command_scope() + ":" + command_name
        
        if command_name[0] == ":":
            command_name = command_name[1:]
            
        handler = self.command_handlers.find_handler(command_name)
        if handler:
            if command.children[2].data == 'program_data':
                arg = self._parse_program_data(command.children[2])
            else:
                arg = "no Idea"
            return handler.set(command_name,arg)
        else:
            #print("No handler for query "+command_name)
            return "Invalid command"

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
#print(ci.process_line("this is junk"))