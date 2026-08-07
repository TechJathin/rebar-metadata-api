import sys, os, sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agent import rebar_agent

def run_evaluation():
    print("🚀 开始运行 Agent 构件提取与合规校验 Evals 评估")
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE rebar_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT NOT NULL, drawing_id TEXT NOT NULL,
        component_type TEXT NOT NULL, specification TEXT NOT NULL, quantity INTEGER NOT NULL, weight_kg REAL NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()

    res1 = rebar_agent.process_unstructured_text("长江大桥一标段 DWG-2026-001 主梁 HRB400E Φ22 10 1500.5kg", conn)
    assert len(res1.extracted_components) == 1 and not res1.requires_human_review, "测试 1 失败"

    res2 = rebar_agent.process_unstructured_text("长江大桥二标段 DWG-2026-002 主梁 HRB400E Φ25 5 9500.0kg", conn)
    assert res2.requires_human_review, "测试 2 失败"

    print("📊 Evals 评估通过率: 100.0% (2/2)")

if __name__ == "__main__":
    run_evaluation()