# package imports for this work
import subprocess, typing
from google import genai
import pydantic

# what project are we working in?
PROJECT_ID = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True, check=True).stdout.strip()
PROJECT_ID

# setup google genai SDK
client = genai.Client(vertexai = True, project = PROJECT_ID, location = 'us-central1')

# setup the schemas for information we want to create
class Address(pydantic.BaseModel):
    street: str = pydantic.Field(description = 'The street address which might be across two lines.')
    city: str = pydantic.Field(description = 'The city part of an address with appropriate punctuation.')
    state: str = pydantic.Field(description = 'The state part of an address presented as a two letter abbreviation.')
    zip_code: str = pydantic.Field(description = 'The zip-5 or zip-9 code part of an address.')

    @pydantic.field_validator('state')
    def check_state_abbreviation(cls, value):
        if len(value) != 2:
            raise ValueError('State abbreviation must be two letters.')
        return value.upper()
    
    @pydantic.field_validator('zip_code')
    def check_zip_code(cls, value):
        if not (len(value) == 5 or len(value) == 10 and value[5] == '-'):
            raise ValueError('Zip code must be in the format XXXXX or XXXXX-XXXX.')
        return value

class Company(pydantic.BaseModel):
    company_name: str = pydantic.Field(description = 'The name of the company.')
    address: Address
    phone_number: typing.Optional[str] = pydantic.Field(description = 'The phone number of the company in the format XXX-XXX-XXXX.')
    email_address: pydantic.EmailStr = pydantic.Field(description = 'The email address of the company.')

    @pydantic.field_validator('phone_number')
    def check_phone_number(cls, value):
        if value is not None and len(value) != 12:
            raise ValueError('Phone number must be in the format XXX-XXX-XXXX.')
        return value

class LineItem(pydantic.BaseModel):
    item_sku: str = pydantic.Field(description="The Stock Keeping Unit (SKU) of the item.")
    item_description: str = pydantic.Field(description="A detailed description of the item.")
    unit_price: float = pydantic.Field(description="The price per unit of the item.")
    quantity: int = pydantic.Field(description="The number of units of the item.")
    list_price: float = pydantic.Field(description="The total price for the line item (unit_price * quantity).")
    currency: str = pydantic.Field(description="The currency code (e.g., USD, EUR).")
    discount_rate: typing.Optional[float] = pydantic.Field(default=0.0, description="The discount rate applied to the item, if any (e.g., 0.1 for 10%).")
    tax_rate: typing.Optional[float] = pydantic.Field(default=0.0, description="The tax rate applied to the item, if any (e.g., 0.08 for 8%).")
    item_id: typing.Optional[str] = pydantic.Field(default=None, description="A unique identifier for the line item.")

    @pydantic.field_validator('quantity')
    def check_quantity(cls, value):
        if value <= 0:
            raise ValueError('Quantity must be greater than zero.')
        return value

    @pydantic.field_validator('unit_price', 'list_price')
    def check_price(cls, value):
        if value < 0:
            raise ValueError('Price must be non-negative.')
        return value

    @pydantic.field_validator('discount_rate', 'tax_rate')
    def check_rate(cls, value):
        if not (0.0 <= value <= 1.0):
            raise ValueError('Rate must be between 0.0 and 1.0.')
        return value

    @pydantic.model_validator(mode='after')
    def check_list_price(self):
        calculated_list_price = self.unit_price * self.quantity
        if calculated_list_price != self.list_price:
            raise ValueError(f'List price ({self.list_price}) does not match calculated list price ({calculated_list_price}).')
        return self

class Invoice(pydantic.BaseModel):
    vendor: Company = pydantic.Field(description="The company that is the vendor for the invoice.")
    customer: Company = pydantic.Field(description="The company that is the customer for the invoice.")
    invoice_number: str = pydantic.Field(description="The unique identifier for the invoice.")
    invoice_date: date = pydantic.Field(description="The date the invoice was issued.")
    due_date: typing.Optional[date] = pydantic.Field(default=None, description="The date the invoice is due.")
    line_items: typing.List[LineItem] = pydantic.Field(description="The list of line items for the invoice.")
    subtotal: float = pydantic.Field(description="The sum of the list_price for all line items.")
    tax: float = pydantic.Field(description="The total tax for the invoice.")
    total: float = pydantic.Field(description="The total amount due for the invoice.")
    currency: str = pydantic.Field(description="The currency code for the invoice (e.g., USD, EUR).")

    @pydantic.model_validator(mode='after')
    def check_totals(self):
        calculated_subtotal = sum(item.list_price for item in self.line_items)
        if calculated_subtotal != self.subtotal:
            raise ValueError(f'Subtotal ({self.subtotal}) does not match calculated subtotal ({calculated_subtotal}).')

        calculated_tax = sum(item.list_price * item.tax_rate for item in self.line_items if item.tax_rate)
        if calculated_tax != self.tax:
            raise ValueError(f'Tax ({self.tax}) does not match calculated tax ({calculated_tax}).')

        calculated_total = self.subtotal + self.tax
        if calculated_total != self.total:
            raise ValueError(f'Total ({self.total}) does not match calculated total ({calculated_total}).')
        
        if any(item.currency != self.currency for item in self.line_items):
            raise ValueError(f'All line items must have the same currency as the invoice.')

        return self
