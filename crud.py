import sqlite3
import csv
import io
from typing import List, Optional, Dict
from schemas import ComponentCreate
import openpyxl
import json
def export_components_to_excel(conn: sqlite3.Connection) -> bytes:
    """生成原生 .xlsx 格式的 Excel 字节流"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, project_name, drawing_id, component_type, specification, quantity, weight_kg, created_at FROM rebar_components ORDER BY id ASC")
    rows = cursor.fetchall()
    
    # 创建工作簿与工作表
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "构件数据"
    
    # 写入表头
    headers = ["ID", "项目名称", "图纸编号", "构件类型", "规格型号", "数量", "重量(kg)", "录入时间"]
    ws.append(headers)
    
    # 写入每一行数据
    for row in rows:
        ws.append(list(row))
        
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

def create_component(conn: sqlite3.Connection, component: ComponentCreate) -> Dict:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rebar_components (project_name, drawing_id, component_type, specification, quantity, weight_kg)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        component.project_name,
        component.drawing_id,
        component.component_type,
        component.specification,
        component.quantity,
        component.weight_kg
    ))
    conn.commit()
    new_id = cursor.lastrowid
    return get_component_by_id(conn, new_id)

def create_components_batch(conn: sqlite3.Connection, components: List[ComponentCreate]) -> List[Dict]:
    """1. 批量导入构件"""
    cursor = conn.cursor()
    created_ids = []
    for comp in components:
        cursor.execute("""
            INSERT INTO rebar_components (project_name, drawing_id, component_type, specification, quantity, weight_kg)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            comp.project_name,
            comp.drawing_id,
            comp.component_type,
            comp.specification,
            comp.quantity,
            comp.weight_kg
        ))
        created_ids.append(cursor.lastrowid)
    conn.commit()
    
    return [get_component_by_id(conn, cid) for cid in created_ids if cid]

def get_components(
    conn: sqlite3.Connection, 
    project_name: Optional[str] = None, 
    component_type: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[Dict]:
    cursor = conn.cursor()
    query = "SELECT * FROM rebar_components WHERE 1=1"
    params = []
    
    if project_name:
        query += " AND project_name LIKE ?"
        params.append(f"%{project_name}%")
    if component_type:
        query += " AND component_type = ?"
        params.append(component_type)
        
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, skip])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_component_by_id(conn: sqlite3.Connection, component_id: int) -> Optional[Dict]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rebar_components WHERE id = ?", (component_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def delete_component(conn: sqlite3.Connection, component_id: int) -> bool:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rebar_components WHERE id = ?", (component_id,))
    conn.commit()
    return cursor.rowcount > 0

def get_summary(conn: sqlite3.Connection) -> Dict:
    """2. 统计汇总"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            COALESCE(SUM(quantity), 0) as total_quantity,
            COALESCE(SUM(weight_kg), 0.0) as total_weight_kg
        FROM rebar_components
    """)
    overall = dict(cursor.fetchone())
    
    cursor.execute("""
        SELECT 
            component_type,
            COUNT(*) as count,
            COALESCE(SUM(quantity), 0) as total_quantity,
            COALESCE(SUM(weight_kg), 0.0) as total_weight_kg
        FROM rebar_components
        GROUP BY component_type
        ORDER BY total_weight_kg DESC
    """)
    overall["type_breakdown"] = [dict(r) for r in cursor.fetchall()]
    return overall

def export_components_to_csv(conn: sqlite3.Connection) -> str:
    """3. 导出 CSV 表格数据"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, project_name, drawing_id, component_type, specification, quantity, weight_kg, created_at FROM rebar_components ORDER BY id ASC")
    rows = cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "项目名称", "图纸编号", "构件类型", "规格型号", "数量", "重量(kg)", "录入时间"])
    for row in rows:
        writer.writerow(list(row))
    return output.getvalue()

def export_components_to_json(conn: sqlite3.Connection) -> str:
    """导出格式：将所有构件转为美化格式的 JSON 字符串"""
    rows = get_components(conn=conn, limit=10000)
    # 加上 default=str，将时间等特殊类型转为字符串，防止 500 报错
    return json.dumps(rows, ensure_ascii=False, indent=2, default=str)