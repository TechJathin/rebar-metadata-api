from pydantic import BaseModel, Field

class ComponentBase(BaseModel):
    project_name: str = Field(..., example="长江大桥一标段", description="工程项目名称")
    drawing_id: str = Field(..., example="DWG-2026-001", description="图纸编号")
    component_type: str = Field(..., example="主梁", description="构件类型")
    specification: str = Field(..., example="HRB400E Φ22", description="规格型号")
    quantity: int = Field(default=1, ge=1, description="数量，必须 >= 1")
    weight_kg: float = Field(..., gt=0, description="重量 (kg)，必须 > 0")

class ComponentCreate(ComponentBase):
    pass

class ComponentResponse(ComponentBase):
    id: int
    created_at: str

    class Config:
        orm_mode = True