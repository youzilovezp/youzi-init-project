#!/usr/bin/env bash
# ============================================================================
# youzi-init-project 一键安装 / 卸载 / 更新 / 状态查询
#
# 用法：
#   ./install.sh install    # 安装三个独立 skill
#   ./install.sh uninstall  # 卸载
#   ./install.sh update     # 刷新符号链接
#   ./install.sh status     # 查看安装状态
#   ./install.sh help       # 显示帮助
#
# 安装后会创建三个独立 skill：
#   ~/.claude/skills/yz-init-admin/    → /yz-init-admin（完整前后端）
#   ~/.claude/skills/yz-init-server/   → /yz-init-server（后端 + 中间件）
#   ~/.claude/skills/yz-init-ui/       → /yz-init-ui（仅前端）
#
# 兼容：macOS（BSD tools）+ Linux（GNU tools）
# 输出：纯文本 + emoji，不使用 ANSI 转义
# ============================================================================

set -eo pipefail

# ---------- 纯文本样式 ----------
info()  { printf "  ℹ  %s\n" "$*"; }
ok()    { printf "  ✅  %s\n" "$*"; }
warn()  { printf "  ⚠️  %s\n" "$*"; }
err()   { printf "  ❌  %s\n" "$*" >&2; }
title() { printf "\n== %s ==\n" "$*"; }
hr()    { printf -- "----------------------------------------\n"; }

# ---------- 安全删除：symlink 用 unlink，目录用 rm -rf ----------
# 用法：safe_rm <path>
# 关键修复：rm -rf 跟随符号链接会删除链接指向的目录内容，
# 这里分开处理 symlink 与 directory。
safe_rm() {
    local p="$1"
    if [[ -L "$p" ]]; then
        rm "$p"                              # 符号链接：只删链接本身
    elif [[ -d "$p" ]]; then
        /bin/rm -rf "$p"                     # 真目录：递归删
    elif [[ -e "$p" ]]; then
        rm -f "$p"                           # 文件：直接删
    fi
    # 不存在：什么都不做
}

# ---------- 检测脚本所在目录（用物理路径，避免符号链接误判） ----------
SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd -P)"

# ---------- 默认配置 ----------
SKILLS=(yz-init-admin yz-init-server yz-init-ui)
DEFAULT_DIR="$HOME/.claude/skills"
INSTALL_DIR="$DEFAULT_DIR"
INSTALL_MODE="link"  # link | copy

# ---------- 帮助 ----------
print_help() {
    cat <<EOF
youzi-init-project - 一键安装 / 卸载 / 更新

用法:
  $(basename "$0") <command> [options]

命令:
  install      安装三个 Skill 到 Claude Code
               ~/.claude/skills/yz-init-admin
               ~/.claude/skills/yz-init-server
               ~/.claude/skills/yz-init-ui
  uninstall    卸载已安装的 Skill
  update       刷新符号链接（link 模式自动生效）
  status       查看三个 Skill 的安装状态
  help         显示本帮助

选项（适用于 install/update）:
  --dir <path>        自定义安装目录（默认: $DEFAULT_DIR）
  --mode <link|copy>  安装方式（默认: link）
                      link - 共享 scripts/templates 符号链接
                      copy - 完整复制所有文件

示例:
  $(basename "$0") install                     # 默认安装三个 skill
  $(basename "$0") install --mode copy         # 复制模式
  $(basename "$0") install --dir ~/my-skills   # 自定义目录
  $(basename "$0") update                      # 刷新安装
  $(basename "$0") uninstall                   # 卸载
  $(basename "$0") status                      # 查看状态

EOF
}

# ---------- 参数解析 ----------
parse_args() {
    if [[ $# -eq 0 ]]; then
        print_help
        exit 0
    fi

    COMMAND="$1"; shift

    while [[ $# -gt 0 ]]; do
        case "$1" in
            # 支持 --dir=path 与 --dir path 两种形式
            --dir=*)
                INSTALL_DIR="${1#*=}"
                shift
                ;;
            --dir)
                if [[ $# -lt 2 ]]; then
                    err "--dir 需要一个参数值"
                    exit 1
                fi
                if [[ "$2" == -* ]]; then
                    err "--dir 的参数值不能以 - 开头: $2"
                    exit 1
                fi
                INSTALL_DIR="$2"
                shift 2
                ;;
            --mode=*)
                INSTALL_MODE="${1#*=}"
                shift
                ;;
            --mode)
                if [[ $# -lt 2 ]]; then
                    err "--mode 需要一个参数值"
                    exit 1
                fi
                if [[ "$2" != "link" && "$2" != "copy" ]]; then
                    err "--mode 必须是 link 或 copy，得到: $2"
                    exit 1
                fi
                INSTALL_MODE="$2"
                shift 2
                ;;
            -h|--help) print_help; exit 0 ;;
            *)
                err "未知参数: $1"
                print_help
                exit 1
                ;;
        esac
    done

    # 规范化：去掉尾斜杠，避免路径出现 //yz-init-admin 这种双斜杠
    INSTALL_DIR="${INSTALL_DIR%/}"
}

# ---------- 安全覆盖 prompt（非 TTY 时默认 N，绝不覆盖用户数据） ----------
confirm_replace() {
    local target="$1"
    if [[ ! -t 0 ]]; then
        warn "非交互式 stdin，自动跳过覆盖：$target"
        return 1
    fi
    printf "  是否替换？[y/N] "
    # 用 || 兜底 stdin EOF / 错误
    local ans
    if ! read -r ans; then
        ans="N"
    fi
    case "${ans:-N}" in
        y|Y|yes|YES|Yes) return 0 ;;
        *) return 1 ;;
    esac
}

# ---------- 安装单个 skill ----------
install_one_skill() {
    local skill_name="$1"
    local target="$INSTALL_DIR/$skill_name"

    # 源 SKILL.md 路径
    local src_skill_md
    case "$skill_name" in
        yz-init-admin)  src_skill_md="$SCRIPT_DIR/templates/skills/admin/SKILL.md" ;;
        yz-init-server) src_skill_md="$SCRIPT_DIR/templates/skills/server/SKILL.md" ;;
        yz-init-ui)     src_skill_md="$SCRIPT_DIR/templates/skills/ui/SKILL.md" ;;
        *) err "未知 skill: $skill_name"; return 1 ;;
    esac

    # 检查目标
    if [[ -e "$target" || -L "$target" ]]; then
        warn "目标已存在：$target"
        if ! confirm_replace "$target"; then
            info "$skill_name 跳过"
            return 0
        fi
        # 用 safe_rm 区分 symlink / directory，绝不跟随 symlink 删用户数据
        safe_rm "$target"
    fi

    mkdir -p "$target"

    # 复制 SKILL.md
    cp "$src_skill_md" "$target/SKILL.md"

    case "$INSTALL_MODE" in
        link)
            ln -s "$SCRIPT_DIR/scripts" "$target/scripts"
            ln -s "$SCRIPT_DIR/templates" "$target/templates"
            ok "已创建 $skill_name（符号链接）"
            ;;
        copy)
            cp -R "$SCRIPT_DIR/scripts" "$target/scripts"
            cp -R "$SCRIPT_DIR/templates" "$target/templates"
            ok "已创建 $skill_name（完整复制）"
            ;;
        *)
            err "未知安装模式：$INSTALL_MODE"
            return 1
            ;;
    esac
}

# ---------- install ----------
do_install() {
    title "安装三个 Skill"

    # 验证源目录
    if [[ ! -d "$SCRIPT_DIR/scripts" || ! -d "$SCRIPT_DIR/templates" ]]; then
        err "当前目录不是有效的 skill 仓库：$SCRIPT_DIR"
        err "缺少 scripts/ 或 templates/ 目录"
        exit 1
    fi

    # 关键修复：原脚本只检查 admin 的 SKILL.md，
    # server / ui 缺失时 admin 装成功再崩，留下烂摊子。
    # 这里循环检查全部 3 个 skill 的 SKILL.md
    local missing_skill_md=()
    for skill in "${SKILLS[@]}"; do
        case "$skill" in
            yz-init-admin)  local path="$SCRIPT_DIR/templates/skills/admin/SKILL.md" ;;
            yz-init-server) local path="$SCRIPT_DIR/templates/skills/server/SKILL.md" ;;
            yz-init-ui)     local path="$SCRIPT_DIR/templates/skills/ui/SKILL.md" ;;
        esac
        if [[ ! -f "$path" ]]; then
            missing_skill_md+=("$path")
        fi
    done
    if [[ ${#missing_skill_md[@]} -gt 0 ]]; then
        err "缺少以下 SKILL.md 模板："
        for p in "${missing_skill_md[@]}"; do
            err "  - $p"
        done
        exit 1
    fi

    info "源目录：$SCRIPT_DIR"
    info "目标目录：$INSTALL_DIR"
    info "安装方式：$INSTALL_MODE"
    info "将安装：${SKILLS[*]}"

    mkdir -p "$INSTALL_DIR"

    for skill in "${SKILLS[@]}"; do
        install_one_skill "$skill"
    done

    ok "全部安装完成！"
    echo
    title "下一步"
    hr
    cat <<'EOF'
  1. 重启 Claude Code（已运行的会话需要重启以加载 Skill）

  2. 在 Claude Code 中输入以下命令之一：

        /yz-init-admin my-admin     完整前后端 + 中间件
        /yz-init-server my-api     后端 + 中间件
        /yz-init-ui my-web         仅前端

  3. 按对话中的提示回答问题，Skill 会自动生成项目

EOF
    hr
}

# ---------- uninstall ----------
do_uninstall() {
    title "卸载三个 Skill"

    local found=0
    for skill in "${SKILLS[@]}"; do
        local target="$INSTALL_DIR/$skill"
        if [[ -e "$target" || -L "$target" ]]; then
            safe_rm "$target"      # 用 safe_rm 区分 symlink / 目录
            ok "已删除 $skill"
            found=1
        fi
    done

    if [[ $found -eq 0 ]]; then
        info "未安装任何 skill"
        exit 0
    fi

    cat <<EOF

  提示：Claude Code 在启动时读取 SKILL.md。
        如果之前加载过，建议重启 Claude Code。

EOF
}

# ---------- 检测已安装 skill 的真实模式 ----------
detect_install_mode() {
    local target="$1"
    # 优先检查内部 scripts 是不是 symlink（绝大多数情况）
    if [[ -L "$target/scripts" ]]; then
        echo "link"
    else
        echo "copy"
    fi
}

# ---------- update ----------
do_update() {
    title "更新三个 Skill"

    local found=0
    for skill in "${SKILLS[@]}"; do
        local target="$INSTALL_DIR/$skill"
        if [[ ! -e "$target" && ! -L "$target" ]]; then
            warn "$skill 未安装，跳过"
            continue
        fi
        found=1

        # 检测已安装的真实模式（避免 INSTALL_MODE 全局变量被覆盖）
        local actual_mode
        actual_mode=$(detect_install_mode "$target")

        if [[ "$actual_mode" == "link" ]]; then
            # link 模式：检查 scripts 是否指向当前仓库
            if [[ -L "$target/scripts" ]]; then
                local cur
                cur="$(readlink "$target/scripts")"
                if [[ "$cur" == "$SCRIPT_DIR/scripts" ]]; then
                    info "$skill 已是最新（指向当前仓库）"
                    continue
                fi
            fi
            # scripts 指向别处 / 断了 → 重新链接（安全删除）
            safe_rm "$target"
            install_one_skill "$skill"
        else
            # copy 模式：先备份再覆盖，避免覆盖用户本地修改
            if [[ -d "$target/scripts" || -L "$target/scripts" ]]; then
                local backup_dir
                backup_dir="$target/.scripts.bak.$(date +%Y%m%d_%H%M%S)"
                if [[ -d "$target/scripts" ]]; then
                    cp -R "$target/scripts" "$backup_dir"
                fi
                safe_rm "$target/scripts"
            fi
            if [[ -d "$target/templates" || -L "$target/templates" ]]; then
                local backup_dir
                backup_dir="$target/.templates.bak.$(date +%Y%m%d_%H%M%S)"
                if [[ -d "$target/templates" ]]; then
                    cp -R "$target/templates" "$backup_dir"
                fi
                safe_rm "$target/templates"
            fi
            cp -R "$SCRIPT_DIR/scripts" "$target/scripts"
            cp -R "$SCRIPT_DIR/templates" "$target/templates"
            cp "$SCRIPT_DIR/templates/skills/${skill#yz-init-}/SKILL.md" "$target/SKILL.md"
            ok "已更新 $skill（复制模式，旧版本备份到 .*.bak.*）"
        fi
    done

    if [[ $found -eq 0 ]]; then
        warn "未安装任何 skill，请先执行 install"
        exit 1
    fi
}

# ---------- status ----------
do_status() {
    title "youzi-init-project 安装状态"
    hr
    printf "  源目录：    %s\n" "$SCRIPT_DIR"
    printf "  目标目录：  %s\n" "$INSTALL_DIR"
    hr

    for skill in "${SKILLS[@]}"; do
        local target="$INSTALL_DIR/$skill"
        printf "  [%s]\n" "$skill"
        if [[ -L "$target" ]]; then
            # target 本身是 symlink（少见但可能）
            local link
            link="$(readlink "$target")"
            printf "    状态：    已安装（指向 %s）\n" "$link"
            printf "    ⚠️  target 是符号链接，建议检查\n"
        elif [[ -L "$target/scripts" ]]; then
            local link
            link="$(readlink "$target/scripts")"
            printf "    状态：    已安装（符号链接）\n"
            printf "    scripts：%s\n" "$link"
            if [[ "$link" == "$SCRIPT_DIR/scripts" ]]; then
                printf "    ✅ 指向当前仓库，修改即时生效\n"
            else
                printf "    ⚠️  指向其他位置，建议 update\n"
            fi
        elif [[ -d "$target" ]]; then
            printf "    状态：    已安装（复制模式）\n"
            printf "    ⚠️  复制模式下需 update 同步\n"
        else
            printf "    状态：    未安装\n"
            echo
            continue
        fi
        if [[ -e "$target/SKILL.md" ]]; then
            printf "    SKILL.md：✅\n"
        else
            printf "    SKILL.md：❌ 缺失\n"
        fi
        echo
    done

    # 环境检查
    echo "  环境检查："
    if command -v python3 >/dev/null 2>&1; then
        py_ver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        py_ok=$(python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)')
        if [ $? -eq 0 ] 2>/dev/null || python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
            echo "    ✅ python3: $(python3 --version 2>&1)"
        else
            echo "    ⚠️  python3: ${py_ver} 版本过低（需要 3.11+，python.org 下载新版）"
        fi
    else
        echo "    ⚠️  python3: 未安装（必须）"
    fi
    if command -v node >/dev/null 2>&1; then
        echo "    ✅ node: $(node --version 2>&1)"
    else
        echo "    ⚠️  node: 未安装（前端必需，nodejs.org 下载 LTS）"
    fi
    if command -v pnpm >/dev/null 2>&1; then
        echo "    ✅ pnpm: $(pnpm --version 2>&1)"
    elif command -v npm >/dev/null 2>&1; then
        echo "    ℹ️  pnpm: 未安装（将回退用 npm，或 npm install -g pnpm 提速）"
    else
        echo "    ⚠️  pnpm/npm: 都未安装（前端必需）"
    fi
    if command -v git >/dev/null 2>&1; then
        echo "    ✅ git: $(git --version 2>&1)"
    else
        echo "    ℹ️  git: 未安装（--init-git 会跳过；git clone 则必须）"
    fi
    if python3 -c "import jinja2" 2>/dev/null; then
        echo "    ✅ jinja2: $(python3 -c 'import jinja2; print(jinja2.__version__)')"
    else
        echo "    ⚠️  jinja2: 未安装（scripts/init.py 需要；pip install jinja2）"
    fi
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            echo "    ✅ docker: $(docker --version 2>&1)（daemon 运行中）"
        else
            echo "    ⚠️  docker: 已安装但 daemon 未启动——打开 Docker Desktop 等图标变绿再试"
        fi
    else
        echo "    ⚠️  docker: 未安装（make start 起 PostgreSQL 需要；本机已装 PG 可忽略）"
    fi
}

# ---------- 主入口 ----------
main() {
    parse_args "$@"

    case "$COMMAND" in
        install)   do_install ;;
        uninstall) do_uninstall ;;
        update)    do_update ;;
        status)    do_status ;;
        help)      print_help ;;
        *)
            err "未知命令：$COMMAND"
            print_help
            exit 1
            ;;
    esac
}

main "$@"
