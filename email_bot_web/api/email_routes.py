from http import HTTPStatus

from api.services.box_filter_services import BoxFilterService
from api.services.email_services import EmailBoxService
from api.services.exceptions import (
    EmailBoxByUsernameNotFoundError,
    EmailBoxWithFiltersCreationError,
    EmailServicesNotFoundError,
)
from django.http import HttpRequest
from email_domain.schema import (
    EmailBoxCreateSchema,
    EmailBoxOutputSchema,
    EmailBoxRequestSchema,
    EmailServiceSchema,
    ErrorSchema,
)
from ninja import Router, responses

emails = EmailBoxService
filters = BoxFilterService

router_email = Router(tags=['Почтовые ящики'])


@router_email.post('/emailboxes',
                   response={
                       HTTPStatus.CREATED: dict,
                       HTTPStatus.BAD_REQUEST: ErrorSchema},
                   summary='Создание почтового ящика')
async def create_emailbox(request: HttpRequest, data: EmailBoxCreateSchema):
    try:
        await emails.create_email_box_with_filters(data)
        return responses.JsonResponse({'success': 'Email box created successfully'}, status=HTTPStatus.CREATED)
    except EmailBoxWithFiltersCreationError as e:
        return responses.JsonResponse({'detail': str(e)}, status=HTTPStatus.BAD_REQUEST)


@router_email.post('/emailboxes/info',
                   response={HTTPStatus.OK: EmailBoxOutputSchema,
                             HTTPStatus.NOT_FOUND: ErrorSchema},
                   summary='Получение информации о почтовом ящике по username для конкретного пользователя')
async def get_emailbox_by_username_for_user(request: HttpRequest, data: EmailBoxRequestSchema):
    try:
        email_box_data = await emails.get_email_box_by_username_for_user(data.telegram_id,
                                                                         data.email_username)
        return EmailBoxOutputSchema.from_orm(email_box_data)
    except EmailBoxByUsernameNotFoundError as e:
        return responses.JsonResponse({'detail': str(e)}, status=HTTPStatus.NOT_FOUND)


@router_email.get('/services',
                  response={
                      HTTPStatus.OK: list[EmailServiceSchema],
                      HTTPStatus.NOT_FOUND: ErrorSchema},
                  summary='Получение всех сервисов')
async def get_services(request: HttpRequest):
    try:
        return await emails.get_all_services()
    except EmailServicesNotFoundError:
        return responses.JsonResponse({'detail': 'Services not found'}, status=HTTPStatus.NOT_FOUND)
