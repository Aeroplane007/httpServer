class client():

    def __init__(self, connection, cookie_id: str = "0" , receiver=""):
        self.connection = connection
        self.cookie_id = cookie_id
        self.receiver = receiver

    def SetReceiver(self, receiver):
        self.receiver = receiver

    def SetCookie(self, cookie):
        self.cookie_id = cookie


    def GetReceiver(self):
        return self.receiver
        
    def GetConnection(self):
        return self.connection
    
    def GetCookie(self):
        return self.cookie_id