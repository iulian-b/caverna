# Textual packages
from rich.console import RenderableType
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Switch

# The cool ascii art logo
LOGO_L1 = " ██████╗ █████╗ ██╗   ██╗███████╗██████╗ ███╗   ██╗ █████╗\n"
LOGO_L2 = "██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗████╗  ██║██╔══██╗\n"
LOGO_L3 = "██║     ███████║██║   ██║█████╗  ██████╔╝██╔██╗ ██║███████║\n"
LOGO_L4 = "██║     ██╔══██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██║╚██╗██║██╔══██║\n"
LOGO_L5 = "╚██████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║██║ ╚████║██║  ██║\n"
LOGO_L6 = " ╚═════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝"
LOGO_ASCII = LOGO_L1 + LOGO_L2 + LOGO_L3 + LOGO_L4 + LOGO_L5 + LOGO_L6

# Version
VERSION = 'Caverna - 0.1b - 2024.13.3 - iulian(iulian@firemail.cc)'

# Sidebar message
SBMESSAGE = """

Iulian Ionel Bocșe\n(iulian@firemail.cc)

- [@click="app.open_link('https://github.com/iulian-b/caverna')"]GitHub Repo[/]

"""


########################################################################################################################
class Body(Container):
    pass


########################################################################################################################
class Title(Static):
    pass


########################################################################################################################
class OptionGroup(Container):
    pass


########################################################################################################################
class AboveFold(Container):
    pass


########################################################################################################################
class Section(Container):
    pass


########################################################################################################################
class Column(Container):
    pass


########################################################################################################################
class SectionTitle(Static):
    pass


########################################################################################################################
class Message(Static):
    pass


########################################################################################################################
class Window(Container):
    pass


########################################################################################################################
class SubTitle(Static):
    pass


########################################################################################################################
class Sidebar(Container):
    def compose(self) -> ComposeResult:
        yield Title("Caverna")
        yield OptionGroup(Message(SBMESSAGE), Version())
        yield DarkSwitch()


########################################################################################################################
class DarkSwitch(Horizontal):
    def compose(self) -> ComposeResult:
        yield Switch(value=self.app.dark)
        yield Static("Dark mode toggle", classes="label")

    def on_mount(self) -> None:
        self.watch(self.app, "dark", self.on_dark_change, init=False)

    def on_dark_change(self) -> None:
        self.query_one(Switch).value = self.app.dark

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self.app.dark = event.value


########################################################################################################################
class Version(Static):
    def render(self) -> RenderableType:
        return f"[b]v1.0"
