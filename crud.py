import sqlite3
from typing import List, Optional, Dict
from schemas import ComponentCreate

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