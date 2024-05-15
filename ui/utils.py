# Packages
import os
import random

# Textual packages
from rich.console import RenderableType
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Grid
from textual.screen import Screen, ModalScreen
from textual.widgets import Static, Switch, Button, Label

# The cool ascii art logo
LOGO_L1 = " ██████╗ █████╗██╗   ██╗███████╗██████╗ ███╗   ██╗ █████╗\n"
LOGO_L2 = "██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗████╗  ██║██╔══██╗\n"
LOGO_L3 = "██║     ███████║██║   ██║█████╗  ██████╔╝██╔██╗ ██║███████║\n"
LOGO_L4 = "██║     ██╔══██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██║╚██╗██║██╔══██║\n"
LOGO_L5 = "╚██████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║██║ ╚████║██║  ██║\n"
LOGO_L6 = " ╚═════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝"
LOGO_ASCII = LOGO_L1 + LOGO_L2 + LOGO_L3 + LOGO_L4 + LOGO_L5 + LOGO_L6

# The quirky logo subtitle
SUB_LIST = ['Powered by argon2', 'No place like 127.0.0.1', '100% FOSS', 'Better than LastPass',
            '746865616E7377657269733432',
            'No XZ Utils utilized', 'These messages are random', ':(){ :|:& };:']
LOGO_SUB = "\n" + random.choice(SUB_LIST)

# Version
VERSION = 'v0.7a'
VERSION_LONG = f"~ CAVERNA | {VERSION} | 2024.14.5 | iulian(iulian@firemail.cc) ~"

# Sidebar message
SBMESSAGE = """

 Iulian Ionel Bocșe\n (iulian@firemail.cc)
 \n Spiru Haret Univiversity,
 Bucharest - RO

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
        return f"[b]{VERSION}"


########################################################################################################################
class QuitScreen(ModalScreen):
    def __init__(self, user: str):
        self.user = user
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit?\nAny unsaved progress will be lost", id="question"),
            Button(".Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            try:
                os.remove(f"caves/{self.user}.cvrn")
            except Exception as e:
                print(f"[QuitScreen(user)] Exception in deleting user database on exit: {e}")
            self.app.exit(0)
        else:
            self.app.pop_screen()
