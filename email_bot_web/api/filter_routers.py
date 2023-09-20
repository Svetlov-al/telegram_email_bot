from http import HTTPStatus

from api.services.box_filter_services import BoxFilterService
from api.services.email_services import EmailBoxService
from api.services.exceptions import (
    BoxFilterCreationError,
    BoxFiltersNotFoundError,
    EmailBoxByUsernameNotFoundError,
)
from django.http import HttpRequest
from email_domain.schema import (
    BoxFilterSchema,
    CreateBoxFilterRequest,
    EmailBoxRequestSchema,
    ErrorSchema,
)
from ninja import Router, responses

emails = EmailBoxService
filters = BoxFilterService

router_filter = Router(tags=['Фильтры'])


@router_filter.post('/filters/create',
                    response={
                        HTTPStatus.CREATED: dict,
                        HTTPStatus.BAD_REQUEST: ErrorSchema},
                    summary='Создание фильтра для почтового ящика')
async def create_filter_for_box(request: HttpRequest, data: CreateBoxFilterRequest):
    try:
        email_box = await emails.get_email_box_by_username_for_user(data.telegram_id, data.email_username)
    except EmailBoxByUsernameNotFoundError as e:
        return responses.JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)

    try:
        await filters.create_box_filter(email_box, data.filter_data.filter_value, data.filter_data.filter_name)
        return responses.JsonResponse({'success': 'Filter created successfully'}, status=HTTPStatus.CREATED)
    except BoxFilterCreationError as e:
        return responses.JsonResponse({'detail': str(e)}, status=HTTPStatus.BAD_REQUEST)


@router_filter.post('/filters',
                    response={
                        HTTPStatus.OK: list[BoxFilterSchema],
                        HTTPStatus.NOT_FOUND: ErrorSchema
                    },
                    summary='Получение всех фильтров для почтового ящика')
async def get_filters_for_box(request: HttpRequest, data: EmailBoxRequestSchema):
    try:
        filters_schemas = await filters.get_filters_for_user_and_email(data.telegram_id, data.email_username)
        return filters_schemas

    except BoxFiltersNotFoundError as e:
        return responses.JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)
