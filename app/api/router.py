from fastapi import APIRouter, HTTPException
from app.api.schemas import PatternRequest, PatternResponse
from app.analysis.detector import detect_cup_and_handle_wrapper
from app.config.constants import STOCK_SYMBOLS


router = APIRouter()

@router.post("/detect-pattern", response_model=PatternResponse)
def detect_pattern(request: PatternRequest):
    """
    Detects the 'cup and handle' pattern for a given stock.

    Args:
        request (PatternRequest): The request object containing the company name and whether to
        include a plot.

    Returns:
        PatternResponse: The response object containing the company name, whether the pattern was
        detected, and the plot in base64 format if requested.
    """
    # List of valid company names derived from STOCK_SYMBOLS
    valid_companies = [name.lower() for name in STOCK_SYMBOLS.values()]

    # Normalize company name to lowercase
    company_name = request.company.lower()

    # Validate company name
    if company_name not in valid_companies:
        raise HTTPException(
            status_code=400, detail="Invalid company name provided."
        )

    # Normalize include_plot to boolean
    include_plot_str = str(request.include_plot).lower()

    # Validate include_plot
    if include_plot_str not in ["true", "false"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid value for include_plot. Use 'true' or 'false'."
        )

    include_plot = include_plot_str == 'true'

    try:
        detected, plot_b64 = detect_cup_and_handle_wrapper(
            company=company_name,
            include_plot=include_plot
        )
        return PatternResponse(
            company=request.company,
            pattern_detected=detected,
            plot_base64=plot_b64 if include_plot else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))