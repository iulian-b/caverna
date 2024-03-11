from __future__ import annotations

# Libs
import argon2

# Textual
from rich.console import RenderableType
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    RichLog,
    Static,
)

# Caverna
import utils.db_tools as db_tools
import utils.pwd_tools as pwd_tools
from ui.utils import (
    Sidebar,
    Body,
    Section,
    SectionTitle,
    LOGO_ASCII
)

from_markup = Text.from_markup

DEBUG = False
LOGGED_IN = False


class LoginForm(Container):
    input_uname = Input(placeholder="Username", classes="Input", id="input_username")
    input_paswd = Input(placeholder="Master Password", classes="Input", password=True, id="input_password")

    def compose(self, input_uname=input_uname, input_paswd=input_paswd) -> ComposeResult:
        yield Static("Username", classes="label")
        yield input_uname
        yield Static("Password", classes="label")
        yield input_paswd
        yield Static()
        yield Button("Login", variant="primary")

    def _on_mount(self, event: events.Mount) -> None:
        self.query_one("#input_username").focus()

    def on_button_pressed(self) -> None:
        username = self.input_uname.value
        password = self.input_paswd.value

        if len(username) > 0 and len(password) > 0:
            try:
                ph = argon2.PasswordHasher()
                # Retrieve control hash
                control_hash = db_tools.db_user_get_hash(username)

                # Verify
                ph.verify(control_hash, password)

                # Return
                self.app.exit([username, control_hash])

            # Argon2 hash mismatch (invalid password)
            except argon2.exceptions.VerifyMismatchError:
                self.input_uname.add_class("-invalid")
                self.input_paswd.add_class("-invalid")
                self.app.add_note("[LOGIN]: FAILED (incorrect master password)")

            # Type error (invalid username)
            except TypeError:
                self.input_uname.add_class("-invalid")
                self.input_paswd.add_class("-invalid")
                self.app.add_note("[LOGIN]: FAILED (user does not exist)")


# Reuturn Username, Password, Log
class Login(App[list]):
    CSS_PATH = "../css/login.tcss"
    TITLE = "Caverna"
    BINDINGS = [
        ("f1", "app.toggle_class('RichLog', '-hidden')", "Log"),
        ("f8", "app.toggle_dark", "Theme"),
        ("ctrl+h", "toggle_sidebar", "About"),
        Binding("ctrl+q", "app.quit", "Quit", show=True),
    ]
    show_sidebar = reactive(False)

    def compose(self) -> ComposeResult:
        yield Container(
            Sidebar(classes="-hidden"),
            Header(show_clock=True),
            RichLog(classes="-hidden", wrap=False, highlight=True, markup=True),
            Body(
                Section(
                    SectionTitle(LOGO_ASCII),
                    LoginForm(id="login-form"),
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
