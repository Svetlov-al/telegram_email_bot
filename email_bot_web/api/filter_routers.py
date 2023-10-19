from http import HTTPStatus

from api.services.box_filter_services import BoxFilterService
from api.services.email_services import EmailBoxService
from django.http import HttpRequest, JsonResponse
from email_service.schema import (
    BoxFilterSchema,
    CreateBoxFilterRequest,
    EmailBoxRequestSchema,
    ErrorSchema,
)
from infrastructure.exceptions import (
    BoxFilterCreationError,
    BoxFiltersNotFoundError,
    EmailBoxByUsernameNotFoundError,
)
from ninja import Router

emails = EmailBoxService
filters = BoxFilterService


router_filter = Router(tags=['Фильтры'])


@router_filter.post(
    '/create',
    response={
        HTTPStatus.CREATED: dict[str, str],
        HTTPStatus.BAD_REQUEST: ErrorSchema
    },
    summary='Создание фильтра для почтового ящика',
)
async def create_filter_for_box(request: HttpRequest, data: CreateBoxFilterRequest):
    try:
        await filters.create_box_filter(data.telegram_id, data.email_username,
                                        data.filter_data.filter_value, data.filter_data.filter_name)
        return JsonResponse({'success': 'Filter created successfully'}, status=HTTPStatus.CREATED)
    except BoxFilterCreationError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.BAD_REQUEST)
    except EmailBoxByUsernameNotFoundError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)


@router_filter.post(
    '',
    response={
        HTTPStatus.OK: list[BoxFilterSchema],
        HTTPStatus.NOT_FOUND: ErrorSchema
    },
    summary='Получение всех фильтров для почтового ящика',
)
async def get_filters_for_box(request: HttpRequest, data: EmailBoxRequestSchema):
    try:
        filters_schemas = await filters.get_filters_for_user_and_email(data.telegram_id, data.email_username)
        return filters_schemas

    except BoxFiltersNotFoundError as e:
        return JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)
