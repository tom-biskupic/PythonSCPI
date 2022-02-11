

class QueryHandler():
    def __init__(self):
        pass

    #
    # Takes the command name which can be a colon seperated collection
    # of strings like VOLTAGE:MEAS
    #
    # The return value (as a string) is returned to the caller
    # as the response to this function
    #
    def query(self,program_header,call_context=None):
        pass

class IDNHandler(QueryHandler):
    def __init__(self,manufacturer,model,serial,firmware_version):
        self.result = manufacturer+","+model+","+serial+","+firmware_version
    
    def query(self,program_header,call_context=None):
        return self.result
        