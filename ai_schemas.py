from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedComponent(BaseModel):
    project_name: str = Field(..., description="工程项目名称")
    drawing_id: str = Field(..., description="图纸编号")
    component_type: str = Field(..., description="构件类型（如主梁/框架柱/剪力墙）")
    specification: str = Field(..., description="钢筋/构件规格型号")
    quantity: int = Field(default=1, ge=1, description="数量")
    weight_kg: float = Field(..., gt=0, description="重量 (kg)")

class RuleValidationResult(BaseModel):
    is_compliant: bool = Field(..., description="是否符合国家工程规范")
    rule_id: Optional[str] = Field(None, description="匹配到的规范编号")
    warning_message: Optional[str] = Field(None, description="合规预警/修改建议")

class AgentParseResult(BaseModel):
    extracted_components: List[ExtractedComponent]
    confidence_score: float
    validation_results: List[RuleValidationResult]
    requires_human_review: bool = Field(..., description="是否需要人工复核")
    summary_message: str = Field(..., description="Agent 决策总结")