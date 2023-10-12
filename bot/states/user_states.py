from aiogram.dispatcher.filters.state import State, StatesGroup


class BotStates(StatesGroup):
    """
    Класс BotStates представляет собой группу состояний для управления потоком диалога бота.

    Этот класс используется для определения различных этапов или состояний, в которых может находиться пользователь
    во время взаимодействия с ботом. Каждое состояние может соответствовать определенной стадии диалога или
    определенной команде, которую пользователь отправляет боту.

    Attributes:
        MainMenuState (State): Состояние, соответствующее главному меню.
        UserCreateState (State): Состояние, соответствующее процессу создания пользователя.
        EmailBoxCreateState (State): Состояние, соответствующее процессу создания почтового ящика.
        ShowCaseState (State): Состояние, соответствующее процессу показа зарегистрированных почтовых ящиков.
    """
    MainMenuState = State()
    UserCreateState = State()
    EmailBoxCreateState = State()
    ShowCaseState = State()


class RegistrationBox(StatesGroup):
    """
    Класс состояний для процесса регистрации почтового ящика в боте.

    При регистрации почтового ящика пользователь проходит через несколько этапов:
    1. Ввод имени пользователя (логина) для почтового ящика.
    2. Ввод пароля для почтового ящика.
    3. Ввод названия фильтра, чтобы определить, какие письма пользователь хочет получать.
    4. Ввод значения фильтра, чтобы уточнить, какие письма соответствуют заданному фильтру.

    Каждый этап соответствует определенному состоянию в этом классе.

    Attributes:
    - WaitForUserNameState: Ожидание ввода имени пользователя (логина) для почтового ящика.
    - WaitForPasswordState: Ожидание ввода пароля для почтового ящика.
    - WaitForFilterNameState: Ожидание ввода названия фильтра.
    - WaitForFilterValueState: Ожидание ввода значения фильтра.
    - CheckEmailInfoState: Состояние, проверки данных веденных пользователем при регистрации почтового ящика.
    - CheckFilterInfoState: Состояние, проверки данных веденных пользователем при добавлении нового фильтра.
    - WaitForNewFilterNameState: Ожидание ввода навзвания фильтра при создании нового фильтра.
    - WaitForNewFilterValueState: Ожидание ввода значения фильтра при создании нового фильтра.
    """

    WaitForUserNameState = State()
    WaitForPasswordState = State()
    WaitForFilterNameState = State()
    WaitForFilterValueState = State()
    CheckEmailInfoState = State()
    CheckFilterInfoState = State()
    WaitForNewFilterValueState = State()
    WaitForNewFilterNameState = State()
