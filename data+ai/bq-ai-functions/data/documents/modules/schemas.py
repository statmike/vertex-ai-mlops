"""Pydantic schemas for receipt and invoice documents.

Defines the data structures used by AI.GENERATE to create synthetic documents.
Import these schemas in any notebook that needs to generate or validate
receipt/invoice data.

Usage:
    from modules.schemas import Receipt, Invoice, json_schema_prompt

    # Build a prompt that describes the expected JSON structure
    prompt_instructions = json_schema_prompt(Receipt)

    # Use with AI.GENERATE — output_schema is just a single STRING field,
    # and the prompt tells Gemini what JSON structure to return
    query = f'''
    SELECT (AI.GENERATE(
      CONCAT('Generate a receipt. ', '{prompt_instructions}'),
      output_schema => "json STRING"
    )).json AS receipt_json
    '''
"""

import json as _json
from pydantic import BaseModel, Field
from typing import Optional, Union, get_origin, get_args


# Python type → JSON schema type name
_JSON_TYPES = {str: 'string', int: 'integer', float: 'number', bool: 'boolean'}


def _json_type_str(annotation) -> str:
    """Map a Python type annotation to a human-readable JSON type description."""
    origin = get_origin(annotation)
    # Handle Optional[T]
    if origin is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return f'{_json_type_str(args[0])} or null'
    # Handle list[T]
    if origin is list:
        inner = get_args(annotation)[0]
        if isinstance(inner, type) and issubclass(inner, BaseModel):
            return f'array of objects'
        return f'array of {_JSON_TYPES.get(inner, "string")}s'
    # Handle nested BaseModel
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return 'object'
    return _JSON_TYPES.get(annotation, 'string')


def json_schema_prompt(model: type[BaseModel], indent: int = 0) -> str:
    """Generate a prompt description of the expected JSON structure.

    Produces a human-readable specification that tells Gemini exactly what
    JSON keys, types, and formats to return. Handles nested models.

    Args:
        model: A Pydantic BaseModel class.
        indent: Current indentation level (for nested models).

    Returns:
        String describing the expected JSON structure for use in prompts.
    """
    lines = []
    prefix = '  ' * indent
    for name, info in model.model_fields.items():
        annotation = info.annotation
        origin = get_origin(annotation)
        type_str = _json_type_str(annotation)
        desc = f' — {info.description}' if info.description else ''

        # Check for nested list[BaseModel]
        if origin is list:
            inner = get_args(annotation)[0]
            if isinstance(inner, type) and issubclass(inner, BaseModel):
                lines.append(f'{prefix}- "{name}": {type_str}{desc}, each with:')
                lines.append(json_schema_prompt(inner, indent + 1))
                continue

        lines.append(f'{prefix}- "{name}": ({type_str}){desc}')
    return '\n'.join(lines)


def json_example(model: type[BaseModel]) -> str:
    """Generate a minimal JSON example from a Pydantic model.

    Returns a compact JSON string showing the expected structure with
    placeholder values. Useful for including in prompts.
    """
    def _example_value(annotation):
        origin = get_origin(annotation)
        if origin is Union:
            args = [a for a in get_args(annotation) if a is not type(None)]
            if len(args) == 1:
                return _example_value(args[0])
        if origin is list:
            inner = get_args(annotation)[0]
            if isinstance(inner, type) and issubclass(inner, BaseModel):
                return [_example_obj(inner)]
            return ['...']
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return _example_obj(annotation)
        return {str: '...', int: 0, float: 0.0, bool: True}.get(annotation, '...')

    def _example_obj(m):
        return {name: _example_value(info.annotation) for name, info in m.model_fields.items()}

    return _json.dumps(_example_obj(model), indent=2)


# ---------------------------------------------------------------------------
# Receipt schemas
# ---------------------------------------------------------------------------

class ReceiptItem(BaseModel):
    """A single line item on a receipt."""
    name: str = Field(description='Short product name like a thermal receipt printout')
    qty: int = Field(description='Quantity purchased, 1-4')
    price: float = Field(description='Unit price, $0.99-$14.99')
    total: float = Field(description='Line total: qty * price')


class Receipt(BaseModel):
    """Complete receipt data for a US retail store."""
    store_name: str = Field(description='Unique store name')
    address: str = Field(description='US street address')
    city_state_zip: str = Field(description='City, state abbreviation, and ZIP')
    phone: str = Field(description='Phone number with area code')
    date: str = Field(description='Date in MM/DD/YYYY format, within the past year')
    time: str = Field(description='Time in HH:MM AM/PM format')
    items: list[ReceiptItem] = Field(description='3-15 purchased items')
    subtotal: float = Field(description='Sum of all item totals')
    tax_rate: float = Field(description='Tax rate as decimal between 0.04 and 0.10')
    tax: float = Field(description='Tax amount: round(subtotal * tax_rate, 2)')
    total: float = Field(description='Grand total: subtotal + tax')
    payment_method: str = Field(description='CASH or card type with last 4 digits like VISA ****1234')
    cash_tendered: Optional[float] = Field(default=None, description='Cash tendered if CASH payment, null for card payments')
    change: Optional[float] = Field(default=None, description='Change given if CASH payment, null for card payments')


# ---------------------------------------------------------------------------
# Invoice schemas
# ---------------------------------------------------------------------------

class InvoiceLineItem(BaseModel):
    """A single line item on an invoice."""
    description: str = Field(description='Service or product description')
    qty: int = Field(description='Quantity, hours, or months')
    unit: str = Field(description='Unit of measure: hrs, ea, or mo')
    unit_price: float = Field(description='Price per unit')
    amount: float = Field(description='Line total: qty * unit_price')


class Invoice(BaseModel):
    """Complete invoice data for a US business."""
    company_name: str = Field(description='Company name issuing the invoice')
    company_address: str = Field(description='Company street address')
    company_city_state_zip: str = Field(description='Company city, state, ZIP')
    company_phone: str = Field(description='Company phone number')
    company_email: str = Field(description='Company email address')
    client_name: str = Field(description='Client company name')
    client_contact: str = Field(description='Client contact person full name')
    client_address: str = Field(description='Client street address')
    client_city_state_zip: str = Field(description='Client city, state, ZIP')
    invoice_number: str = Field(description='Invoice number in format INV-YYYY-NNNN')
    issue_date: str = Field(description='Issue date in YYYY-MM-DD format, within past year')
    due_date: str = Field(description='Due date in YYYY-MM-DD format')
    line_items: list[InvoiceLineItem] = Field(description='2-8 professional service or product line items')
    subtotal: float = Field(description='Sum of all line item amounts')
    tax_rate: float = Field(description='Tax rate as decimal between 0.00 and 0.10')
    tax: float = Field(description='Tax amount: round(subtotal * tax_rate, 2)')
    total_due: float = Field(description='Total due: subtotal + tax')
    terms: str = Field(description='Payment terms: Net 15, Net 30, Net 45, Net 60, or Net 90')
    notes: str = Field(description='Short professional closing note or empty string')
