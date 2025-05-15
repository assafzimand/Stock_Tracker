from fastapi import APIRouter, HTTPException
from app.api.schemas import PatternRequest, PatternResponse
from app.analysis.detector import detect_cup_and_handle_wrapper


router = APIRouter()

@router.post("/detect-pattern", response_model=PatternResponse)
def detect_pattern(request: PatternRequest):
    try:
        detected, plot_b64 = detect_cup_and_handle_wrapper(
            company=request.company,
            include_plot=request.include_plot
        )
        return PatternResponse(
            company=request.company,
            pattern_detected=detected,
            plot_base64=plot_b64 if request.include_plot else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))