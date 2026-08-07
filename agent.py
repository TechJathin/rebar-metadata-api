class RebarAgent:
    def process_unstructured_text(self, text: str, db_conn: sqlite3.Connection) -> AgentParseResult:
        extracted_components = self._parse_text_to_components(text)
        validation_results = [rag_service.validate_component(c) for c in extracted_components]
        
        has_non_compliant = any(not v.is_compliant for v in validation_results)

        # 智能体自主决策分支
        if has_non_compliant:
            return AgentParseResult(
                extracted_components=extracted_components,
                validation_results=validation_results,
                requires_human_review=True,  # 打上待人工复核标记，拒绝直接入库
                summary_message="【Agent 决策】检测到构件不符合工程规范，已暂存并标记为待人工复核，未直接入库。"
            )
        else:
            # 合规：自动调用第一阶段开发的数据库 Tool 批量入库！
            components_create = [ComponentCreate(**c.dict()) for c in extracted_components]
            crud.create_components_batch(conn=db_conn, components=components_create)
            return AgentParseResult(
                extracted_components=extracted_components,
                validation_results=validation_results,
                requires_human_review=False,
                summary_message=f"【Agent 自动决策】合规校验通过！自动调用数据库 Tool 将 {len(extracted_components)} 条构件录入数据库。"
            )