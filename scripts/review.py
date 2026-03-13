#!/usr/bin/env python3
"""
AI Code Review Bot - 使用智谱 GLM 分析 PR 并给出建议
"""

import argparse
import os
import requests
from zhipuai import ZhipuAI


def get_pr_info(repo: str, pr_number: int, token: str) -> dict:
    """获取 PR 基本信息"""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def create_review_comment(repo: str, pr_number: int, body: str, token: str):
    """在 PR 上发布评论"""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "body": body,
        "event": "COMMENT"
    }
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()


def analyze_diff(diff_content: str, api_key: str) -> str:
    """使用智谱 GLM 分析代码变更"""
    client = ZhipuAI(api_key=api_key)
    
    prompt = f"""你是一个专业的代码审查专家。请分析以下 Git diff 内容，给出具体的改进建议。

重点关注：
1. 潜在的 bug 或逻辑问题
2. 代码风格和最佳实践
3. 性能优化建议
4. 安全隐患
5. 可读性和可维护性

请用中文回复，结构清晰，按文件或模块分组给出建议。如果没有明显问题，可以简短说明。

---
Git Diff:
{diff_content}
---

请给出你的审查意见："""

    response = client.chat.completions.create(
        model="glm-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000
    )
    
    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(description="AI Code Review Bot")
    parser.add_argument("--repo", required=True, help="GitHub 仓库 (owner/repo)")
    parser.add_argument("--pr-number", type=int, required=True, help="PR 编号")
    parser.add_argument("--diff-file", required=True, help="diff 文件路径")
    args = parser.parse_args()

    # 从环境变量获取凭证
    github_token = os.environ.get("GITHUB_TOKEN")
    zhipu_api_key = os.environ.get("ZHIPU_API_KEY")
    
    if not github_token:
        raise ValueError("GITHUB_TOKEN 环境变量未设置")
    if not zhipu_api_key:
        raise ValueError("ZHIPU_API_KEY 环境变量未设置")

    # 读取 diff
    with open(args.diff_file, "r", encoding="utf-8") as f:
        diff_content = f.read()
    
    if not diff_content.strip():
        print("Diff 为空，跳过审查")
        return

    print(f"正在审查 PR #{args.pr_number}...")
    
    # 获取 PR 信息
    pr_info = get_pr_info(args.repo, args.pr_number, github_token)
    pr_title = pr_info.get("title", "")
    pr_author = pr_info.get("user", {}).get("login", "unknown")
    
    print(f"PR 标题: {pr_title}")
    print(f"作者: {pr_author}")
    
    # 分析 diff
    print("正在调用智谱 GLM 分析...")
    review_result = analyze_diff(diff_content, zhipu_api_key)
    
    # 格式化评论
    comment_body = f"""## 🤖 AI 代码审查报告

**PR**: #{args.pr_number} - {pr_title}
**作者**: @{pr_author}

---

{review_result}

---
*由皮皮马 🐴 自动生成 | 使用智谱 GLM-4*"""

    # 发布评论
    print("正在发布审查评论...")
    create_review_comment(args.repo, args.pr_number, comment_body, github_token)
    print("✅ 审查完成！")


if __name__ == "__main__":
    main()
