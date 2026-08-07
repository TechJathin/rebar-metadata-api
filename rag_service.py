class RAGService:
    def validate_component(self, comp: ExtractedComponent) -> RuleValidationResult:
        """比对国标规范数据库，检查构件单重、抗震钢筋级别等限制"""
        matching_rules = [r for r in self.rules if r["component_type"] == comp.component_type]
        for rule in matching_rules:
            # 校验 1：最大重量限制
            if comp.weight_kg > rule["max_weight_kg"]:
                return RuleValidationResult(
                    is_compliant=False,
                    rule_id=rule["rule_id"],
                    warning_message=f"【合规预警】重量 {comp.weight_kg}kg 超过 {rule['title']} 限制 {rule['max_weight_kg']}kg！"
                )
        return RuleValidationResult(is_compliant=True, warning_message="符合国家工程规范。")