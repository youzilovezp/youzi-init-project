"""脚手架自身回归测试 — 把历轮审计修复的 bug 固化为永久断言。

跑法：仓库根目录 `python3 -m pytest tests/ -q`（零网络、零 Docker、秒级）。
任何改动破坏这些断言 = 引入了已知类型的回归，当场拦截。
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
TEMPLATES = ROOT / "templates"
ADD_MODULE = SCRIPTS / "add_module.py"
ADD_MODULE_TMPL = TEMPLATES / "backend" / "scripts" / "add_module.py"


# ============================================================
# 一、双副本 / 结构一致性（防"只改一份"类回归）
# ============================================================
def test_add_module_dual_copy_identical():
    """scripts/add_module.py 与模板副本必须逐字节一致（第十轮 🔴 回归）。"""
    assert (
        ADD_MODULE.read_bytes() == ADD_MODULE_TMPL.read_bytes()
    ), "两份 add_module.py 漂移了！修复必须同时改两处（或从根目录拷贝过去）"


def test_makefile_restore_unique_per_mode():
    """Makefile 每个模式段只能有一个 restore:（第八轮 🟠 重复定义回归）。"""
    t = (TEMPLATES / "root" / "Makefile.tmpl").read_text()
    sections = t.split("{% else %}")
    assert len(sections) == 2, "应有 admin/server 两段"
    for name, sec in zip(["admin", "server"], sections):
        assert (
            len(re.findall(r"^restore:", sec, re.M)) == 1
        ), f"{name} 段 restore 不唯一"
        assert len(re.findall(r"^start:", sec, re.M)) == 1, f"{name} 段 start 不唯一"
        assert len(re.findall(r"^dev:", sec, re.M)) == 1, f"{name} 段 dev 不唯一"


def test_makefile_no_hardcoded_ports_in_recipes():
    """recipe 里的端口必须动态读 .env（第八轮多项目并存修复）。"""
    t = (TEMPLATES / "root" / "Makefile.tmpl").read_text()
    # 模板变量 {{ port }} 是合法的（渲染默认值）；硬编码数字端口在 --port 后不允许
    for m in re.finditer(r"--port[= ]([^\s&\\]+)", t):
        port = m.group(1)
        assert "$(" in port or "{{" in port, f"硬编码端口: {port}"


# ============================================================
# 二、add_module 生成器（第 5/6/8/9 轮修复的回归网）
# ============================================================
sys.path.insert(0, str(SCRIPTS))
from add_module import (  # noqa: E402
    _parse_fields,
    _model_datetime_import,
    _default_js_literal,
)


def test_fields_colon_in_default():
    """默认值含冒号不截断（第九轮 🔴：url:str:http://x → 'http'）。"""
    f = _parse_fields("url:str:http://x.com")
    assert f[0]["default"] == "http://x.com"


def test_fields_datetime_seconds_preserved():
    """datetime 默认值时分秒不丢（第九轮 🔴）。"""
    f = _parse_fields("evt:datetime:2026-01-01T12:34:56")
    assert "12:34:56" in str(f[0]["default"]) or "12, 34, 56" in str(f[0]["default"])


def test_fields_bool_invalid_rejected():
    """非法 bool 默认值报错不静默 False（第九轮 🟡）。"""
    with pytest.raises(ValueError, match="true/false"):
        _parse_fields("x:bool:flase")


def test_fields_python_keyword_rejected():
    """Python 关键字模块名/字段名拦截（第六轮 🔴 注入）。"""
    from add_module import add_module as _am

    _am._force = False
    assert _am("lambda", backend_dir=None, frontend_dir=None) == 1


def test_fields_title_injection_rejected():
    """title 引号注入拦截（第六轮 🔴）。"""
    from add_module import add_module as _am

    _am._force = False
    assert _am("okmod", title='a"""b', backend_dir=None, frontend_dir=None) == 1


def test_model_datetime_import_present():
    """datetime 字段生成的 model 必须带 from datetime import datetime（第六轮 🔴 NameError）。"""
    fields = _parse_fields("a:datetime:2026-01-01T00:00:00")
    assert "from datetime import datetime" in _model_datetime_import(fields)
    assert _model_datetime_import(_parse_fields("a:str")) == ""


def test_table_name_plural_rules(tmp_path):
    """表名复数（行为级）：box→boxes、bus→buses、leaf→leafs（+s）、order→orders。"""
    from add_module import add_module as _am

    _am._force = False
    _am("box", backend_dir=tmp_path, frontend_dir=tmp_path / "fe")
    _am("bus", backend_dir=tmp_path, frontend_dir=tmp_path / "fe")
    _am("leaf", backend_dir=tmp_path, frontend_dir=tmp_path / "fe")
    _am("order", backend_dir=tmp_path, frontend_dir=tmp_path / "fe")
    tables = sorted(
        m.group(1)
        for m in re.finditer(
            r'__tablename__ = "(\w+)"',
            (tmp_path / "app" / "models").rglob("*.py").__class__
            and "".join(
                f.read_text() for f in (tmp_path / "app" / "models").glob("*.py")
            ),
        )
    )
    assert tables == ["boxes", "buses", "leafs", "orders"], tables


def test_js_literal_datetime_string():
    """datetime 默认值 → JS 字符串（第九轮 TS null 类型错误）。"""
    from datetime import datetime as dt

    assert _default_js_literal(dt(2026, 1, 1)) == '"2026-01-01T00:00:00"'


def test_generated_model_ast_valid(tmp_path):
    """全类型字段生成的 model 通过 ast 语法校验（含 datetime import）。"""
    from add_module import add_module as _am

    _am._force = False
    rc = _am(
        "widget",
        title="挂件",
        fields_spec="a:str,b:text,c:int,d:float,e:bool,f:datetime:2026-01-01T00:00:00",
        backend_dir=tmp_path,
        frontend_dir=tmp_path / "fe",
    )
    assert rc == 0
    model = tmp_path / "app" / "models" / "widget.py"
    ast.parse(model.read_text())  # 语法崩溃会抛


def test_generated_view_no_literal_row_name(tmp_path):
    """生成视图的删除确认不得出现字面 $row.name（第十轮 🔴 模板错）。"""
    from add_module import add_module as _am

    (tmp_path / "fe").mkdir()
    (tmp_path / "fe" / "package.json").write_text("{}")
    (tmp_path / "fe" / "src").mkdir()
    _am._force = False
    _am("thing", title="物", backend_dir=tmp_path, frontend_dir=tmp_path / "fe")
    view = (tmp_path / "fe" / "src" / "views" / "thing" / "index.vue").read_text()
    assert "$row.name" not in view, "删除确认文案出现字面 $row.name"
    assert "catch(() => false)" in view, "确认框缺 .catch（unhandled rejection 回归）"
    assert "el-pagination" in view, "生成页缺分页（第五轮 🔴）"
    assert "formatTime" in view, "生成页缺 formatTime（第十一轮 🔴 时区）"


# ============================================================
# 三、init.py 生成完整性（第 4/6/8 轮修复的回归网）
# ============================================================
def _gen(name: str, args: list[str]) -> Path:
    tmp = tempfile.mkdtemp(prefix=f"yz-{name}-")
    proj = Path(tmp) / name
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "init.py"), name, *args],
        cwd=tmp,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, r.stderr[-500:]
    return proj


def test_admin_generation_complete():
    """admin 模式：占位符全替换、基线迁移在、AGENTS.md 在、gitignore 齐。"""
    p = _gen("chkadmin", ["--only", "admin"])
    env = p / "backend" / ".env"
    content = env.read_text()
    for ph in ("CHANGE_ME", "__SECRET_KEY__"):
        assert ph not in content, f".env 残留占位符 {ph}"
    assert (
        p / "backend" / "alembic" / "versions" / "0001_baseline.py"
    ).exists(), "缺基线迁移"
    assert (p / "AGENTS.md").exists(), "缺 AGENTS.md"
    gi = (p / ".gitignore").read_text()
    for must in ("node_modules", "backups/", ".env"):
        assert must in gi, f".gitignore 缺 {must}"
    # 渲染残留：真正的 jinja 指令行（{% if %} / {% endif %} / 行首 {{ var }} 模板变量）
    for f in p.rglob("*"):
        if f.suffix in (".py", ".ts", ".vue", ".yml", ".ini") and f.is_file():
            for line in f.read_text().split("\n"):
                s = line.strip()
                if s.startswith("{%") or (
                    s.startswith("{{")
                    and s.endswith("}}")
                    and " " in s
                    and "'" not in s
                ):
                    pytest.fail(f"jinja 残留: {f.name}: {line[:60]}")


def test_ui_mode_gitignore_has_node_modules():
    """ui 模式 .gitignore 必须含 node_modules（第六轮 🔴）。"""
    p = _gen("chkui", ["--only", "ui"])
    assert "node_modules" in (p / ".gitignore").read_text()
    assert not (p / "backend").exists(), "ui 模式不应有 backend/"


def test_with_redis_sets_host():
    """--with-redis 必须写 REDIS_HOST=localhost（第八轮 🟠 flag 失效）。"""
    p = _gen("chkredis", ["--only", "server", "--with-redis"])
    m = re.search(r"^REDIS_HOST=(\S*)$", (p / ".env").read_text(), re.M)
    assert m and m.group(1) == "localhost", "REDIS_HOST 未启用"


def test_admin_pass_not_baked_into_source():
    """自定义密码不得进任何源码/文档（第七轮 🔴 git 泄露）。"""
    p = _gen("chksecret", ["--only", "admin", "--admin-pass", "Xray#Secret999"])
    for f in p.rglob("*"):
        if f.is_file() and f.suffix in (".py", ".ts", ".vue", ".md", ".tmpl"):
            if f.name == ".env":
                continue
            assert "Xray#Secret999" not in f.read_text(), f"密码泄漏到 {f}"


def test_no_youzi_placeholder_left():
    """Youzi Admin 占位符替换完整（含 setup.ts——第九轮 🟡）。"""
    p = _gen("chktitle", ["--only", "admin"])
    for f in (p / "frontend").rglob("*"):
        if f.is_file() and f.suffix in (".ts", ".vue", ".html", ".md", ".json"):
            assert "Youzi Admin" not in f.read_text(), f"占位符残留: {f}"


# ============================================================
# 四、关键模板内容断言（历轮修复的模板级回归）
# ============================================================
def test_init_db_stamp_head_not_baseline():
    """stamp 必须 head 不能写死 baseline（第十一轮 🟠 克隆卡死）。"""
    t = (TEMPLATES / "backend" / "app" / "db" / "init_db.py.tmpl").read_text()
    assert 'stamp", "head"' in t
    assert 'stamp", "0001_baseline"' not in t


def test_init_db_admin_independent_of_seed():
    """admin 创建必须独立于 AUTO_SEED_DATA（第九轮 🟠 生产无管理员）。"""
    t = (TEMPLATES / "backend" / "app" / "db" / "init_db.py.tmpl").read_text()
    assert "admin + 角色必须始终创建" in t


def test_adminer_no_depends_on_postgres():
    """adminer 不得 depends_on postgres（第七轮 🔴 端口冲突）。"""
    t = (TEMPLATES / "root" / "docker-compose.yml.tmpl").read_text()
    sec = t[t.find("adminer:") : t.find("volumes:")]
    assert "depends_on" not in sec


def test_dockerfile_copies_alembic_ini():
    """Dockerfile 必须拷 alembic.ini（第六轮 🟠 容器内迁移失效）。"""
    t = (TEMPLATES / "backend" / "docker" / "Dockerfile").read_text()
    assert "alembic.ini" in t


def test_backup_sqlite_uses_api_not_cp():
    """SQLite backup 必须用 sqlite3 backup API（第十一轮 🟠 撕页）——正反双向断言。"""
    t = (TEMPLATES / "root" / "Makefile.tmpl").read_text()
    # 反向：不允许裸 cp 拷 app.db 到 backups（跨行也算）
    assert not re.search(r"cp\s+(?:backend/)?data/app\.db\s", t), "存在裸 cp 拷库文件"
    # 正向：backup API 必须存在（两模式段各一）
    assert t.count("sqlite3.connect('backend/data/app.db').backup") == 1
    assert t.count("sqlite3.connect('data/app.db').backup") == 1


def test_makefile_middleware_reuse_logic():
    """中间件复用（核心需求）——作用域级断言：探测→复用分支→Docker 兜底→daemon 检查的顺序结构。"""
    t = (TEMPLATES / "root" / "Makefile.tmpl").read_text()
    for must in (
        "port_listening",
        "复用本机已运行的 PostgreSQL",
        "docker info",
        "优先复用本机已运行的 PG/Redis",
    ):
        assert must in t, f"中间件复用逻辑缺: {must}"
    # 顺序结构：每个 start: recipe 内，port_listening 调用必须出现在 docker compose up 之前（先探测复用、缺才 Docker）
    for m in re.finditer(r"^start:.*?$(.*?)(?=^\w|\Z)", t, re.M | re.S):
        body = m.group(1)
        i_probe = body.find("port_listening")
        i_docker = body.find("docker compose")
        assert (
            0 < i_probe < i_docker
        ), "start recipe 中端口探测必须在 docker compose 之前（复用优先）"


def test_docs_no_stale_manuals():
    """文档不得残留旧时代说法（第十一轮 6🔴：手动基线/随机密码/小写 msg）。"""
    docs = [ROOT / "使用手册.md", ROOT / "README.md", ROOT / "安装说明.md"]
    docs += list((TEMPLATES / "backend" / "docs").glob("*.tmpl"))
    docs += [
        TEMPLATES / "backend" / "后端说明.md.tmpl",
        TEMPLATES / "frontend" / "前端说明.md.tmpl",
    ]
    docs += list((TEMPLATES / "skills").rglob("SKILL.md"))
    for d in docs:
        t = d.read_text()
        for bad, why in [
            (r'msg="', "小写 msg=（Makefile 只认 MSG=）"),
            ("随机密码", "随机密码说法（默认是 admin）"),
            ("db-migrate msg=init", "手动建基线（已自动 stamp）"),
            ("make db-reset", "不存在的命令"),
            ("make db-shell", "不存在的命令"),
        ]:
            assert not re.search(bad, t), f"{d.name} 残留: {why}"


def test_docs_python3_unified():
    """文档统一 python3（第十一轮 🟡：裸 python 在干净机器不存在）。"""
    for d in (
        [ROOT / "使用手册.md", ROOT / "README.md", ROOT / "安装说明.md"]
        + list(TEMPLATES.rglob("*.md.tmpl"))
        + list((TEMPLATES / "skills").rglob("SKILL.md"))
    ):
        t = d.read_text()
        for m in re.finditer(r"(?<![\w./-])python (?=[a-z./])", t):
            ctx = t[max(0, m.start() - 30) : m.end() + 30]
            pytest.fail(f"{d.name} 残留裸 python: ...{ctx}...")


def test_conftest_env_before_app_import():
    """测试隔离：环境变量必须抢在 import app 之前（第五轮 🔴 测试污染开发库）。"""
    t = (TEMPLATES / "backend" / "tests" / "conftest.py").read_text()
    assert t.index('os.environ["DB_TYPE"] = "sqlite"') < t.index(
        "from app.core.config import settings"
    )


# ============================================================
# 五、Makefile 渲染后语法（第八轮 missing separator 回归）
# ============================================================
@pytest.mark.parametrize("mode", ["admin", "server"])
def test_makefile_renders_and_parses(mode):
    """渲染后全部 target 逐个 make -n 解析（弱断言强化：不再只测 start）。"""
    import shutil as _sh

    if not _sh.which("make"):
        pytest.skip("无 make 命令")
    t = (TEMPLATES / "root" / "Makefile.tmpl").read_text()
    if mode == "admin":
        t = t[: t.find("{% else %}")]
    else:
        t = t[t.find("{% else %}") + len("{% else %}") :]
    t = t.replace("{% if enable_redis %}", "").replace("{% endif %}", "")
    t = t.replace("{{ backend_port }}", "8000").replace("{{ frontend_port }}", "3000")
    t = t.replace("{{ project_name }}", "x")
    with tempfile.TemporaryDirectory() as td:
        Path(td, "Makefile").write_text(t)
        Path(td, "backend" if mode == "admin" else ".env").write_text("")
        # 提取全部 target 名
        targets = re.findall(r"^([a-z-]+):\s*##", t, re.M)
        assert len(targets) >= 10, f"target 提取异常: {targets}"
        for tgt in targets:
            r = subprocess.run(
                ["make", "-n", "-C", td, tgt],
                capture_output=True,
                text=True,
                timeout=30,
            )
            ok = (
                r.returncode == 0 or "No such file" in r.stderr or "No rule" in r.stderr
            )
            assert ok, f"make -n {tgt} 失败: {r.stderr[:200]}"


# ============================================================
# 六、第 12 轮补充：模板行为级断言（补防护网缺口）
# ============================================================
def test_compose_renders_valid_yaml():
    """docker-compose 两模式渲染后是合法 YAML 且服务齐全。"""
    import yaml
    from jinja2 import Environment

    t = (TEMPLATES / "root" / "docker-compose.yml.tmpl").read_text()
    for only in ("admin", "server"):
        r = (
            Environment(keep_trailing_newline=True)
            .from_string(t)
            .render(
                project_name="x",
                project_title="X",
                backend_port=8000,
                postgres_port=5432,
                redis_port=6379,
                only=only,
                enable_redis=True,
            )
        )
        d = yaml.safe_load(r)
        for svc in ("backend", "postgres", "adminer", "redis"):
            assert svc in d["services"], f"{only} 模式缺 {svc}"


def test_reset_admin_updates_hash_in_try():
    """reset_admin：密码更新逻辑必须在 try 块内（第十一轮 🔴 死代码回归）。"""
    t = (TEMPLATES / "backend" / "scripts" / "reset_admin.py").read_text()
    ast.parse(t)
    i_user_none = t.find("if user is None")
    i_hash = t.find("user.password_hash = hash_password")
    i_except = t.find("except Exception")
    assert 0 < i_user_none < i_hash < i_except, "重置逻辑跑到 except 死区了"


def test_format_ts_exists_and_used():
    """时区工具存在且被两个系统页 + add_module 模板引用（第十一轮 🔴 时区）。"""
    f = TEMPLATES / "frontend" / "src" / "utils" / "format.ts"
    assert f.exists() and "UTC" in f.read_text()
    for v in ["system/user/index.vue", "system/role/index.vue"]:
        assert (
            "formatTime" in (TEMPLATES / "frontend" / "src" / "views" / v).read_text()
        )
    assert "formatTime" in ADD_MODULE.read_text()


def test_session_sqlite_busy_timeout():
    """SQLite 引擎必须带 busy timeout（第十一轮 🟡 database is locked）。"""
    t = (TEMPLATES / "backend" / "app" / "db" / "session.py").read_text()
    assert '"timeout": 15' in t


def test_user_crud_ilike_fuzzy():
    """用户搜索是 ilike 模糊匹配（第 10 轮前端 agent 修复）。"""
    t = (TEMPLATES / "backend" / "app" / "crud" / "user.py").read_text()
    assert 'ilike(f"%{username}%")' in t


def test_init_port_clash_hint():
    """init.py 生成时必须检测端口占用并提示（第 12 轮 🟠 多项目）。"""
    t = (SCRIPTS / "init.py").read_text()
    assert "端口已被占用" in t and "connect_ex" in t


# ============================================================
# 七、第 13 轮：opencode 双平台支持
# ============================================================
def test_install_sh_supports_dual_platform():
    """install.sh 必须支持 --platform claude|opencode|all + 双目录映射。"""
    t = (ROOT / "install.sh").read_text()
    assert "platform_dir()" in t
    for must in (
        ".claude/skills",
        ".config/opencode/skills",
        "--platform",
        "active_platforms",
    ):
        assert must in t, f"双平台支持缺: {must}"
    import re as _re

    # 平台校验必须存在（防拼错平台名静默装错地方）
    assert _re.search(r'\[\[ "\$PLATFORM" != "all" .* "opencode" \]\]', t)


def test_docs_mention_opencode():
    """三份根文档必须提到 opencode（双平台宣传一致）。"""
    for d in [ROOT / "README.md", ROOT / "安装说明.md", ROOT / "使用手册.md"]:
        assert "opencode" in d.read_text().lower(), f"{d.name} 未提及 opencode"
