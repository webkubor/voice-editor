import typer
from cli.commands.voice import app as voice_app
from cli.commands.tts import tts_clone, tts_design
from cli.commands.job import app as job_app
from cli.commands.preset import app as preset_app

app = typer.Typer(
    name="voice",
    help="[bold cyan]声音编辑器[/bold cyan] — 面向人类、AI 与 agent 的本地语音工作台",
    add_completion=False,
)
app.add_typer(voice_app, name="voice")
app.add_typer(job_app, name="job")
app.add_typer(preset_app, name="preset")
app.command("clone")(tts_clone)
app.command("design")(tts_design)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    voice — 声音编辑器

    子命令组：
      voice      音色素材管理（list / add / preview / show / rm / import）
      clone      从已有音色克隆合成
      design     从文字描述设计新音色
      preset     预设管理（list / show / run / batch）
      job        任务历史（list / show / clean）
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
