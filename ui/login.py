# Forgot why i needed this. 2BR in next version
from __future__ import annotations

# Packages
import argon2

# Textual Pakcages
from rich.console import RenderableType
from rich.text import Text
from textual import events, on
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

# Caverna Packages
from utils import db_tools as db_tools
from utils.ui_utils import (
    Sidebar,
    Body,
    Section,
    SectionTitle,
    LOGO_ASCII,
    LOGO_SUB
)

# Used for markdown text
from_markup = Text.from_markup

# Flags
DEBUG = False
LOGGED_IN = False


########################################################################################################################
class LoginForm(Container):
    input_uname = Input(placeholder="Username", classes="Input", id="input_username")
    input_paswd = Input(placeholder="Master Password", classes="Input", password=True, id="input_password")
    input_secret = Input(placeholder="Secret", classes="Input", password=True, id="input_secret")

    def compose(self, input_uname=input_uname, input_paswd=input_paswd, input_secret=input_secret) -> ComposeResult:
        yield Static("Username", classes="label")
        yield input_uname
        yield Static("Password", classes="label")
        yield input_paswd
        yield Static("Secret", classes="label")
        yield input_secret
        yield Static()
        yield Button("Login", variant="primary", id="btn_login")

    def _on_mount(self, event: events.Mount) -> None:
        self.query_one("#input_username").clear()
        self.query_one("#input_password").clear()
        self.query_one("#input_secret").clear()
        self.query_one("#input_username").focus()

    @on(Button.Pressed, "#btn_login")
    def login_pressed(self, event: Button.Pressed) -> None:

        # Get the inputted username and master password
        username = self.input_uname.value
        password = self.input_paswd.value
        secret = self.input_secret.value

        # If all Input fields are filled
        if len(username) > 0 and len(password) > 0 and len(secret) > 0:
            try:
                # Get the user's hash from the _users database
                ph = argon2.PasswordHasher()
                control_hash = db_tools.db_user_get_hash(username)

                a = str(password + secret)
                # Verify the inputted password against the hash
                ph.verify(control_hash, a)

                # Verify the inputted secret
                if db_tools.db_user_check_secret(username, secret):
                    # Return the username, master password hash and secret
                    self.app.exit([username, str(db_tools.db_user_get_hash(username)), secret])

            # Argon2 hash mismatch (invalid password)
            except argon2.exceptions.VerifyMismatchError:
                self.input_uname.add_class("-invalid")
                self.input_paswd.add_class("-invalid")
                self.input_secret.add_class("-invalid")
                self.notify("🚫 Incorrect credentials", title="ERROR", severity="error", timeout=3)
                self.app.add_note("[LOGIN]: 🚫 FAILED (incorrect credentials)")

            # Type error (invalid username)
            except TypeError:
                self.input_uname.add_class("-invalid")
                self.input_paswd.add_class("-invalid")
                self.input_secret.add_class("-invalid")
                self.notify("🚫 Incorrect credentials", title="ERROR", severity="error", timeout=3)
                self.app.add_note("[LOGIN]: 🚫 FAILED (incorrect credentials)")


########################################################################################################################
class Login(App[list]):
    CSS_PATH = "../css/login.tcss"
    TITLE = "CAVERNA"
    SUB_TITLE = "Login"
    BINDINGS = [
        ("f1", "app.toggle_class('RichLog', '-hidden')", "❗ Log"),
        ("f5", "toggle_sidebar", "🌐 About"),
        ("f9", "app.toggle_dark", "🎨 Theme"),
        Binding("ctrl+q", "app.quit", "⛔ Exit", show=True),
    ]
    show_sidebar = reactive(False)

    def compose(self) -> ComposeResult:
        yield Container(
            Sidebar(classes="-hidden"),
            Header(show_clock=True),
            RichLog(classes="-hidden", wrap=True, highlight=True, markup=True),
            Body(
                Section(
                    SectionTitle(LOGO_ASCII + LOGO_SUB),
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
