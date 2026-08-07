import sqlite3
from typing import List, Optional

from database import init_db, get_db
import schemas
import crud
from fastapi import FastAPI, Depends, HTTPException, status, Query, Response, UploadFile, File
import json

init_db()

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="工程图纸构件元数据解析与存储 API",
    version="v1.0.0",  # 1. 修改右上角版本号
    description="提供工程构件数据的录入、校验、检索与导出服务",
    docs_url=None      # 关闭默认 docs，使用自定义 docs
)

# 2. 自定义 /docs 页面，通过 CSS 隐藏 /openapi.json 链接
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API 文档"
    )
    # 注入 CSS 隐藏 /openapi.json 链接与 OAS 3.1 标签
    hide_link_css = """
    <style>
        .swagger-ui .info .link { display: none !important; }
    </style>
    """
    body_content = response.body.decode("utf-8").replace("</head>", f"{hide_link_css}</head>")
    return HTMLResponse(content=body_content)

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
    """导出全部数据为 CSV 文件（彻底解决 Excel 中文乱码问题）"""
    csv_text = crud.export_components_to_csv(conn=conn)
    # 使用字节串 b"\xef\xbb\xbf" 添加 BOM 标头，提示 Excel 自动使用 UTF-8 编码打开
    csv_bytes = b"\xef\xbb\xbf" + csv_text.encode("utf-8")
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

# 2. 新增文件上传接口
@app.post("/api/v1/components/upload-json", response_model=List[schemas.ComponentResponse], status_code=status.HTTP_201_CREATED, tags=["构件管理"])
async def upload_components_json_file(file: UploadFile = File(...), conn: sqlite3.Connection = Depends(get_db)):
    """选择/上传本地 .json 文件自动读取并导入构件数据"""
    # 校验文件扩展名
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="只允许上传 .json 格式的文件")
    
    # 读取文件内容并解析 JSON
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON 文件解析失败，请检查语法格式: {str(e)}")
    
    # 转换并校验数据结构
    try:
        if isinstance(data, dict):
            components_to_create = [schemas.ComponentCreate(**data)]
        elif isinstance(data, list):
            components_to_create = [schemas.ComponentCreate(**item) for item in data]
        else:
            raise HTTPException(status_code=400, detail="JSON 文件根节点必须是对象 {} 或数组 []")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"数据内容字段校验失败: {str(e)}")

    # 批量保存到数据库
    return crud.create_components_batch(conn=conn, components=components_to_create)

@app.get("/api/v1/components/export", tags=["统计与导出"])
def export_components_file(
    format: str = Query("csv", description="导出格式选项，支持：csv, excel (或 xlsx), json"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """支持多格式选项的数据文件导出接口（支持 CSV 表格、原生 Excel 电子表格、JSON 文件）"""
    fmt = format.lower().strip()
    
    if fmt in ("excel", "xlsx"):
        excel_bytes = crud.export_components_to_excel(conn=conn)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=rebar_components.xlsx"}
        )
    elif fmt == "json":
        json_data = crud.export_components_to_json(conn=conn)
        return Response(
            content=json_data.encode("utf-8"),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=rebar_components.json"}
        )
    elif fmt == "csv":
        csv_text = crud.export_components_to_csv(conn=conn)
        csv_bytes = b"\xef\xbb\xbf" + csv_text.encode("utf-8")
        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=rebar_components.csv"}
        )
    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式 '{format}'，可选值: csv, excel, json")