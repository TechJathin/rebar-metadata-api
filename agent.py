import re, sqlite3
from typing import List
from ai_schemas import ExtractedComponent, RuleValidationResult, AgentParseResult
from schemas import ComponentCreate
from rag_service import rag_service
import crud

class RebarAgent:
    def process_unstructured_text(self, text: str, db_conn: sqlite3.Connection) -> AgentParseResult:
        extracted_components = self._parse_text_to_components(text)
        
        if not extracted_components:
            return AgentParseResult(
                extracted_components=[], confidence_score=0.0, validation_results=[],
                requires_human_review=True, summary_message="未识别出有效构件，需人工复核。"
            )

        validation_results = [rag_service.validate_component(c) for c in extracted_components]
        has_non_compliant = any(not v.is_compliant for v in validation_results)

        if has_non_compliant:
            return AgentParseResult(
                extracted_components=extracted_components, confidence_score=0.85,
                validation_results=validation_results, requires_human_review=True,
                summary_message="【Agent 决策】检测到构件不符合工程规范，已暂存并标记为待人工复核，未直接入库。"
            )
        else:
            components_create = [ComponentCreate(**(c.dict() if hasattr(c, "dict") else c.model_dump())) for c in extracted_components]
            crud.create_components_batch(conn=db_conn, components=components_create)
            return AgentParseResult(
                extracted_components=extracted_components, confidence_score=0.98,
                validation_results=validation_results, requires_human_review=False,
                summary_message=f"【Agent 自动决策】合规校验通过！自动调用数据库 Tool 将 {len(extracted_components)} 条构件录入数据库。"
            )

    def _parse_text_to_components(self, text: str) -> List[ExtractedComponent]:
        components = []
        pattern = r"(?P<proj>[\u4e00-\u9fa5A-Za-z0-9]+)\s+(?P<dwg>DWG-[A-Za-z0-9-]+)\s+(?P<type>主梁|框架柱|剪力墙|板|桥墩)\s+(?P<spec>[A-Za-z0-9Φ\s]+?)\s+(?P<qty>\d+)(?:件|根|套)?\s+(?P<weight>\d+(?:\.\d+)?)(?:kg|千克|公斤|吨)?"
        matches = re.finditer(pattern, text)
        for match in matches:
            d = match.groupdict()
            components.append(ExtractedComponent(
                project_name=d["proj"].strip(), drawing_id=d["dwg"].strip(),
                component_type=d["type"].strip(), specification=d["spec"].strip(),
                quantity=int(d["qty"]), weight_kg=float(d["weight"])
            ))
        return components

rebar_agent = RebarAgent()