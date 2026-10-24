import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Union

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

compliance_dir = backend_dir / "compliance"
if str(compliance_dir) not in sys.path:
    sys.path.insert(0, str(compliance_dir))

from compliance_service import check_product_compliance

router = APIRouter(prefix="/compliance", tags=["Compliance Services"])

class ComplianceCheckRequest(BaseModel):
    product_name: str = Field(..., description="Product name or BIS Standard number (e.g. 'Food Mixer', 'Pressure Cooker')")

class ComplianceTestItem(BaseModel):
    clause: Optional[str] = None
    test_name: Optional[str] = None
    test_type: Optional[str] = None
    requirement: Optional[str] = None

class ComplianceDocumentItem(BaseModel):
    document: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

class ComplianceReportResponse(BaseModel):
    product_name: str
    compliance_status: str
    standard_number: Optional[str] = None
    document_title: str
    title_en: Optional[str] = None
    title_hi: Optional[str] = None
    certification_scheme: str
    is_mandatory: Optional[bool] = True
    qco_notice: Optional[str] = None
    mandatory_tests: List[Union[ComplianceTestItem, Dict[str, Any], str]] = []
    required_documents: List[Union[ComplianceDocumentItem, Dict[str, Any], str]] = []
    marking_requirements: str

@router.post("/check", response_model=ComplianceReportResponse)
def get_compliance_report(req: ComplianceCheckRequest):
    """
    Generate structured BIS Product Compliance & Certification Intelligence Report.
    """
    if not req.product_name or not req.product_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product name cannot be empty."
        )

    try:
        report = check_product_compliance(req.product_name.strip())
        return ComplianceReportResponse(**report)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance check error: {str(e)}"
        )
