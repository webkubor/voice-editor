"""voice ai — AI 文案助手命令（需 FreeLLMAPI 服务）

用法:
    voice ai-script "写一段武侠旁白，讲剑客归隐山林" --words 200
    voice ai-polish "原文..." --style "更激昂"
"""

import typer
from rich.console import Console

console = Console()


def ai_script(
    prompt: str = typer.Argument(..., help="文案描述，如：写一段武侠旁白"),
    words: int = typer.Option(None, "--words", "-w", help="目标字数"),
):
    """AI 文案生成 — 根据描述生成配音文案"""
    from core.llm_client import generate_script, check_status

    status = check_status()
    if not status["available"]:
        console.print("[red]FreeLLMAPI 未连接[/red]")
        console.print("[dim]安装: curl -fsSL https://freellmapi.co/install.sh | bash[/dim]")
        raise typer.Exit(1)

    console.print(f"[cyan]生成中...[/cyan] {prompt}")
    try:
        result = generate_script(prompt, words)
        console.print()
        console.print(result)
        console.print()
        console.print(f"[green]生成完成，{len(result)} 字[/green]")
    except Exception as e:
        console.print(f"[red]生成失败: {e}[/red]")
        raise typer.Exit(1)


def ai_polish(
    text: str = typer.Argument(..., help="要润色的文案"),
    style: str = typer.Option("", "--style", "-s", help="风格提示，如：更激昂 / 更平静"),
):
    """AI 文案润色 — 优化文案适合 TTS"""
    from core.llm_client import polish_script, check_status

    status = check_status()
    if not status["available"]:
        console.print("[red]FreeLLMAPI 未连接[/red]")
        console.print("[dim]安装: curl -fsSL https://freellmapi.co/install.sh | bash[/dim]")
        raise typer.Exit(1)

    console.print(f"[cyan]润色中...[/cyan]")
    try:
        result = polish_script(text, style)
        console.print()
        console.print(result)
        console.print()
        console.print(f"[green]润色完成，{len(result)} 字[/green]")
    except Exception as e:
        console.print(f"[red]润色失败: {e}[/red]")
        raise typer.Exit(1)
