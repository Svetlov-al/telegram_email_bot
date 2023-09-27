class CustomError(Exception):
    """Базовый класс для всех кастомных исключений"""
    pass


class UserAlreadyExistsError(CustomError):
    """Исключение, возникающее при попытке создать пользователя, который уже существует"""
    pass


class UserNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить пользователя, которого не существует"""
    pass


class EmailBoxCreationError(CustomError):
    """Исключение, возникающее при попытке создать почтовый ящик"""
    pass


class EmailBoxWithFiltersCreationError(CustomError):
    """Исключение, возникающее при попытке создать почтовый ящик с фильтрами"""
    pass


class EmailBoxWithFiltersAlreadyExist(CustomError):
    """Исключение, возникающее при попытке создать уже существующй почтовый ящик"""
    pass


class EmailBoxNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить список почтовых ящиков пользователя"""
    pass


class EmailBoxesNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить список почтовых ящиков пользователя"""
    pass


class EmailBoxByUsernameNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить почтовый ящик по имени пользователя"""
    pass


class EmailServicesNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить список доступных почтовых сервисов"""
    pass


class BoxFilterCreationError(CustomError):
    """Исключениеб возникающее при попыптке создать фильтр для почтового ящика"""
    pass


class BoxFiltersNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить фильтр по почтовому ящику"""
    pass
