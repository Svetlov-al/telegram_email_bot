from http import HTTPStatus

from api.services.box_filter_services import BoxFilterService
from api.services.email_services import EmailBoxService
from api.services.exceptions import (
    EmailAlreadyListeningError,
    EmailBoxByUsernameNotFoundError,
    EmailBoxWithFiltersAlreadyExist,
    EmailBoxWithFiltersCreationError,
    EmailListeningError,
    EmailServiceSlugDoesNotExist,
    EmailServicesNotFoundError,
    UserDataNotFoundError,
)
from django.http import HttpRequest, JsonResponse
from email_service.schema import (
    EmailBoxCreateSchema,
    EmailBoxOutputSchema,
    EmailBoxRequestSchema,
    EmailServiceSchema,
    ErrorSchema,
)
from ninja import Router

emails = EmailBoxService
filters = BoxFilterService

router_email = Router(tags=['Почтовые ящики'])


@router_email.post(
    '',
    response={
        HTTPStatus.CREATED: dict,
        HTTPStatus.BAD_REQUEST: ErrorSchema
    },
    summary='Создание почтового ящика',
)
async def create_emailbox(request: HttpRequest, data: EmailBoxCreateSchema):
    try:
        await emails.create_email_box_with_filters(data)
        return JsonResponse({'success': 'Email box created successfully'}, status=HTTPStatus.CREATED)
    except EmailBoxWithFiltersCreationError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.BAD_REQUEST)
    except EmailBoxWithFiltersAlreadyExist as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.BAD_REQUEST)
    except EmailServiceSlugDoesNotExist as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)


@router_email.post(
    'start_listening',
    response={
        HTTPStatus.OK: dict,
        HTTPStatus.BAD_REQUEST: ErrorSchema
    },
    summary='Запуск отслеживания писем для почты',
)
async def start_listening(request: HttpRequest, data: EmailBoxRequestSchema):
    try:
        return await emails.start_listening_for_email(data.telegram_id, data.email_username)
    except UserDataNotFoundError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)
    except EmailServiceSlugDoesNotExist as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)
    except EmailAlreadyListeningError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.BAD_REQUEST)


@router_email.post(
    'stop_listening',
    response={
        HTTPStatus.OK: dict,
        HTTPStatus.BAD_REQUEST: ErrorSchema
    },
    summary='Остановка отслеживания писем для почты',
)
async def stop_listening(request: HttpRequest, data: EmailBoxRequestSchema):
    try:
        return await emails.stop_listening_for_email(data.telegram_id, data.email_username)
    except UserDataNotFoundError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)
    except EmailListeningError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.BAD_REQUEST)


@router_email.post(
    '/info',
    response={
        HTTPStatus.OK: EmailBoxOutputSchema,
        HTTPStatus.NOT_FOUND: ErrorSchema
    },
    summary='Получение информации о почтовом ящике по username для конкретного пользователя',
)
async def get_emailbox_by_username_for_user(request: HttpRequest, data: EmailBoxRequestSchema):
    try:
        email_box_data = await emails.get_email_box_by_username_for_user(data.telegram_id,
                                                                         data.email_username)
        return EmailBoxOutputSchema.from_orm(email_box_data)
    except EmailBoxByUsernameNotFoundError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)


@router_email.get(
    '/services',
    response={
        HTTPStatus.OK: list[EmailServiceSchema],
        HTTPStatus.NOT_FOUND: ErrorSchema
    },
    summary='Получение всех сервисов',
)
async def get_services(request: HttpRequest):
    try:
        services = await emails.get_all_services()
        return services
    except EmailServicesNotFoundError:
        return JsonResponse({'detail': 'Services not found'}, status=HTTPStatus.NOT_FOUND)
