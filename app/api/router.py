from fastapi import APIRouter, HTTPException
from app.api.schemas import PatternRequest, PatternResponse
from app.analysis.detector import detect_cup_and_handle_wrapper
from app.config.constants import STOCK_SYMBOLS
import logging


router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

@router.post("/detect-pattern", response_model=PatternResponse)
def detect_pattern(request: PatternRequest):
    """
    Detects the 'cup and handle' pattern for a given stock.

    Args:
        request (PatternRequest): The request object containing the company name or stock symbol
        and whether to include a plot.

    Returns:
        PatternResponse: The response object containing the company name, whether the pattern was
        detected, and the plot in base64 format if requested.
    """
    logging.info(
        f"Received request for company or symbol: {request.company}, "
        f"include_plot: {request.include_plot}"
    )

    # Normalize input to lowercase
    input_name = request.company.lower()

    # List of valid company names and symbols derived from STOCK_SYMBOLS
    valid_companies = {
        name.lower(): company for company, name in STOCK_SYMBOLS.items()
    }
    valid_symbols = {
        symbol.lower(): symbol for symbol in STOCK_SYMBOLS.keys()
    }

    # Determine if input is a company name or symbol
    if input_name in valid_companies:
        symbol = valid_companies[input_name]
    elif input_name in valid_symbols:
        symbol = valid_symbols[input_name]
    else:
        raise HTTPException(status_code=400, detail="Invalid company name or symbol provided.")

    # Get canonical company name
    company_name = STOCK_SYMBOLS[symbol]


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
        logging.info(
            f"Pattern detection completed for company: {request.company}, "
            f"detected: {detected}"
        )
        return PatternResponse(
            company=request.company,
            pattern_detected=detected,
            plot_base64=plot_b64 if include_plot else None
        )
    except ValueError as e:
        logging.error(
            f"Error during pattern detection for company: {request.company}, "
            f"error: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))