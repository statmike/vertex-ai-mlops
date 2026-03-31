from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field

class LocationDocx(BaseModel):
    type: Literal["docx_table", "docx_paragraph"]
    paragraph_index: Optional[int] = None
    table_index: Optional[int] = None
    row_index: Optional[int] = None
    cell_index: Optional[int] = None

class LocationExcel(BaseModel):
    type: Literal["excel_cell"]
    sheet_name: str
    cell_reference: str # e.g. "B2"

class LocationPdf(BaseModel):
    type: Literal["pdf_page"]
    page_number: int

class Qualification(BaseModel):
    question_type: Optional[Literal["generic", "project_specific"]] = None
    reasoning: Optional[str] = None

class Answer(BaseModel):
    text: Optional[str] = None
    confidence_score: Optional[float] = None
    sources: List[str] = Field(default_factory=list)

class Critique(BaseModel):
    passed_quality_check: Optional[bool] = None
    feedback: Optional[str] = None
    retry_count: int = 0

class Question(BaseModel):
    id: str
    text: str
    location: Union[LocationDocx, LocationExcel, LocationPdf]
    status: Literal["extracted", "qualified", "answered", "critiqued", "completed", "error"] = "extracted"
    qualification: Qualification = Field(default_factory=Qualification)
    answer: Answer = Field(default_factory=Answer)
    critique: Critique = Field(default_factory=Critique)
    
class DocumentMetadata(BaseModel):
    filename: str
    type: Literal["docx", "excel", "pdf"]
    path: str
    status: Literal["processing", "completed", "error"] = "processing"

class RFIState(BaseModel):
    """
    The root schema representing the JSON payload passed between ADK Agents.
    """
    document: DocumentMetadata
    questions: List[Question] = Field(default_factory=list)
