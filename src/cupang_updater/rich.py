import rich.traceback
from rich.console import Console, Group
from rich.live import Live
from rich.status import Status

console = Console(tab_size=4)
rich.traceback.install()


def get_rich_status():
    return Status("...", console=console)


def get_rich_live(*renderable):
    return Live(Group(*renderable), console=console, transient=True)
