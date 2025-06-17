class Block:
    def __init__(self, block_type, params=None):
        """
        Инициализация блока
        
        Args:
            block_type (str): Тип блока
            params (dict, optional): Параметры блока. По умолчанию None.
        """
        self.block_type = block_type
        self.params = params or {}
    
    def get_data(self):
        """
        Получение данных блока
        
        Returns:
            dict: Данные блока
        """
        return {
            "block_type": self.block_type,
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
        return Block(self.block_type, self.params.copy())