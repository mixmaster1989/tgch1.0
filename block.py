class Block:
    def __init__(self, type):
        self.type = type
        self.params = {}
    
    def get_data(self):
        return {
            "type": self.type,
            "params": self.params
        } 