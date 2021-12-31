

class CommandHandler():
    def __init__(self):
        pass

    #
    # Takes an array of strings ad the program header. These correspond
    # to the colon separated command name like SOURCE:VOLTAGE which would 
    # become an array of two strings
    #
    # The argument is passed as program data and includes the value 
    # after applying unit scaling
    #
    def set(self,program_header,program_data):
        pass

class PrintHandler(CommandHandler):
    def set(self,program_header,program_data):
        print("Command = "+program_header+" Args="+program_data)
        return "Ok"
