from pydantic import BaseModel, ConfigDict, Field


class TelegramIDModel(BaseModel):
    telegram_id: int

    model_config = ConfigDict(from_attributes=True)


class UserModel(TelegramIDModel):
    username: str | None
    first_name: str | None
    last_name: str | None


class ProductIDModel(BaseModel):
    id: int


class ProductCategoryIDModel(BaseModel):
    category_id: int


class PaymentData(BaseModel):
    user_id: int = Field(..., description="ID пользователя Telegram")
    price: int = Field(..., description="Сумма платежа в рублях")
    product_id: int = Field(..., description="ID товара")
    paid: bool

class TicketData(BaseModel):
    namesurname: str = Field(..., description="Имя посетителя")
    year: str = Field(..., description="Курс")
    tel_number: str = Field(..., description="Номер телефона")
    payment_id: str = Field(..., description="ID платежа")
