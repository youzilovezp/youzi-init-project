#!/usr/bin/env python3
"""
一键添加业务模块。

用法（在生成的项目根目录执行）：
    python backend/scripts/add_module.py order
    python backend/scripts/add_module.py product --title "商品管理"

自动生成 model / schema / crud / router / view / api 六个文件，
并打印需要用户手动注册的提示。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def _snake(s: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()


def _pascal(s: str) -> str:
    return "".join(w.capitalize() for w in _snake(s).split("_"))


# 一级占位符用 __XXX__ 形式（避开 Vue 的 {{ }} 与 HTML < >）
# 后端模板：MODULE / CLS / TITLE / TABLE
# 后端特殊：{item_id} 用 {{item_id}} 占位（见 ROUTER_TEMPLATE）
# 前端二级：OPEN={ CLOSE=} ITEMS/RULES/ITEM_FIELDS/ROW_NAME/DATE_FMT/IDX
TEMPLATE_PLACEHOLDERS = {
    "OPEN": "{",
    "CLOSE": "}",
    "ITEMS": "{ id: 0, name: '' }",
    "RULES": "{ name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }",
    "ITEM_FIELDS": "{ name: form.name }",
    "ROW_NAME": "{row.name}",
    "DATE_FMT": "{{ new Date(scope.row.created_at).toLocaleString() }}",
    "IDX": "{id}",
}


def _render(template: str, **kwargs) -> str:
    """占位符用 __NAME__ 形式。"""
    for k, v in kwargs.items():
        template = template.replace(f"__{k}__", v)
    return template


def _render_view(template: str, **kwargs) -> str:
    """带二级替换（前端模板）。"""
    full = _render(template, **kwargs)
    # 二级替换：<<%XXX%>> → 对应 JS/TS 字符
    for k, v in TEMPLATE_PLACEHOLDERS.items():
        full = full.replace(f"<<%{k}%>>", v)
    return full


# ---------- 模板片段 ----------
MODEL_TEMPLATE = '''"""{title} ORM 模型。"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_class import Base, TimestampMixin


class __CLS__(Base, TimestampMixin):
    __tablename__ = "__TABLE__"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
'''

SCHEMA_TEMPLATE = '''"""{title} schema。"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class __CLS__Base(BaseModel):
    name: str


class __CLS__Create(__CLS__Base):
    pass


class __CLS__Update(BaseModel):
    name: str | None = None


class __CLS__Out(__CLS__Base):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
'''

CRUD_TEMPLATE = '''"""{title} CRUD。"""

from app.crud.base import CRUDBase
from app.models.__MODULE__ import __CLS__
from app.schemas.__MODULE__ import __CLS__Create, __CLS__Update


__MODULE___crud = CRUDBase[__CLS__, __CLS__Create, __CLS__Update](__CLS__)
'''

ROUTER_TEMPLATE = '''"""{title} 接口。"""

from fastapi import APIRouter

from app.api.deps import SessionDep, SuperUser
from app.core.exceptions import NotFoundError
from app.crud.__MODULE__ import __MODULE___crud
from app.schemas.common import ResponseModel
from app.schemas.__MODULE__ import __CLS__Create, __CLS__Out, __CLS__Update

router = APIRouter()


@router.get("", response_model=ResponseModel[list[__CLS__Out]], summary="{title}列表")
async def list_items(db: SessionDep, _user: SuperUser):
    items = await __MODULE___crud.list_all(db)
    return ResponseModel(data=[__CLS__Out.model_validate(i) for i in items])


@router.post("", response_model=ResponseModel[__CLS__Out], summary="创建{title}")
async def create_item(db: SessionDep, _user: SuperUser, payload: __CLS__Create):
    obj = await __MODULE___crud.create(db, payload)
    return ResponseModel(data=__CLS__Out.model_validate(obj))


@router.get("/__ITEM_ID__", response_model=ResponseModel[__CLS__Out], summary="{title}详情")
async def get_item(db: SessionDep, _user: SuperUser, item_id: int):
    obj = await __MODULE___crud.get(db, item_id)
    if obj is None:
        raise NotFoundError("{title}不存在")
    return ResponseModel(data=__CLS__Out.model_validate(obj))


@router.put("/__ITEM_ID__", response_model=ResponseModel[__CLS__Out], summary="更新{title}")
async def update_item(
    db: SessionDep, _user: SuperUser, item_id: int, payload: __CLS__Update
):
    obj = await __MODULE___crud.get(db, item_id)
    if obj is None:
        raise NotFoundError("{title}不存在")
    updated = await __MODULE___crud.update(db, obj, payload)
    return ResponseModel(data=__CLS__Out.model_validate(updated))


@router.delete("/__ITEM_ID__", response_model=ResponseModel, summary="删除{title}")
async def delete_item(db: SessionDep, _user: SuperUser, item_id: int):
    if not await __MODULE___crud.delete(db, item_id):
        raise NotFoundError("{title}不存在")
    return ResponseModel(message="已删除")
'''

VIEW_TEMPLATE = """<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import * as __MODULE__Api from '@/api/__MODULE__'
import type { __CLS__ } from '@/api/__MODULE__'

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
  await formRef.value.validate(async (valid) => <<%OPEN%>>
    if (!valid) return
    if (dialogMode.value === 'create') <<%OPEN%>>
      await __MODULE__Api.createItem(<<%ITEM_FIELDS%>>)
      ElMessage.success('创建成功')
    <<%CLOSE%>> else <<%OPEN%>>
      await __MODULE__Api.updateItem(form.id, <<%ITEM_FIELDS%>>)
      ElMessage.success('更新成功')
    <<%CLOSE%>>
    dialogVisible.value = false
    fetchData()
  <<%CLOSE%>>)
<<%CLOSE%>>

async function handleDelete(row: __CLS__) <<%OPEN%>>
  await ElMessageBox.confirm(`确定删除「$<<%ROW_NAME%>>`吗？`, '提示', <<%OPEN%>> type: 'warning' <<%CLOSE%>>)
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
        <el-button type="success" @click="openCreate">新增__TITLE__</</el-button>
      </div>

      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" />
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
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>
"""

API_TEMPLATE = """// {title} 接口
import request from './request'

export interface __CLS__ <<%OPEN%>>
  id: number
  name: string
  created_at: string
<<%CLOSE%>>

export interface __CLS__CreatePayload <<%OPEN%>>
  name: string
<<%CLOSE%>>

export interface __CLS__UpdatePayload <<%OPEN%>>
  name?: string
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


def add_module(
    module_name: str,
    title: str | None = None,
    backend_dir: Path = Path("backend"),
    frontend_dir: Path = Path("frontend"),
) -> int:
    if not re.match(r"^[a-z][a-z0-9_]*$", module_name):
        print(f"❌ 模块名格式错误：{module_name}（只允许小写字母、数字、下划线）")
        return 1

    title = title or _pascal(module_name)
    model_cls = _pascal(module_name)
    cls = model_cls
    table_name = (
        module_name + "s" if not module_name.endswith("s") else module_name + "es"
    )

    backend_app = backend_dir / "app"
    files = {
        backend_app / "models" / f"{module_name}.py": _render(
            MODEL_TEMPLATE, title=title, CLS=model_cls, TABLE=table_name
        ),
        backend_app / "schemas" / f"{module_name}.py": _render(
            SCHEMA_TEMPLATE, title=title, CLS=cls
        ),
        backend_app / "crud" / f"{module_name}.py": _render(
            CRUD_TEMPLATE, title=title, MODULE=module_name, CLS=model_cls
        ),
        backend_app / "api" / "v1" / "endpoints" / f"{module_name}.py": _render(
            ROUTER_TEMPLATE,
            title=title,
            MODULE=module_name,
            CLS=cls,
            ITEM_ID="{item_id}",
        ),
        frontend_dir / "src" / "api" / f"{module_name}.ts": _render(
            API_TEMPLATE, title=title, MODULE=module_name, CLS=cls
        ),
        frontend_dir / "src" / "views" / module_name / "index.vue": _render_view(
            VIEW_TEMPLATE, title=title, MODULE=module_name, CLS=cls, TITLE=title
        ),
    }

    print(f"🚀 添加模块：{module_name}（{title}）")
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"   ✅ {path}")

    print()
    print("📋 接下来你需要手动做（脚本不做，避免误改你的代码）：")
    print("   1. 编辑 backend/app/models/__init__.py，新增：")
    print(f"      from app.models.{module_name} import {model_cls}")
    print()
    print("   2. 编辑 backend/app/api/v1/router.py，新增：")
    print(
        f"      from app.api.v1.endpoints.{module_name} import router as {module_name}_router"
    )
    print(
        f"      api_router.include_router({module_name}_router, prefix='/{module_name}', tags=['{title}'])"
    )
    print()
    print("   3. 编辑 frontend/src/router/index.ts，添加路由：")
    print(
        f"      {{ path: '{module_name}', name: '{model_cls}', component: () => import('@/views/{module_name}/index.vue'), meta: {{ title: '{title}', icon: 'Document' }} }}"
    )
    print()
    print("   4. 编辑 frontend/src/layouts/BasicLayout.vue，添加菜单项。")
    print()
    print(
        f'   5. 生成数据库迁移：`make db-migrate msg="add {module_name}"` 然后 `make db-upgrade`'
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
        "--backend-dir", default="backend", help="后端目录（默认 backend）"
    )
    parser.add_argument(
        "--frontend-dir", default="frontend", help="前端目录（默认 frontend）"
    )
    args = parser.parse_args()
    return add_module(
        module_name=args.name,
        title=args.title,
        backend_dir=Path(args.backend_dir),
        frontend_dir=Path(args.frontend_dir),
    )


if __name__ == "__main__":
    sys.exit(main())
