# Packages
import sys
import atexit
import os

# Textual Pakcages
from rich.console import RenderableType
from textual import events, on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    RichLog,
)

# Caverna
from ui.utils import (
    Sidebar,
    Body,
    Section,
    SectionTitle,
    LOGO_ASCII,
    QuitScreen
)
import ui.vault


########################################################################################################################
class MenuForm(Container):
    btn_vault = Button(label="🔑 Vault", variant="primary", disabled=False, id="btn_vault")
    btn_mail = Button(label="📧 E-mail", variant="success", disabled=True, id="btn_mail")
    btn_notes = Button(label="📝 Notes", variant="warning", disabled=True, id="btn_notes")
    btn_settings = Button(label="⚙  Settings", variant="default", disabled=True, id="btn_settings")

    def compose(self, btn_vault=btn_vault, btn_mail=btn_mail, btn_notes=btn_notes,
                btn_settings=btn_settings) -> ComposeResult:
        yield Horizontal(
            btn_vault,
            btn_mail,
        )
        yield Horizontal(
            btn_notes,
            btn_settings,
        )

    def _on_mount(self, event: events.Mount) -> None:
        self.btn_vault.disabled = False

    @on(Button.Pressed, "#btn_vault")
    def vault_pressed(self, event: Button.Pressed) -> None:
        if self.app.DEBUG: self.app.add_note(f"[MenuForm]@Button.Pressed(#btn_vault): Pressed vault button")
        # self.btn_vault.disabled = False
        # self.app.exit(1)
        # self.push_screen(ui.Vault(self.app.USERNAME, self.app.PASSWORD, self.app.SECRET, self.app.DEBUG))
        self.app.push_screen(ui.vault.Vault(self.app.USERNAME, self.app.PASSWORD, self.app.SECRET, self.app.DEBUG))
        # self.app.install_screen(ui.vault.Vault(self.app.USERNAME, self.app.PASSWORD, self.app.SECRET, self.app.DEBUG), name='vault')


########################################################################################################################
class Menu(App[list]):
    CSS_PATH = "../css/menu.tcss"
    TITLE = "Caverna - Menu"
    USERNAME = "None"
    PASSWORD = "None"
    SECRET = ""
    DEBUG = False
    BINDINGS = [
        ("f1", "app.toggle_class('RichLog', '-hidden')", "❗Log"),
        ("f8", "app.toggle_dark", "📺 Theme"),
        ("f9", "toggle_sidebar", "🌐 About"),
        ("ctrl+q", "exit", "⛔ Exit"),
    ]
    show_sidebar = reactive(False)

    def __init__(self, USERNAME, PASSWORD, SECRET, DEBUG):
        if USERNAME == "None" and PASSWORD == "None":
            sys.exit("[ERROR]: Login module skipped. Aborting")
        self.DEBUG = DEBUG
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.SECRET = SECRET
        super().__init__()

    def action_exit(self) -> None:
        self.push_screen(QuitScreen(self.app.USERNAME))

    def compose(self) -> ComposeResult:
        yield Container(
            Sidebar(classes="-hidden"),
            Header(show_clock=True),
            RichLog(classes="-hidden", wrap=False, highlight=True, markup=True),
            Body(
                Section(
                    SectionTitle(LOGO_ASCII),
                    Section(
                        MenuForm(id="menu-form"),
                        id="menu_background"
                    ),
                ),
                classes="location-widgets location-first", id="login-panel"
            ),
            id="app-container"
        )
        yield Footer()

    # Adds a note to the RichLog
    def add_note(self, renderable: RenderableType) -> None:
        self.query_one(RichLog).write(renderable)

    # Used for handling http links
    def action_open_link(self, link: str) -> None:
        self.app.bell()
        import webbrowser
        webbrowser.open(link)

    # Toggles the sidebar
    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    # On Mount
    def _on_mount(self) -> None:
        self.add_note("Logged in!")
        self.add_note(f"Welcome, {self.USERNAME}")
        if self.app.DEBUG: self.app.add_note(
            f"[Menu].__init__(self, USERNAME, PASSWORD, SECRET, DEBUG): opened menu with data: {self.app.USERNAME}, {self.app.PASSWORD}, {self.app.SECRET}, {self.app.DEBUG}")
