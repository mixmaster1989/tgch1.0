class Block:
    def __init__(self, type, params=None):
        """
        Инициализация блока
        
        Args:
            type (str): Тип блока
            params (dict, optional): Параметры блока. По умолчанию None.
        """
        self.type = type
        self.params = params or {}
    
    def get_data(self):
        """
        Получение данных блока
        
        Returns:
            dict: Данные блока
        """
        return {
            "type": self.type,
            "params": self.params
        }
    
    def update_param(self, name, value):
        """
        Обновление параметра блока
        
        Args:
            name (str): Имя параметра
            value: Значение параметра
        """
        self.params[name] = value
    
    def duplicate(self):
        """
        Создает копию блока с теми же параметрами
        
        Returns:
            Block: Новый блок с теми же параметрами
        """
        return Block(self.type, self.params.copy())