#!/usr/bin/env python3
"""
一键添加业务模块。

用法（在生成的项目根目录执行）：
    python backend/scripts/add_module.py order
    python backend/scripts/add_module.py product --title "商品管理"
    python backend/scripts/add_module.py product --title "商品管理" \
        --fields "name:str,price:float:0,stock:int:0,status:str:active"

自动生成 model / schema / crud / router / view / api 六个文件，
并打印需要用户手动注册的提示。

字段类型（--fields 用）：
    str / text / int / float / bool / datetime
语法：name:type[:default]
  示例：--fields "name:str,price:float:0,status:str:active,desc:text"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ---------- 命名辅助 ----------
def _snake(s: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()


def _pascal(s: str) -> str:
    return "".join(w.capitalize() for w in _snake(s).split("_"))


# ---------- 字段类型定义 ----------
FIELD_TYPES: dict[str, dict[str, str]] = {
    "str": {"sql": "String(100)", "py": "str", "ts": "string"},
    "text": {"sql": "Text", "py": "str", "ts": "string"},
    "int": {"sql": "Integer", "py": "int", "ts": "number"},
    "float": {"sql": "Numeric(10, 2)", "py": "float", "ts": "number"},
    "bool": {"sql": "Boolean", "py": "bool", "ts": "boolean"},
    "datetime": {"sql": "DateTime", "py": "datetime", "ts": "string"},
}

# 中文标签猜词表（form / table 标签）
_LABEL_HINT = {
    "name": "名称",
    "title": "标题",
    "status": "状态",
    "price": "价格",
    "amount": "金额",
    "total": "总额",
    "quantity": "数量",
    "stock": "库存",
    "email": "邮箱",
    "phone": "电话",
    "mobile": "手机",
    "address": "地址",
    "desc": "描述",
    "description": "描述",
    "remark": "备注",
    "notes": "备注",
    "code": "编码",
    "type": "类型",
    "sort": "排序",
    "url": "链接",
    "avatar": "头像",
    "image": "图片",
    "icon": "图标",
}


def _label(name: str) -> str:
    return _LABEL_HINT.get(name, name)


def _parse_default(type_: str, raw: str | None):
    """根据类型解析默认值字符串。raw=None 表示必填。"""
    if raw is None:
        return None
    if type_ in ("str", "text"):
        return raw.strip("'\"")
    if type_ == "int":
        return int(raw)
    if type_ == "float":
        return float(raw)
    if type_ == "bool":
        return raw.lower() in ("true", "1", "yes", "on")
    return None


def _default_js_literal(d) -> str:
    """把 Python 默认值渲染成 JS 字面量。"""
    if d is None:
        return "null"
    if isinstance(d, bool):
        return "true" if d else "false"
    if isinstance(d, (int, float)):
        return str(d)
    if isinstance(d, str):
        # 用 json.dumps 生成安全的 JS 字符串字面量（自动转义 ' " \ 等）
        # ensure_ascii=False 保留中文字符
        return json.dumps(d, ensure_ascii=False)
    return "null"


def _py_default_literal(d) -> str:
    """Python 字面量（用于 Pydantic 字段默认值）。"""
    if d is None:
        return "None"
    if isinstance(d, bool):
        return "True" if d else "False"
    if isinstance(d, str):
        return repr(d)
    return str(d)


def _parse_fields(spec: str | None) -> list[dict]:
    """解析 --fields 字符串为字段列表。

    不传时：返回 [{name: 'name', type: 'str', default: None}]，与历史行为一致。

    字段名校验（防止生成代码注入）：
        1. 必须匹配 ^[a-z_][a-z0-9_]*$（合法 Python / TS 标识符）
        2. 不能与 TimestampMixin 自动生成的保留名冲突：id / created_at / updated_at
    """
    RESERVED_NAMES = {"id", "created_at", "updated_at"}
    VALID_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")

    if not spec:
        return [
            {
                "name": "name",
                "type": "str",
                "default": None,
                "raw_default": None,
                "required": True,
            }
        ]

    fields: list[dict] = []
    for raw_item in spec.split(","):
        item = raw_item.strip()
        if not item:
            continue
        parts = item.split(":")
        name = parts[0].strip()
        if not name:
            raise ValueError(f"字段名不能为空：{item!r}")
        if not VALID_NAME.match(name):
            raise ValueError(
                f"字段名 {name!r} 不合法（必须以小写字母或下划线开头，仅含小写字母、数字、下划线）"
            )
        if name in RESERVED_NAMES:
            raise ValueError(
                f"字段名 {name!r} 是保留名（id / created_at / updated_at 由 TimestampMixin 自动生成）"
            )
        if name in {
            "class",
            "type",
            "import",
            "return",
            "from",
            "def",
            "var",
            "function",
        }:
            raise ValueError(f"字段名 {name!r} 是 Python/JS 保留关键字，请换一个")
        type_ = parts[1].strip() if len(parts) > 1 else "str"
        raw_default = parts[2].strip() if len(parts) > 2 else None
        if type_ not in FIELD_TYPES:
            raise ValueError(
                f"未知字段类型: {type_!r}（支持: {', '.join(FIELD_TYPES)}）"
            )
        try:
            default = _parse_default(type_, raw_default)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"字段 {name!r} 的默认值 {raw_default!r} 无法解析为 {type_}: {e}"
            ) from e
        # NaN / inf 拦截
        if isinstance(default, float) and (
            default != default or default == float("inf") or default == float("-inf")
        ):
            raise ValueError(
                f"字段 {name!r} 的默认值 {raw_default!r} 是 NaN / inf，拒绝生成"
            )
        fields.append(
            {
                "name": name,
                "type": type_,
                "default": default,
                "raw_default": raw_default,
                "required": raw_default is None,
            }
        )
    if not fields:
        raise ValueError("--fields 至少需要一个字段")
    return fields


# ---------- 字段渲染 ----------
def _model_field_lines(fields: list[dict]) -> str:
    """生成 SQLAlchemy mapped_column 行（除 id 之外的全部字段）。"""
    lines = []
    for f in fields:
        info = FIELD_TYPES[f["type"]]
        sql_type = info["sql"]
        if f["required"]:
            kwarg = "nullable=False"
        else:
            kwarg = f"default={_py_default_literal(f['default'])}"
        lines.append(
            f"    {f['name']}: Mapped[{info['py']}] = mapped_column({sql_type}, {kwarg})"
        )
    return "\n".join(lines)


def _model_imports(fields: list[dict]) -> str:
    """根据字段类型导出 SQLAlchemy 需要 import 的类型。"""
    bases = {"Integer"}  # id 永远要 Integer
    for f in fields:
        bases.add(FIELD_TYPES[f["type"]]["sql"].split("(")[0])
    return ", ".join(sorted(bases))


def _schema_field_lines(fields: list[dict]) -> str:
    """生成 Pydantic Base 字段行（Base / Create 共用）。"""
    lines = []
    for f in fields:
        py_type = FIELD_TYPES[f["type"]]["py"]
        if f["required"]:
            lines.append(f"    {f['name']}: {py_type}")
        else:
            lines.append(
                f"    {f['name']}: {py_type} = {_py_default_literal(f['default'])}"
            )
    return "\n".join(lines)


def _schema_update_lines(fields: list[dict]) -> str:
    """Update schema：所有字段 Optional。"""
    lines = []
    for f in fields:
        py_type = FIELD_TYPES[f["type"]]["py"]
        lines.append(f"    {f['name']}: {py_type} | None = None")
    return "\n".join(lines)


def _ts_interface_lines(fields: list[dict], optional: bool = False) -> str:
    """TS interface 字段。"""
    lines = []
    for f in fields:
        ts_type = FIELD_TYPES[f["type"]]["ts"]
        if optional or not f["required"]:
            lines.append(f"  {f['name']}?: {ts_type}")
        else:
            lines.append(f"  {f['name']}: {ts_type}")
    return "\n".join(lines)


def _form_default_obj(fields: list[dict]) -> str:
    """生成 dialog form 的初始值 JS 对象字面量。"""
    items = ["id: 0"]
    for f in fields:
        if f["required"]:
            # 必填字段：根据类型给一个不会触发表单校验失败的占位默认值
            if f["type"] in ("int", "float"):
                default = 0
            elif f["type"] == "bool":
                default = "false"
            elif f["type"] == "datetime":
                default = "null"  # ← 之前是 ''，datetime 不能用空串
            else:
                default = "''"  # str / text 用空串（用户必须填）
        else:
            default = _default_js_literal(f["default"])
        items.append(f"{f['name']}: {default}")
    return "{ " + ", ".join(items) + " }"


def _form_validation_rules(fields: list[dict]) -> str:
    """生成 Element Plus 的 FormRules（只校验 str 必填字段）。

    Element Plus 的 FormRule 必须用 field 名作为 key（对应 el-form-item 的 prop），
    不能有 name 字段。type-check 期望 Partial<Record<string, FormItemRule>>。
    """
    rules = []
    for f in fields:
        if f["required"] and f["type"] == "str":
            rules.append(
                f"    {f['name']}: [{{ required: true, message: '请输入{_label(f['name'])}', trigger: 'blur' }}]"
            )
    if not rules:
        return "{}"
    return "{\n" + ",\n".join(rules) + "\n  }"


def _table_columns(fields: list[dict]) -> str:
    """生成 el-table-column 行。text 字段不进表格（太宽）。"""
    lines = []
    for f in fields:
        if f["type"] == "text":
            continue
        width = "120" if f["type"] == "float" else ""
        if width:
            lines.append(
                f'        <el-table-column prop="{f["name"]}" label="{_label(f["name"])}" width="{width}" />'
            )
        else:
            lines.append(
                f'        <el-table-column prop="{f["name"]}" label="{_label(f["name"])}" />'
            )
    return "\n".join(lines)


def _form_items(fields: list[dict]) -> str:
    """生成 dialog 内的 el-form-item。"""
    widget_map = {
        "str": "el-input",
        "text": "el-input",
        "int": "el-input-number",
        "float": "el-input-number",
        "bool": "el-switch",
        "datetime": "el-date-picker",
    }
    lines = []
    for f in fields:
        widget = widget_map[f["type"]]
        if f["type"] == "text":
            lines.append(
                f'        <el-form-item label="{_label(f["name"])}" prop="{f["name"]}">'
            )
            lines.append(
                f'          <el-input v-model="form.{f["name"]}" type="textarea" :rows="3" />'
            )
            lines.append("        </el-form-item>")
        elif widget == "el-switch":
            lines.append(
                f'        <el-form-item label="{_label(f["name"])}" prop="{f["name"]}">'
            )
            lines.append(f'          <el-switch v-model="form.{f["name"]}" />')
            lines.append("        </el-form-item>")
        else:
            lines.append(
                f'        <el-form-item label="{_label(f["name"])}" prop="{f["name"]}">'
            )
            lines.append(f'          <{widget} v-model="form.{f["name"]}" />')
            lines.append("        </el-form-item>")
    return "\n".join(lines)


# ---------- 占位符替换 ----------
# 一级占位符：__XXX__
# 前端二级：<<%XXX%>>（避开 Vue 的 {{ }} 与 HTML < >）
TEMPLATE_PLACEHOLDERS = {
    "OPEN": "{",
    "CLOSE": "}",
    "ITEMS": "{ id: 0, name: '' }",
    "RULES": "[{ name: 'name', required: true, message: '请输入名称', trigger: 'blur' }]",
    "ITEM_FIELDS": "form",
    "ROW_NAME": "row.name",
    "DATE_FMT": "{{ new Date(scope.row.created_at).toLocaleString() }}",
    "IDX": "{id}",
}


def _render(template: str, **kwargs) -> str:
    """一级占位符 __XXX__ → kwargs 值。"""
    for k, v in kwargs.items():
        template = template.replace(f"__{k}__", str(v))
    return template


def _render_view(
    template: str, placeholders: dict[str, str] | None = None, **kwargs
) -> str:
    """带二级替换（前端模板）。

    placeholders 接受调用方传入的 local dict（避免改全局 TEMPLATE_PLACEHOLDERS），
    默认为模块级默认 dict（保持向后兼容）。
    """
    full = _render(template, **kwargs)
    src = placeholders if placeholders is not None else TEMPLATE_PLACEHOLDERS
    for k, v in src.items():
        full = full.replace(f"<<%{k}%>>", v)
    return full


# ---------- 模板片段 ----------
MODEL_TEMPLATE = '''"""__TITLE__ ORM 模型。"""

from sqlalchemy import __MODEL_IMPORTS__
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_class import Base, TimestampMixin


class __CLS__(Base, TimestampMixin):
    __tablename__ = "__TABLE__"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
__MODEL_FIELDS__
'''

SCHEMA_TEMPLATE = '''"""__TITLE__ schema。"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class __CLS__Base(BaseModel):
__SCHEMA_FIELDS__


class __CLS__Create(__CLS__Base):
    pass


class __CLS__Update(BaseModel):
__SCHEMA_UPDATE_FIELDS__


class __CLS__Out(__CLS__Base):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
'''

CRUD_TEMPLATE = '''"""__TITLE__ CRUD。"""

from app.crud.base import CRUDBase
from app.models.__MODULE__ import __CLS__
from app.schemas.__MODULE__ import __CLS__Create, __CLS__Update


__MODULE___crud = CRUDBase[__CLS__, __CLS__Create, __CLS__Update](__CLS__)
'''

ROUTER_TEMPLATE = '''"""__TITLE__ 接口。"""

from fastapi import APIRouter

from app.api.deps import SessionDep, SuperUser
from app.core.exceptions import NotFoundError
from app.crud.__MODULE__ import __MODULE___crud
from app.schemas.common import ResponseModel
from app.schemas.__MODULE__ import __CLS__Create, __CLS__Out, __CLS__Update

router = APIRouter()


@router.get("", response_model=ResponseModel[list[__CLS__Out]], summary="__TITLE__列表")
async def list_items(db: SessionDep, _user: SuperUser):
    items = await __MODULE___crud.list_all(db)
    return ResponseModel(data=[__CLS__Out.model_validate(i) for i in items])


@router.post("", response_model=ResponseModel[__CLS__Out], summary="创建__TITLE__")
async def create_item(db: SessionDep, _user: SuperUser, payload: __CLS__Create):
    obj = await __MODULE___crud.create(db, payload)
    return ResponseModel(data=__CLS__Out.model_validate(obj))


@router.get("/__ITEM_ID__", response_model=ResponseModel[__CLS__Out], summary="__TITLE__详情")
async def get_item(db: SessionDep, _user: SuperUser, item_id: int):
    obj = await __MODULE___crud.get(db, item_id)
    if obj is None:
        raise NotFoundError("__TITLE__不存在")
    return ResponseModel(data=__CLS__Out.model_validate(obj))


@router.put("/__ITEM_ID__", response_model=ResponseModel[__CLS__Out], summary="更新__TITLE__")
async def update_item(
    db: SessionDep, _user: SuperUser, item_id: int, payload: __CLS__Update
):
    obj = await __MODULE___crud.get(db, item_id)
    if obj is None:
        raise NotFoundError("__TITLE__不存在")
    updated = await __MODULE___crud.update(db, obj, payload)
    return ResponseModel(data=__CLS__Out.model_validate(updated))


@router.delete("/__ITEM_ID__", response_model=ResponseModel, summary="删除__TITLE__")
async def delete_item(db: SessionDep, _user: SuperUser, item_id: int):
    if not await __MODULE___crud.delete(db, item_id):
        raise NotFoundError("__TITLE__不存在")
    return ResponseModel(message="已删除")
'''

VIEW_TEMPLATE = """<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import * as __MODULE__Api from '@/api/__MODULE__'
import type { __CLS__, __CLS__CreatePayload, __CLS__UpdatePayload } from '@/api/__MODULE__'

const loading = ref(false)
const tableData = ref<__CLS__[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const formRef = ref<FormInstance>()
const form = reactive(<<%ITEMS%>>)

const rules: FormRules = <<%RULES%>>

async function fetchData() <<%OPEN%>>
  loading.value = true
  try <<%OPEN%>>
    tableData.value = await __MODULE__Api.listItems()
  <<%CLOSE%>> finally <<%OPEN%>>
    loading.value = false
  <<%CLOSE%>>
}

function openCreate() <<%OPEN%>>
  dialogMode.value = 'create'
  Object.assign(form, <<%ITEMS%>>)
  dialogVisible.value = true
<<%CLOSE%>>

function openEdit(row: __CLS__) <<%OPEN%>>
  dialogMode.value = 'edit'
  Object.assign(form, row)
  dialogVisible.value = true
<<%CLOSE%>>

async function handleSubmit() <<%OPEN%>>
  if (!formRef.value) return
  // Element Plus validate() 返回 Promise<boolean>——用 await + 非 async 回调
  // 之前 await formRef.value.validate(async (valid) => {...}) 是错的：
  // validate 回调签名是 sync (valid: boolean) => void，async 函数返回 void 不会
  // 变成 awaitable，会让 fetchData 在 valid=false 时也执行，删除/更新仍发出请求
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  const payload: __CLS__CreatePayload = <<%ITEM_FIELDS%>>
  if (dialogMode.value === 'create') <<%OPEN%>>
    await __MODULE__Api.createItem(payload)
    ElMessage.success('创建成功')
  <<%CLOSE%>> else <<%OPEN%>>
    await __MODULE__Api.updateItem(form.id, payload)
    ElMessage.success('更新成功')
  <<%CLOSE%>>
  dialogVisible.value = false
  fetchData()
<<%CLOSE%>>

async function handleDelete(row: __CLS__) <<%OPEN%>>
  await ElMessageBox.confirm(`确定删除「$<<%ROW_NAME%>>」吗？`, '提示', <<%OPEN%>> type: 'warning' <<%CLOSE%>>)
  await __MODULE__Api.deleteItem(row.id)
  ElMessage.success('已删除')
  fetchData()
<<%CLOSE%>>

onMounted(fetchData)
</script>

<template>
  <div class="page">
    <el-card>
      <div style="margin-bottom: 16px">
        <el-button type="success" @click="openCreate">新增__TITLE__</el-button>
      </div>

      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="ID" width="80" />
__TABLE_COLUMNS__
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            <<%DATE_FMT%>>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="openEdit(scope.row as __CLS__)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(scope.row as __CLS__)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增__TITLE__' : '编辑__TITLE__'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
__FORM_ITEMS__
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>
"""

API_TEMPLATE = """// __TITLE__ 接口
import request from './request'

export interface __CLS__ <<%OPEN%>>
  id: number
__TS_INTERFACE_FIELDS__
  created_at: string
<<%CLOSE%>>

export interface __CLS__CreatePayload <<%OPEN%>>
__TS_PAYLOAD_FIELDS__
<<%CLOSE%>>

export interface __CLS__UpdatePayload <<%OPEN%>>
__TS_UPDATE_FIELDS__
<<%CLOSE%>>

/** 列表 */
export function listItems() <<%OPEN%>>
  return request.get<__CLS__[], __CLS__[]>('/__MODULE__')
<<%CLOSE%>>

/** 创建 */
export function createItem(payload: __CLS__CreatePayload) <<%OPEN%>>
  return request.post<__CLS__, __CLS__>('/__MODULE__', payload)
<<%CLOSE%>>

/** 详情 */
export function getItem(id: number) <<%OPEN%>>
  return request.get<__CLS__, __CLS__>(`/__MODULE__/$<<%IDX%>>`)
<<%CLOSE%>>

/** 更新 */
export function updateItem(id: number, payload: __CLS__UpdatePayload) <<%OPEN%>>
  return request.put<__CLS__, __CLS__>(`/__MODULE__/$<<%IDX%>>`, payload)
<<%CLOSE%>>

/** 删除 */
export function deleteItem(id: number) <<%OPEN%>>
  return request.delete<unknown, unknown>(`/__MODULE__/$<<%IDX%>>`)
<<%CLOSE%>>
"""


# ---------- 主体 ----------
def add_module(
    module_name: str,
    title: str | None = None,
    fields_spec: str | None = None,
    backend_dir: Path | None = None,
    frontend_dir: Path | None = None,
) -> int:
    if not re.match(r"^[a-z][a-z0-9_]*$", module_name):
        print(f"❌ 模块名格式错误：{module_name}（只允许小写字母、数字、下划线）")
        return 1

    # 目录自动探测：admin 模式 app 在 backend/，server 模式 app 在根目录
    if backend_dir is None:
        backend_dir = Path(".") if Path("app/models").exists() else Path("backend")
    if frontend_dir is None:
        frontend_dir = Path("frontend")

    try:
        fields = _parse_fields(fields_spec)
    except ValueError as e:
        print(f"❌ --fields 解析失败：{e}")
        return 1

    title = title or _pascal(module_name)
    model_cls = _pascal(module_name)
    cls = model_cls
    table_name = (
        module_name + "s" if not module_name.endswith("s") else module_name + "es"
    )

    # 一次性算好所有动态内容
    model_imports = _model_imports(fields)
    model_fields_str = _model_field_lines(fields)
    schema_fields_str = _schema_field_lines(fields)
    schema_update_str = _schema_update_lines(fields)
    ts_iface_str = _ts_interface_lines(fields, optional=False)
    ts_payload_str = _ts_interface_lines(fields, optional=False)
    ts_update_str = _ts_interface_lines(fields, optional=True)
    table_columns_str = _table_columns(fields)
    form_items_str = _form_items(fields)

    # 改为函数内 local dict，避免模块全局状态在并发 / 多调用间泄漏
    placeholders = dict(TEMPLATE_PLACEHOLDERS)
    placeholders["ITEMS"] = _form_default_obj(fields)
    placeholders["RULES"] = _form_validation_rules(fields)
    placeholders["ITEM_FIELDS"] = (
        "{ " + ", ".join(f"{f['name']}: form.{f['name']}" for f in fields) + " }"
    )
    placeholders["ROW_NAME"] = "row.name"

    backend_app = backend_dir / "app"
    files = {
        backend_app / "models" / f"{module_name}.py": _render(
            MODEL_TEMPLATE,
            TITLE=title,
            MODEL_IMPORTS=model_imports,
            CLS=model_cls,
            TABLE=table_name,
            MODEL_FIELDS=model_fields_str,
        ),
        backend_app / "schemas" / f"{module_name}.py": _render(
            SCHEMA_TEMPLATE,
            TITLE=title,
            CLS=cls,
            SCHEMA_FIELDS=schema_fields_str,
            SCHEMA_UPDATE_FIELDS=schema_update_str,
        ),
        backend_app / "crud" / f"{module_name}.py": _render(
            CRUD_TEMPLATE, TITLE=title, MODULE=module_name, CLS=model_cls
        ),
        backend_app / "api" / "v1" / "endpoints" / f"{module_name}.py": _render(
            ROUTER_TEMPLATE,
            TITLE=title,
            MODULE=module_name,
            CLS=cls,
            ITEM_ID="{item_id}",
        ),
    }

    # server 模式（纯后端项目）没有前端，跳过前端文件生成
    has_frontend = (frontend_dir / "package.json").exists() or (
        frontend_dir / "src"
    ).exists()
    if has_frontend:
        files[frontend_dir / "src" / "api" / f"{module_name}.ts"] = _render_view(
            API_TEMPLATE,
            placeholders=placeholders,
            TITLE=title,
            MODULE=module_name,
            CLS=cls,
            TS_INTERFACE_FIELDS=ts_iface_str,
            TS_PAYLOAD_FIELDS=ts_payload_str,
            TS_UPDATE_FIELDS=ts_update_str,
        )
        files[frontend_dir / "src" / "views" / module_name / "index.vue"] = (
            _render_view(
                VIEW_TEMPLATE,
                placeholders=placeholders,
                TITLE=title,
                MODULE=module_name,
                CLS=cls,
                TABLE_COLUMNS=table_columns_str,
                FORM_ITEMS=form_items_str,
            )
        )
    else:
        print(f"ℹ️  未检测到前端工程（{frontend_dir}），只生成后端 4 个文件")

    print(f"🚀 添加模块：{module_name}（{title}）")
    if fields_spec:
        field_summary = ", ".join(f"{f['name']}:{f['type']}" for f in fields)
        print(f"   📦 字段（{len(fields)} 个）：{field_summary}")

    # 关键修复：之前会静默覆盖用户已编辑过的文件。
    # 现在检测到已存在的文件就拒绝继续（除非 --force）。
    existing = [p for p in files if p.exists()]
    if existing:
        force = getattr(add_module, "_force", False)
        if not force:
            print()
            print(f"❌ 目标文件已存在（{len(existing)} 个），拒绝覆盖：")
            for p in existing:
                print(f"   - {p}")
            print()
            print("   解决方案：")
            print("   1. 这些模块文件已经生成过 / 被你手动改过")
            print("   2. 如确认要覆盖，加 --force 重跑")
            print("   3. 或先备份 / 删除旧文件再重跑")
            return 2
        print(f"   ⚠️  --force 已指定，覆盖 {len(existing)} 个已存在文件")

    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"   ✅ {path}")

    print()
    print("📋 接下来你需要手动做（脚本不做，避免误改你的代码）：")
    print(f"   1. 编辑 {backend_dir}/app/models/__init__.py，新增：")
    print(f"      from app.models.{module_name} import {model_cls}")
    print()
    print(f"   2. 编辑 {backend_dir}/app/api/v1/router.py，新增：")
    print(
        f"      from app.api.v1.endpoints.{module_name} import router as {module_name}_router"
    )
    print(
        f"      api_router.include_router({module_name}_router, prefix='/{module_name}', tags=['{title}'])"
    )
    if has_frontend:
        print()
        print("   3. 编辑 frontend/src/router/index.ts，添加路由：")
        print(
            f"      {{ path: '{module_name}', name: '{model_cls}', component: () => import('@/views/{module_name}/index.vue'), meta: {{ title: '{title}', icon: 'Document' }} }}"
        )
        print()
        print("   4. 编辑 frontend/src/layouts/BasicLayout.vue，添加菜单项。")
        print()
        print(
            f'   5. 生成数据库迁移：`make db-migrate MSG="add {module_name}"` 然后 `make db-upgrade`'
        )
    else:
        print()
        print(
            f'   3. 生成数据库迁移：`make db-migrate MSG="add {module_name}"` 然后 `make db-upgrade`'
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="一键添加业务模块（生成 model/schema/crud/router/view/api）"
    )
    parser.add_argument(
        "name", help="模块名（snake_case），如 order / product / article"
    )
    parser.add_argument(
        "--title", default=None, help="中文标题（默认自动从 name 推导）"
    )
    parser.add_argument(
        "--fields",
        default=None,
        help=(
            "自定义字段，逗号分隔，格式 name:type[:default]。"
            "类型: str/text/int/float/bool/datetime。"
            '示例: --fields "name:str,price:float:0,stock:int:0,status:str:active,desc:text"'
        ),
    )
    parser.add_argument(
        "--backend-dir",
        default=None,
        help="后端目录（默认自动探测：根目录有 app/ 用 .，否则 backend）",
    )
    parser.add_argument(
        "--frontend-dir",
        default=None,
        help="前端目录（默认 frontend；没有前端工程时自动跳过前端文件）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖已存在的目标文件（默认拒绝覆盖，避免误删用户已修改的代码）",
    )
    args = parser.parse_args()
    # 用模块全局变量传递 force（避免改动函数签名与现有调用方）
    add_module._force = args.force  # type: ignore[attr-defined]
    return add_module(
        module_name=args.name,
        title=args.title,
        fields_spec=args.fields,
        backend_dir=Path(args.backend_dir) if args.backend_dir else None,
        frontend_dir=Path(args.frontend_dir) if args.frontend_dir else None,
    )


if __name__ == "__main__":
    sys.exit(main())
