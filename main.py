from fastapi import FastAPI, Depends, HTTPException, status, Query
import sqlite3
from typing import List, Optional

from database import init_db, get_db
import schemas
import crud

# 启动时建立数据库表
init_db()

app = FastAPI(
    title="工程图纸构件元数据 API",
    description="提供工程构件数据的录入、校验与检索服务",
    version="1.0.0"
)

@app.get("/", tags=["系统"])
def read_root():
    return {"message": "工程图纸构件元数据 API", "docs_url": "/docs", "status": "online"}

@app.post("/api/v1/components", response_model=schemas.ComponentResponse, status_code=status.HTTP_201_CREATED, tags=["构件管理"])
def create_new_component(component: schemas.ComponentCreate, conn: sqlite3.Connection = Depends(get_db)):
    return crud.create_component(conn=conn, component=component)

@app.get("/api/v1/components", response_model=List[schemas.ComponentResponse], tags=["构件管理"])
def list_components(
    project_name: Optional[str] = Query(None, description="按项目名称模糊查询"),
    component_type: Optional[str] = Query(None, description="按构件类型精确查询"),
    conn: sqlite3.Connection = Depends(get_db)
):
    return crud.get_components(conn=conn, project_name=project_name, component_type=component_type)

@app.get("/api/v1/components/{component_id}", response_model=schemas.ComponentResponse, tags=["构件管理"])
def get_component(component_id: int, conn: sqlite3.Connection = Depends(get_db)):
    db_component = crud.get_component_by_id(conn=conn, component_id=component_id)
    if not db_component:
        raise HTTPException(status_code=404, detail=f"未找到 ID 为 {component_id} 的构件记录")
    return db_component

@app.delete("/api/v1/components/{component_id}", tags=["构件管理"])
def remove_component(component_id: int, conn: sqlite3.Connection = Depends(get_db)):
    success = crud.delete_component(conn=conn, component_id=component_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"未找到 ID 为 {component_id} 的构件记录")
    return {"message": f"ID 为 {component_id} 的构件记录已成功删除"}