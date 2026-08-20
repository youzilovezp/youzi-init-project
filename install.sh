#!/usr/bin/env bash
# ============================================================================
# youzi-init-project 一键安装 / 卸载 / 更新 / 状态查询
#
# 用法：
#   ./install.sh install    # 安装到 ~/.claude/skills/youzi-init-project
#   ./install.sh uninstall  # 卸载
#   ./install.sh update     # 重新链接（仅符号链接模式有效）
#   ./install.sh status     # 查看安装状态
#   ./install.sh help       # 显示帮助
#
# 选项（适用于 install / update）：
#   --dir <path>    自定义安装目录（默认 ~/.claude/skills）
#   --mode <link|copy>  安装方式：符号链接（默认）或复制
#
# 兼容：macOS（BSD tools）+ Linux（GNU tools）
# 依赖：bash 3.2+、python3（仅 status 命令需要）
# ============================================================================

set -eo pipefail

# ---------- 颜色（仅在 TTY 下启用） ----------
if [[ -t 1 ]]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
    BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; BOLD=''; RESET=''
fi

info()  { printf "${BLUE}ℹ ${RESET}%s\n" "$*"; }
ok()    { printf "${GREEN}✅${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}⚠️ ${RESET}%s\n" "$*"; }
err()   { printf "${RED}❌${RESET} %s\n" "$*" >&2; }
title() { printf "\n${BOLD}${BLUE}== %s ==${RESET}\n" "$*"; }

# ---------- 检测脚本所在目录（不依赖 pwd） ----------
SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

# ---------- 默认配置 ----------
SKILL_NAME="youzi-init-project"
DEFAULT_DIR="$HOME/.claude/skills"
INSTALL_DIR="$DEFAULT_DIR"
INSTALL_MODE="link"  # link | copy

# ---------- 帮助 ----------
print_help() {
    cat <<EOF
${BOLD}youzi-init-project${RESET} - 一键安装 / 卸载 / 更新

${BOLD}用法:${RESET}
  $(basename "$0") <command> [options]

${BOLD}命令:${RESET}
  ${GREEN}install${RESET}      安装 Skill 到 Claude Code（默认符号链接）
  ${GREEN}uninstall${RESET}    卸载已安装的 Skill
  ${GREEN}update${RESET}       刷新符号链接（如果用复制模式会重新复制）
  ${GREEN}status${RESET}       查看安装状态
  ${GREEN}help${RESET}         显示本帮助

${BOLD}选项（适用于 install/update）:${RESET}
  --dir <path>        自定义安装目录（默认: $DEFAULT_DIR）
  --mode <link|copy>  安装方式（默认: link）
                      link - 创建符号链接，仓库修改即时生效
                      copy - 复制文件，需要 update 才能同步修改

${BOLD}示例:${RESET}
  $(basename "$0") install                     # 安装到默认位置
  $(basename "$0") install --mode copy         # 复制方式安装
  $(basename "$0") install --dir ~/my-skills   # 安装到自定义位置
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
            --dir)  INSTALL_DIR="$2"; shift 2 ;;
            --mode) INSTALL_MODE="$2"; shift 2 ;;
            -h|--help) print_help; exit 0 ;;
            *)
                err "未知参数: $1"
                print_help
                exit 1
                ;;
        esac
    done

    TARGET="$INSTALL_DIR/$SKILL_NAME"
}

# ---------- install ----------
do_install() {
    title "安装 $SKILL_NAME"

    # 0. 验证源目录
    if [[ ! -f "$SCRIPT_DIR/SKILL.md" ]]; then
        err "当前目录不是有效的 skill 仓库：$SCRIPT_DIR"
        err "缺少 SKILL.md 文件"
        exit 1
    fi

    info "源目录：$SCRIPT_DIR"
    info "目标位置：$TARGET"
    info "安装方式：$INSTALL_MODE"

    # 1. 创建 ~/.claude/skills
    mkdir -p "$INSTALL_DIR"

    # 2. 检查目标是否已存在
    if [[ -e "$TARGET" || -L "$TARGET" ]]; then
        if [[ -L "$TARGET" ]]; then
            warn "目标已是符号链接：$TARGET -> $(readlink "$TARGET")"
        else
            warn "目标已存在：$TARGET"
        fi
        printf "是否替换？[y/N] "; read -r ans
        if [[ "${ans:-N}" != "y" && "${ans:-N}" != "Y" ]]; then
            info "已取消"
            exit 0
        fi
        /bin/rm -rf "$TARGET"
    fi

    # 3. 执行安装
    case "$INSTALL_MODE" in
        link)
            ln -s "$SCRIPT_DIR" "$TARGET"
            ok "已创建符号链接"
            ;;
        copy)
            cp -R "$SCRIPT_DIR" "$TARGET"
            ok "已复制文件"
            ;;
        *)
            err "未知安装模式：$INSTALL_MODE（应为 link 或 copy）"
            exit 1
            ;;
    esac

    # 4. 验证
    if [[ ! -e "$TARGET/SKILL.md" ]]; then
        err "安装验证失败：$TARGET/SKILL.md 不存在"
        exit 1
    fi

    ok "安装成功！"
    echo
    title "下一步"
    cat <<EOF
  1. ${BOLD}重启 Claude Code${RESET}（已运行的会话需要重启以加载 Skill）

  2. 在 Claude Code 中输入以下命令之一：
     ${GREEN}/yz:init-admin my-admin${RESET}    # 完整前后端
     ${GREEN}/yz:init-server my-api${RESET}    # 仅后端 + 中间件
     ${GREEN}/yz:init-ui my-web${RESET}        # 仅前端

  3. 按对话中的提示回答问题，Skill 会自动生成项目

EOF
}

# ---------- uninstall ----------
do_uninstall() {
    title "卸载 $SKILL_NAME"

    if [[ ! -e "$TARGET" && ! -L "$TARGET" ]]; then
        info "未安装：$TARGET 不存在"
        exit 0
    fi

    if [[ -L "$TARGET" ]]; then
        warn "检测到符号链接：$TARGET -> $(readlink "$TARGET")"
        info "将仅删除链接（不影响源目录）"
    elif [[ -d "$TARGET" ]]; then
        warn "检测到目录：$TARGET"
        info "将递归删除整个目录"
    fi

    printf "确认卸载？[y/N] "; read -r ans
    if [[ "${ans:-N}" != "y" && "${ans:-N}" != "Y" ]]; then
        info "已取消"
        exit 0
    fi

    /bin/rm -rf "$TARGET"
    ok "已卸载：$TARGET"

    # 提示用户清理 SKILL.md cache
    cat <<EOF

  ${YELLOW}提示${RESET}：Claude Code 在启动时读取 SKILL.md。
  如果之前加载过，建议重启 Claude Code。
EOF
}

# ---------- update ----------
do_update() {
    title "更新 $SKILL_NAME"

    if [[ ! -e "$TARGET" && ! -L "$TARGET" ]]; then
        warn "未安装：$TARGET 不存在，请先执行 install"
        exit 1
    fi

    if [[ -L "$TARGET" ]]; then
        # 符号链接：检查指向是否仍是本仓库
        local link_target
        link_target="$(readlink "$TARGET")"
        if [[ "$link_target" == "$SCRIPT_DIR" ]]; then
            ok "已是最新（符号链接指向当前仓库）"
            ok "  $TARGET -> $link_target"
            info "符号链接模式下，源目录的任何修改都会即时生效，无需 update"
            exit 0
        else
            warn "符号链接指向其他位置：$link_target"
            info "重新指向当前目录：$SCRIPT_DIR"
            /bin/rm "$TARGET"
            ln -s "$SCRIPT_DIR" "$TARGET"
            ok "已更新链接"
        fi
    else
        # 复制模式：重新复制
        info "检测到复制模式，重新复制文件..."
        /bin/rm -rf "$TARGET"
        cp -R "$SCRIPT_DIR" "$TARGET"
        ok "已更新"
    fi
}

# ---------- status ----------
do_status() {
    title "$SKILL_NAME 安装状态"

    printf "${BOLD}源目录${RESET}：%s\n" "$SCRIPT_DIR"
    printf "${BOLD}目标位置${RESET}：%s\n" "$TARGET"
    printf "${BOLD}安装方式偏好${RESET}：%s\n\n" "$INSTALL_MODE"

    if [[ -L "$TARGET" ]]; then
        printf "${GREEN}状态${RESET}：${GREEN}已安装（符号链接）${RESET}\n"
        printf "  链接：%s -> %s\n" "$TARGET" "$(readlink "$TARGET")"
        if [[ "$(readlink "$TARGET")" == "$SCRIPT_DIR" ]]; then
            echo "  ✅ 指向当前仓库，修改即时生效"
        else
            echo "  ⚠️  指向其他位置，建议执行 update"
        fi
    elif [[ -d "$TARGET" ]]; then
        printf "${YELLOW}状态${RESET}：${YELLOW}已安装（复制模式）${RESET}\n"
        printf "  目录：%s\n" "$TARGET"
        echo "  ⚠️  复制模式下，源目录的修改不会自动同步，需执行 update"
    else
        printf "${RED}状态${RESET}：${RED}未安装${RESET}\n"
        echo "  执行 ./install.sh install 进行安装"
        return 1
    fi

    # 检查关键文件
    echo
    echo "关键文件检查："
    for f in SKILL.md scripts/init.py templates; do
        if [[ -e "$TARGET/$f" ]]; then
            ok "$f"
        else
            err "$f (缺失)"
        fi
    done

    # 检查 python3
    echo
    echo "环境检查："
    if command -v python3 >/dev/null 2>&1; then
        ok "python3: $(python3 --version 2>&1)"
    else
        warn "python3: 未安装（init.py 需要 python3）"
    fi

    # 检查 jinja2
    if python3 -c "import jinja2" 2>/dev/null; then
        ok "jinja2: $(python3 -c 'import jinja2; print(jinja2.__version__)')"
    else
        warn "jinja2: 未安装（运行 pip install jinja2）"
    fi

    return 0
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
