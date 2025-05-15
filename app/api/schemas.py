from pydantic import BaseModel, Field
from typing import Optional


class PatternRequest(BaseModel):
    company: str = Field(..., description="Must be one of: Apple, Microsoft, Alphabet, Amazon, Nvidia, Meta, Tesla")
    include_plot: Optional[bool] = False


class PatternResponse(BaseModel):
    company: str
    pattern_detected: bool
    plot_base64: Optional[str] = None
    