from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Header

from payment_service.application.dto import CreatePaymentInputDTO
from payment_service.presentation.api.dependencies import (
    get_provider,
    verify_api_key,
)
from payment_service.presentation.api.interfaces import UseCaseProvider
from payment_service.presentation.api.schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PaymentResponse,
)

router = APIRouter(
    prefix='/api/v1/payments',
    tags=['payments'],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    path='',
    status_code=HTTPStatus.ACCEPTED,
    response_model=CreatePaymentResponse,
)
async def create_payment(
    body: CreatePaymentRequest,
    idempotency_key: str = Header(alias='Idempotency-Key', max_length=64),
    provider: UseCaseProvider = Depends(get_provider),
) -> CreatePaymentResponse:
    use_case = provider.create_payment()
    payment = await use_case(
        data=CreatePaymentInputDTO(
            amount=body.amount,
            currency=body.currency,
            description=body.description,
            metadata=body.metadata,
            webhook_url=str(body.webhook_url),
            idempotency_key=idempotency_key,
        )
    )
    return CreatePaymentResponse.model_validate(payment)


@router.get(
    path='/{payment_id}',
    status_code=HTTPStatus.OK,
    response_model=PaymentResponse,
)
async def get_payment(
    payment_id: UUID,
    provider: UseCaseProvider = Depends(get_provider),
) -> PaymentResponse:
    use_case = provider.get_payment()
    payment = await use_case(payment_id=payment_id)
    return PaymentResponse.model_validate(payment)
