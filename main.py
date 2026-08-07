from fastapi import FastAPI, Depends, HTTPException, status, Query, Response
import sqlite3
from typing import List, Optional

from database import init_db, get_db
import schemas
import crud

init_db()

app = FastAPI(
    title="工程图纸构件元数据解析与存储 API",
    description="提供工程构件数据的单条录入、批量导入、检索、汇总统计与 CSV 表格导出服务",
    version="1.1.0"
)

@app.get("/", tags=["系统"])
def read_root():
    return {
        "message": "工程图纸构件元数据解析与存储 API",
        "docs_url": "/docs",
        "status": "online",
        "version": "1.1.0"
    }

@app.post("/api/v1/components", response_model=schemas.ComponentResponse, status_code=status.HTTP_201_CREATED, tags=["构件管理"])
def create_new_component(component: schemas.ComponentCreate, conn: sqlite3.Connection = Depends(get_db)):
    """单条录入构件元数据"""
    return crud.create_component(conn=conn, component=component)

@app.post("/api/v1/components/batch", response_model=List[schemas.ComponentResponse], status_code=status.HTTP_201_CREATED, tags=["构件管理"])
def create_components_batch(components: List[schemas.ComponentCreate], conn: sqlite3.Connection = Depends(get_db)):
    """新功能 1: 批量导入多个构件 JSON 数组"""
    if not components:
        raise HTTPException(status_code=400, detail="提交的构件列表不能为空")
    return crud.create_components_batch(conn=conn, components=components)

@app.get("/api/v1/components", response_model=List[schemas.ComponentResponse], tags=["构件管理"])
def list_components(
    project_name: Optional[str] = Query(None, description="按项目名称模糊查询"),
    component_type: Optional[str] = Query(None, description="按构件类型精确查询"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """查询构件列表"""
    return crud.get_components(conn=conn, project_name=project_name, component_type=component_type)

@app.get("/api/v1/components/summary", response_model=schemas.SummaryResponse, tags=["统计与导出"])
def get_components_summary(conn: sqlite3.Connection = Depends(get_db)):
    """新功能 2: 获取汇总统计信息（总条数、总数量、总重量及分类分布）"""
    return crud.get_summary(conn=conn)

@app.get("/api/v1/components/export/csv", tags=["统计与导出"])
def export_components_csv(conn: sqlite3.Connection = Depends(get_db)):
    """新功能 3: 导出全部数据为 CSV 表格文件（自动带 UTF-8 BOM 兼容 Excel 打开）"""
    csv_data = crud.export_components_to_csv(conn=conn)
    csv_bytes = "\xef\xbb\xbf" + csv_data
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=rebar_components.csv"}
    )

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