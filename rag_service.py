import json, os
from typing import List, Dict
from ai_schemas import ExtractedComponent, RuleValidationResult

RULES_FILE = os.path.join(os.path.dirname(__file__), "rag", "gb_rules.json")

class RAGService:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict]:
        if os.path.exists(RULES_FILE):
            with open(RULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def validate_component(self, comp: ExtractedComponent) -> RuleValidationResult:
        matching_rules = [r for r in self.rules if r["component_type"] == comp.component_type]
        if not matching_rules:
            return RuleValidationResult(is_compliant=True, warning_message="未找到针对该构件类型的特殊限制规范，默认合规。")

        for rule in matching_rules:
            if comp.weight_kg > rule["max_weight_kg"]:
                return RuleValidationResult(
                    is_compliant=False,
                    rule_id=rule["rule_id"],
                    warning_message=f"【合规预警】构件重量 {comp.weight_kg}kg 超过 {rule['title']} 上限 {rule['max_weight_kg']}kg！"
                )
        return RuleValidationResult(is_compliant=True, rule_id=matching_rules[0]["rule_id"], warning_message="符合国家工程规范。")

rag_service = RAGService()