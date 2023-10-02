class CustomError(Exception):
    """Базовый класс для всех кастомных исключений"""


class UserAlreadyExistsError(CustomError):
    """Исключение, возникающее при попытке создать пользователя, который уже существует"""


class UserNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить пользователя, которого не существует"""


class EmailBoxCreationError(CustomError):
    """Исключение, возникающее при попытке создать почтовый ящик"""


class EmailBoxWithFiltersCreationError(CustomError):
    """Исключение, возникающее при попытке создать почтовый ящик с фильтрами"""


class EmailBoxWithFiltersAlreadyExist(CustomError):
    """Исключение, возникающее при попытке создать уже существующй почтовый ящик"""


class EmailBoxNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить почтовый ящик пользователя"""


class EmailBoxesNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить список почтовых ящиков пользователя"""


class EmailBoxByUsernameNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить почтовый ящик по имени пользователя"""


class EmailServicesNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить список доступных почтовых сервисов"""


class BoxFilterCreationError(CustomError):
    """Исключениеб возникающее при попыптке создать фильтр для почтового ящика"""


class BoxFiltersNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить фильтр по почтовому ящику"""


class EmailServiceSlugDoesNotExist(CustomError):
    """Исключение возникающее при попытке получить несуществующий почтовый сервис"""


class EmailListeningError(CustomError):
    """Исключение, возникающее при проблемах с прослушиванием электронной почты."""


class EmailServiceNotFoundError(CustomError):
    """Исключение, возникающее при попытке получить несуществующий почтовый сервис."""


class UserDataNotFoundError(CustomError):
    """Исключение, возникающее при отсутствии данных пользователя в Redis."""


class EmailAlreadyListeningError(CustomError):
    """Исключение, возникающее, когда попытка начать прослушивание для уже прослушиваемого адреса электронной почты."""


class EmailNotListeningError(CustomError):
    """Исключение, возникающее, когда попытка остановить прослушивание для адреса электронной почты, который не прослушивается."""


class EmailCredentialsError(CustomError):
    """Исключение, возникающее если предоставлены не корректные данные логина и пароля от почты"""
