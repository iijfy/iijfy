# scripts/generate_readme.py
# 목적: catalog.yml을 읽어서 README.template.md의 PROJECTS_START~END 구간을 자동으로 채운 README.md를 생성합니다.

from __future__ import annotations

import os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog.yml"
TEMPLATE = ROOT / "README.template.md"
OUT = ROOT / "README.md"

START = "<!-- PROJECTS_START -->"
END = "<!-- PROJECTS_END -->"


def repo_url(username: str, repo: str) -> str:
    return f"https://github.com/{username}/{repo}"


def render_featured(username: str, featured: list[str], repo_meta: dict[str, dict]) -> str:
    lines = []
    lines.append("## 🚀 GenAI Portfolio Highlights\n")
    for r in featured:
        meta = repo_meta.get(r, {})
        desc = meta.get("desc", "").strip()
        url = repo_url(username, r)

        # desc가 비어도 깨지지 않게 처리
        if desc:
            lines.append(f"- **[{r}]({url})**  \n  {desc}")
        else:
            lines.append(f"- **[{r}]({url})**")
    lines.append("")  # blank line
    return "\n".join(lines)


def render_categories(username: str, categories: dict, repo_meta: dict[str, dict]) -> str:
    lines = []
    lines.append("## 🧭 Project Index (카테고리별)\n")

    for cat_name, items in categories.items():
        lines.append("<details>")
        lines.append(f"<summary><b>{cat_name}</b></summary>\n")

        for item in items:
            repo = item["repo"] if isinstance(item, dict) else str(item)
            meta = repo_meta.get(repo, {})
            desc = meta.get("desc", "").strip()
            stack = meta.get("stack", [])
            url = repo_url(username, repo)

            if stack:
                stack_txt = ", ".join(stack)
                stack_txt = f" `[{stack_txt}]`"
            else:
                stack_txt = ""

            if desc:
                lines.append(f"- [{repo}]({url}){stack_txt} — {desc}")
            else:
                lines.append(f"- [{repo}]({url}){stack_txt}")

        lines.append("\n</details>\n")
    return "\n".join(lines).strip() + "\n"


def build_repo_meta(categories: dict) -> dict[str, dict]:
    """
    catalog.yml에서 repo별 desc/stack을 빠르게 찾기 위한 맵을 만듭니다.
    """
    repo_meta: dict[str, dict] = {}
    for _, items in categories.items():
        for item in items:
            if isinstance(item, dict):
                repo = item.get("repo")
                if repo:
                    repo_meta[repo] = {
                        "desc": item.get("desc", ""),
                        "stack": item.get("stack", []),
                    }
    return repo_meta


def main() -> None:
    if not CATALOG.exists():
        raise FileNotFoundError(f"catalog.yml not found: {CATALOG}")
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"README.template.md not found: {TEMPLATE}")

    data = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))

    username = data.get("username") or os.getenv("GITHUB_USERNAME")
    if not username:
        raise ValueError("username이 필요합니다. catalog.yml의 username 또는 환경변수 GITHUB_USERNAME을 설정하세요.")

    featured = data.get("featured", [])
    categories = data.get("categories", {})

    repo_meta = build_repo_meta(categories)

    template_text = TEMPLATE.read_text(encoding="utf-8")
    if START not in template_text or END not in template_text:
        raise ValueError("README.template.md에 PROJECTS_START/END 마커가 없습니다.")

    auto_block = []
    auto_block.append(START)
    auto_block.append("")  # readability
    auto_block.append(render_featured(username, featured, repo_meta))
    auto_block.append(render_categories(username, categories, repo_meta))
    auto_block.append(END)

    auto_text = "\n".join(auto_block)

    # 마커 사이 구간 교체
    before = template_text.split(START)[0]
    after = template_text.split(END)[1]
    out_text = before + auto_text + after

    OUT.write_text(out_text, encoding="utf-8")
    print("README.md updated successfully.")


if __name__ == "__main__":
    main()
