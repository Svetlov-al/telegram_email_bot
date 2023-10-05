from http import HTTPStatus

from api.services.email_services import EmailBoxService
from api.services.user_services import BotUserService
from django.http import HttpRequest, JsonResponse
from email_service.schema import (
    BotUserCreateSchema,
    BotUserOutSchema,
    EmailBoxOutputSchema,
    ErrorSchema,
)
from infrastucture.exceptions import UserAlreadyExistsError, UserNotFoundError
from ninja import Router

bot_users = BotUserService
emails = EmailBoxService

router_user = Router(tags=['Пользователи'])


@router_user.post(
    '',
    response={HTTPStatus.CREATED: BotUserOutSchema,
              HTTPStatus.BAD_REQUEST: ErrorSchema
              },
    summary='Создание пользователя',
)
async def create_user(request: HttpRequest, data: BotUserCreateSchema):
    try:
        user = await bot_users.create_bot_user(data.telegram_id)
        return JsonResponse(BotUserOutSchema.from_orm(user).dict(), status=HTTPStatus.CREATED)
    except UserAlreadyExistsError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.BAD_REQUEST)
    except UserNotFoundError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)


@router_user.get(
    '/{telegram_id}',
    response={
        HTTPStatus.OK: BotUserOutSchema,
        HTTPStatus.BAD_REQUEST: ErrorSchema
    },
    summary='Получение пользователя по ID',
)
async def get_user(request: HttpRequest, telegram_id: int):
    try:
        user = await bot_users.get_bot_user(telegram_id)
        return JsonResponse(BotUserOutSchema.from_orm(user).dict(), status=HTTPStatus.OK)
    except UserNotFoundError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)


@router_user.get(
    '/{telegram_id}/boxes',
    response={
        HTTPStatus.OK: list[EmailBoxOutputSchema],
        HTTPStatus.NOT_FOUND: ErrorSchema
    },
    summary='Получение пользователя со всеми ящиками и фильтрами',
)
async def get_user_with_boxes(request: HttpRequest, telegram_id: int):
    try:
        return await emails.get_email_boxes_for_user(telegram_id)
    except UserNotFoundError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)
