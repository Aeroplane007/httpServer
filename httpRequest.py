

class httpRequest():

    def __init__(self, req_type: str, action: str ,parameters: dict = {}):
        self.req_type = req_type
        self.action = action
        self.parameters = parameters


    def GetReqType(self):
        return self.req_type

    def GetAction(self):
        return self.action
    
    def GetParameter(self,parameter):
        return self.parameters[parameter]
