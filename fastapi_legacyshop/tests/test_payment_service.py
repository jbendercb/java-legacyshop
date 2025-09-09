import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from app.services.payment_service import PaymentService
from app.models.payment import Payment, PaymentStatus
from app.exceptions import PaymentError, PaymentGatewayError


@pytest.mark.asyncio
async def test_authorize_payment_success(db_session):
    service = PaymentService(db_session)
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "transaction_id": "txn_123",
            "message": "Payment authorized"
        }
        mock_post.return_value = mock_response
        
        result = await service.authorize_payment(
            order_id=1,
            amount=Decimal("100.00"),
            card_number="4111111111111111",
            expiry_month=12,
            expiry_year=2025,
            cvv="123"
        )
        
        assert result.status == PaymentStatus.AUTHORIZED
        assert result.external_payment_id == "txn_123"
        assert result.amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_authorize_payment_4xx_error(db_session):
    service = PaymentService(db_session)
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "success": False,
            "message": "Invalid card number"
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(PaymentError) as exc_info:
            await service.authorize_payment(
                order_id=1,
                amount=Decimal("100.00"),
                card_number="invalid",
                expiry_month=12,
                expiry_year=2025,
                cvv="123"
            )
        
        assert "Invalid card number" in str(exc_info.value)


@pytest.mark.asyncio
async def test_authorize_payment_5xx_retry(db_session):
    service = PaymentService(db_session)
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.json.return_value = {
            "success": False,
            "message": "Internal server error"
        }
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "success": True,
            "transaction_id": "txn_retry_123",
            "message": "Payment authorized"
        }
        
        mock_post.side_effect = [mock_response_fail, mock_response_success]
        
        result = await service.authorize_payment(
            order_id=1,
            amount=Decimal("100.00"),
            card_number="4111111111111111",
            expiry_month=12,
            expiry_year=2025,
            cvv="123"
        )
        
        assert result.status == PaymentStatus.AUTHORIZED
        assert result.external_payment_id == "txn_retry_123"
        assert mock_post.call_count == 2  # Verify retry happened


@pytest.mark.asyncio
async def test_authorize_payment_5xx_retry_exhausted(db_session):
    service = PaymentService(db_session)
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.json.return_value = {
            "success": False,
            "message": "Bad gateway"
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(PaymentGatewayError) as exc_info:
            await service.authorize_payment(
                order_id=1,
                amount=Decimal("100.00"),
                card_number="4111111111111111",
                expiry_month=12,
                expiry_year=2025,
                cvv="123"
            )
        
        assert "Bad gateway" in str(exc_info.value)
        assert mock_post.call_count == 2  # Initial call + 1 retry
