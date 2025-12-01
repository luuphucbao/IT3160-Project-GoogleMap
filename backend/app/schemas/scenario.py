from pydantic import BaseModel
from typing import Literal, List, Optional

# --- Phần Base (Cốt lõi) ---
class Point(BaseModel):
    """Geographic point"""
    lat: float
    lng: float

class ScenarioRequest(BaseModel):
    """Dữ liệu Client gửi lên để tạo tắc đường"""
    scenario_type: Literal["rain", "block"]
    line_start: Point
    line_end: Point
    penalty_weight: float
    threshold: float = 50.0

    class Config:
        json_schema_extra = {
            "example": {
                "scenario_type": "rain",
                "line_start": {"lat": 21.0, "lng": 105.8},
                "line_end": {"lat": 21.1, "lng": 105.9},
                "penalty_weight": 50.0,
                "threshold": 50.0
            }
        }

class ScenarioResponse(BaseModel):
    """Dữ liệu trả về sau khi tạo xong"""
    message: str
    affected_edges: int
    scenario_type: str

# --- Phần Mở rộng (Để hiển thị list trên Admin UI) ---
class ScenarioItem(ScenarioRequest):
    """Dùng để hiển thị danh sách các điểm đang tắc"""
    id: int
    active: bool = True