# -*- coding: utf-8 -*-
"""
功能: 一键将当前项目上传到 GitHub。
流程: 检查 git/gh -> 初始化仓库 -> 提交代码 -> 创建远程仓库 -> 推送分支。
"""

import shutil
import subprocess
import sys
from pathlib import Path


class GitHubUploader:
    """
    功能: 通过类初始化参数控制上传行为，完成当前项目上传 GitHub。
    输入: 初始化时传入仓库名、分支名、提交信息、远程名、可见性、是否跳过登录检查。
    输出: 调用 upload() 后完成上传流程或抛出异常。
    """

    def __init__(self) -> None:
        """
        功能: 初始化上传配置参数。
        输入: 无; 通过方法体内的配置项直接调整行为。
        输出: 无; 参数非法时抛出异常。
        """
        # GitHub 仓库名: 支持 "owner/repo"; 为空时使用当前目录名
        self.repo_name = "Anh2023.github.io"
        # 推送分支名: 常用 main 或 master
        self.branch = "main"
        # 提交信息: git commit -m 的内容
        self.commit_message = "init: first commit"
        # 远程仓库名: 默认 origin
        self.remote = "origin"
        # 仓库可见性: 仅支持 public/private
        self.visibility = "private"
        # 是否跳过 gh 登录检查: True 跳过, False 自动检查并引导登录
        self.skip_auth = False

        # 规范化并兜底默认值，避免空字符串导致后续命令异常
        self.repo_name = self.repo_name.strip() or Path.cwd().name
        self.branch = self.branch.strip() or "main"
        self.remote = self.remote.strip() or "origin"
        self.commit_message = self.commit_message.strip() or "init: first commit"
        self.skip_auth = bool(self.skip_auth)

        visibility_value = self.visibility.strip().lower()
        if visibility_value not in {"public", "private"}:
            raise RuntimeError("visibility 仅支持: public 或 private")
        self.visibility = visibility_value

    def setup_console_utf8(self) -> None:
        """
        功能: 在 Windows 终端尽量启用 UTF-8，避免中文输出乱码。
        输入: 无。
        输出: 无; 即使设置失败也不中断主流程。
        """
        if sys.platform.startswith("win"):
            try:
                import ctypes

                ctypes.windll.kernel32.SetConsoleCP(65001)
                ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            except Exception:
                pass
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass

    def run_cmd(self, cmd: list[str], capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
        """
        功能: 执行外部命令并返回结果。
        输入: cmd 命令列表; capture_output 是否捕获输出; check 失败时是否抛异常。
        输出: subprocess.CompletedProcess 执行结果对象。
        """
        result = subprocess.run(
            cmd,
            text=True,
            encoding="utf-8",
            errors="ignore",
            capture_output=capture_output,
            check=False,
        )
        if check and result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"命令执行失败: {' '.join(cmd)}\n{detail}")
        return result

    def ensure_tool_exists(self, tool: str) -> None:
        """
        功能: 检查命令行工具是否已安装。
        输入: tool 工具名称，例如 git 或 gh。
        输出: 无; 未安装时抛出异常。
        """
        if shutil.which(tool) is None:
            raise RuntimeError(f"未检测到工具: {tool}，请先安装后再运行脚本。")

    def is_git_repo(self) -> bool:
        """
        功能: 判断当前目录是否为 Git 仓库。
        输入: 无。
        输出: True 表示已是仓库; False 表示不是仓库。
        """
        result = self.run_cmd(["git", "rev-parse", "--is-inside-work-tree"], check=False)
        return result.returncode == 0

    def has_git_commit(self) -> bool:
        """
        功能: 判断当前仓库是否已有提交历史。
        输入: 无。
        输出: True 表示已有提交; False 表示还没有提交。
        """
        result = self.run_cmd(["git", "rev-parse", "--verify", "HEAD"], check=False)
        return result.returncode == 0

    def has_changes_after_add(self) -> bool:
        """
        功能: 判断执行 git add 后是否存在待提交变更。
        输入: 无。
        输出: True 表示存在待提交内容; False 表示无变更。
        """
        result = self.run_cmd(["git", "status", "--porcelain"], check=False)
        return bool(result.stdout.strip())

    def has_git_identity(self) -> bool:
        """
        功能: 判断 Git 用户身份是否已配置。
        输入: 无。
        输出: True 表示 user.name 和 user.email 都已配置; False 表示缺失。
        """
        name = self.run_cmd(["git", "config", "--get", "user.name"], check=False).stdout.strip()
        email = self.run_cmd(["git", "config", "--get", "user.email"], check=False).stdout.strip()
        return bool(name and email)

    def get_remote_url(self, remote: str) -> str:
        """
        功能: 获取指定远程仓库地址。
        输入: remote 远程名称，默认通常是 origin。
        输出: 远程 URL 字符串，不存在时返回空字符串。
        """
        result = self.run_cmd(["git", "remote", "get-url", remote], check=False)
        return result.stdout.strip() if result.returncode == 0 else ""

    def ensure_gh_auth(self) -> None:
        """
        功能: 检查 gh 登录状态，未登录时引导登录。
        输入: 无。
        输出: 无; 登录失败时抛出异常。
        """
        status = self.run_cmd(["gh", "auth", "status"], check=False)
        if status.returncode != 0:
            print("[提示] 检测到 gh 未登录，开始执行登录流程...")
            self.run_cmd(["gh", "auth", "login", "--git-protocol", "https", "--web"], capture_output=False, check=True)

        # 强制 gh 使用 https 协议，避免生成 git@github.com 的 SSH 远程地址
        self.run_cmd(["gh", "config", "set", "git_protocol", "https"], check=False)
        # 配置 git 通过 gh 管理认证，避免 push 时反复认证失败
        self.run_cmd(["gh", "auth", "setup-git"], check=False)

    def to_https_remote_url(self, remote_url: str) -> str:
        """
        功能: 将 GitHub SSH 远程地址转换为 HTTPS 地址。
        输入: remote_url 当前远程 URL。
        输出: 转换后的 URL; 非 GitHub SSH 地址则原样返回。
        """
        url = remote_url.strip()
        if url.startswith("git@github.com:"):
            return f"https://github.com/{url[len('git@github.com:'):]}"
        if url.startswith("ssh://git@github.com/"):
            return f"https://github.com/{url[len('ssh://git@github.com/'):]}"
        return url

    def ensure_remote_https(self, remote: str) -> str:
        """
        功能: 确保远程地址为 GitHub HTTPS 协议。
        输入: remote 远程名。
        输出: 最终远程 URL。
        """
        current_url = self.get_remote_url(remote)
        if not current_url:
            return ""
        https_url = self.to_https_remote_url(current_url)
        if https_url != current_url:
            print(f"[步骤] 远程地址从 SSH 切换为 HTTPS: {https_url}")
            self.run_cmd(["git", "remote", "set-url", remote, https_url], check=True)
        return self.get_remote_url(remote)

    def create_repo_and_push(self, repo: str, visibility: str, remote: str) -> None:
        """
        功能: 创建 GitHub 仓库并推送当前目录代码。
        输入: repo 仓库名(可含 owner/repo); visibility 为 public/private; remote 远程名。
        输出: 无; 失败时抛出异常。
        """
        # 分两步执行，避免 gh 直接 push 时因 SSH 公钥未配置失败
        cmd = ["gh", "repo", "create", repo, f"--{visibility}", "--source", ".", "--remote", remote]
        self.run_cmd(cmd, capture_output=False, check=True)
        self.ensure_remote_https(remote)
        self.push_to_existing_remote(remote, self.branch)

    def push_to_existing_remote(self, remote: str, branch: str) -> None:
        """
        功能: 将当前分支推送到已存在的远程仓库。
        输入: remote 远程名; branch 分支名。
        输出: 无; 推送失败时抛出异常。
        """
        self.run_cmd(["git", "push", "-u", remote, branch], capture_output=False, check=True)

    def upload(self) -> None:
        """
        功能: 执行完整上传流程。
        输入: 无，使用初始化参数。
        输出: 无; 失败时抛出异常。
        """
        self.setup_console_utf8()
        self.ensure_tool_exists("git")
        self.ensure_tool_exists("gh")

        if not self.is_git_repo():
            print("[步骤] 初始化 Git 仓库")
            self.run_cmd(["git", "init"], check=True)
        else:
            print("[步骤] 已检测到 Git 仓库，跳过初始化")

        print("[步骤] 暂存当前目录全部文件")
        self.run_cmd(["git", "add", "."], check=True)

        need_commit = self.has_changes_after_add() or not self.has_git_commit()
        if need_commit:
            if not self.has_git_identity():
                raise RuntimeError(
                    "未检测到 git 用户信息，请先执行:\n"
                    "git config --global user.name \"你的GitHub用户名\"\n"
                    "git config --global user.email \"你的GitHub邮箱\""
                )
            print(f"[步骤] 提交代码: {self.commit_message}")
            self.run_cmd(["git", "commit", "-m", self.commit_message], check=True)
        else:
            print("[步骤] 无需提交：当前没有新变更")

        print(f"[步骤] 设置主分支为 {self.branch}")
        self.run_cmd(["git", "branch", "-M", self.branch], check=True)

        remote_url = self.get_remote_url(self.remote)
        if remote_url:
            print(f"[步骤] 检测到远程 {self.remote}: {remote_url}")
            print("[步骤] 直接推送到现有远程")
            if not self.skip_auth:
                self.ensure_gh_auth()
            self.ensure_remote_https(self.remote)
            self.push_to_existing_remote(self.remote, self.branch)
        else:
            if not self.skip_auth:
                self.ensure_gh_auth()
            print(f"[步骤] 创建 GitHub 仓库并推送: {self.repo_name} ({self.visibility})")
            self.create_repo_and_push(self.repo_name, self.visibility, self.remote)

        final_remote = self.get_remote_url(self.remote)
        print("\n[完成] 上传完成")
        if final_remote:
            print(f"[远程地址] {final_remote}")


if __name__ == "__main__":
    try:
        uploader = GitHubUploader()
        uploader.upload()
    except Exception as exc:
        print(f"[失败] {exc}", file=sys.stderr)
        sys.exit(1)
