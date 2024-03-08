from __future__ import annotations

# Libs
import argon2

# Caverna
import db_tools
import pwd_tools

# Textual
from rich import box
from rich.console import RenderableType
from rich.table import Table
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    RichLog,
    Static,
    Switch,
    Tree, TextArea
)

from_markup = Text.from_markup

example_table = Table(
    show_edge=False,
    show_header=True,
    expand=True,
    row_styles=["none", "dim"],
    box=box.SIMPLE,
)
example_table.add_column(from_markup("[green]Date"), style="green", no_wrap=True)
example_table.add_column(from_markup("[blue]Title"), style="blue")

example_table.add_column(
    from_markup("[magenta]Box Office"),
    style="magenta",
    justify="right",
    no_wrap=True,
)
example_table.add_row(
    "Dec 20, 2019",
    "Star Wars: The Rise of Skywalker",
    "$375,126,118",
)
example_table.add_row(
    "May 25, 2018",
    from_markup("[b]Solo[/]: A Star Wars Story"),
    "$393,151,347",
)
example_table.add_row(
    "Dec 15, 2017",
    "Star Wars Ep. VIII: The Last Jedi",
    from_markup("[bold]$1,332,539,889[/bold]"),
)
example_table.add_row(
    "May 19, 1999",
    from_markup("Star Wars Ep. [b]I[/b]: [i]The phantom Menace"),
    "$1,027,044,677",
)

LOGO_L1 = "██████╗ █████╗ ██╗   ██╗███████╗██████╗ ███╗   ██╗ █████╗\n"
LOGO_L2 = "██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗████╗  ██║██╔══██╗\n"
LOGO_L3 = "██║     ███████║██║   ██║█████╗  ██████╔╝██╔██╗ ██║███████║\n"
LOGO_L4 = "██║     ██╔══██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██║╚██╗██║██╔══██║\n"
LOGO_L5 = "╚██████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║██║ ╚████║██║  ██║\n"
LOGO_L6 = " ╚═════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝"
LOGO_ASCII = LOGO_L1 + LOGO_L2 + LOGO_L3 + LOGO_L4 + LOGO_L5 + LOGO_L6

DATA = {
    "foo": [
        3.1427,
        (
            "Paul Atreides",
            "Vladimir Harkonnen",
            "Thufir Hawat",
            "Gurney Halleck",
            "Duncan Idaho",
        ),
    ],
}

MESSAGE = """

Iulian Ionel Bocșe\n(iulian@firemail.cc)

- [@click="app.open_link('https://github.com/iulian-b/caverna')"]GitHub Repo[/]

"""

DEBUG = False
LOGGED_IN = False


class Body(Container):
    pass


class Title(Static):
    pass


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


class OptionGroup(Container):
    pass


class SectionTitle(Static):
    pass


class Message(Static):
    pass


class Version(Static):
    def render(self) -> RenderableType:
        return f"[b]v1.0"


class Sidebar(Container):
    def compose(self) -> ComposeResult:
        yield Title("Caverna")
        yield OptionGroup(Message(MESSAGE), Version())
        yield DarkSwitch()


class AboveFold(Container):
    pass


class Section(Container):
    pass


class Column(Container):
    pass


class LoginForm(Container):
    input_uname = Input(placeholder="Username", classes="Input", id="input_username")
    input_paswd = Input(placeholder="Master Password", classes="Input", password=True, id="input_password")
    who = reactive("test")

    def compose(self, input_uname=input_uname, input_paswd=input_paswd) -> ComposeResult:
        yield Static("Username", classes="label")
        yield input_uname
        yield Static("Password", classes="label")
        yield input_paswd
        yield Static()
        yield Button("Login", variant="primary")

    def _on_mount(self, event: events.Mount) -> None:
        self.query_one("#input_username").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        username = self.input_uname.value
        password = self.input_paswd.value

        if len(username) > 0 and len(password) > 0:
            try:
                ph = argon2.PasswordHasher()
                # Retrieve Salt
                salt = db_tools.db_user_get_salt(username)
                # Decode Salt
                salt = pwd_tools.pwd_b64decode(salt)
                # Generate Hash with retrieved salt
                user_hash = ph.hash(password=password, salt=salt)

                try:
                    # Verify
                    ph.verify(user_hash, password)
                    self.app.add_note("Logged in")
                except Exception as e:
                    self.app.add_note("Login failed")
                    self.app.add_note(e)

                login_panel = self.parent.parent.parent.query_one("#login-panel")
                app_container = login_panel.parent
                vault = Vault()
                login_panel.remove()
                app_container.mount(vault)

                self.app.sub_title = username
                self.app.USERNAME = username
                self.app.PASSWORD = user_hash

            except Exception as e:
                self.input_uname.add_class("-invalid")
                self.input_paswd.add_class("-invalid")
                self.app.add_note("Login Failed")
                self.app.add_note(e)


class Window(Container):
    pass


class SubTitle(Static):
    pass


class PasswordInfo(Container):
    def compose(self) -> ComposeResult:
        yield Static("URL", classes="label")
        yield Input(placeholder="One", type="text", id="input_url", classes="disabled", disabled=True)
        yield Static("Username", classes="label")
        yield Input(placeholder="One", type="text", id="input_username", classes="disabled", disabled=True)
        yield Static("Password", classes="label")
        yield Input(placeholder="One", type="text", id="input_password", classes="disabled", disabled=True)

    def _on_mount(self):
        index = 0
        username = self.app.USERNAME
        password = self.app.PASSWORD
        input_url = self.query_one("#input_url")
        input_unm = self.query_one("#input_username")
        input_pwd = self.query_one("#input_password")

        # self.app.add_note(input_url)

        conn = db_tools.db_user_connect(username, password)
        c = conn.cursor()
        c.execute(db_tools.sql("print", ""))
        pwds = c.fetchall()

        pw = pwds[index]

        # self.app.add_note(f"url: {pw[0]}")
        # self.app.add_note(f"uname: {pw[1]}")
        # self.app.add_note(f"pwd: {pw[2]}")

        input_url.placeholder = pw[0]
        input_unm.placeholder = pw[1]
        input_pwd.placeholder = pw[2]
        # yield Container(
        #     Container(
        #         Static("Password", classes="vault-title"),
        #         Input(placeholder="Two", type="text", id="input2", disabled=True)
        #     ),
        # )


class Login(App[list]):
    CSS_PATH = [("css/login.tcss"), ("css/vault.tcss")]
    TITLE = "Caverna"
    BINDINGS = [
        ("f1", "app.toggle_class('RichLog', '-hidden')", "Log"),
        ("ctrl+t", "app.toggle_dark", "Theme"),
        ("ctrl+b", "toggle_sidebar", "Help"),
        # Binding("ctrl+q", "app.quit", "Quit", show=True),
    ]
    show_sidebar = reactive(False)
    PASSWORD = ""
    USERNAME = ""

    def add_note(self, renderable: RenderableType) -> None:
        self.query_one(RichLog).write(renderable)

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

    def action_open_link(self, link: str) -> None:
        self.app.bell()
        import webbrowser
        webbrowser.open(link)

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

        self.exit(["dasda","asdasad"])


class Vault(Static):
    BINDINGS = [
        # Binding(key="f2", action="help", description="Clip"),
        Binding(key="ctrl+a", action="pwd_add", description="Add"),
        Binding(key="ctrl+e", action="pwd_edit", description="Edit"),
        Binding(key="ctrl+r", action="help2", description="Remove"),
    ]

    def get_urls(self, tree):
        pwds = tree.root.children[0]

        conn = db_tools.db_user_connect(self.app.USERNAME, self.app.PASSWORD)
        c = conn.cursor()
        c.execute(db_tools.sql("print", ""))
        urls = c.fetchall()

        for u in urls:
            # self.app.add_note(u)
            pwds.add_leaf(u[0])

        pwds.expand()
        conn.commit()
        conn.close()

    def compose(self) -> ComposeResult:
        tree: Tree[dict] = Tree(self.app.USERNAME, id="vault-tree")
        tree.root.add_leaf(label="URLs")
        self.get_urls(tree)
        tree.root.expand()

        yield Container(
            tree,
            Container(
                PasswordInfo(),
                id="vault-body"
            ),
        )

    def on_mount(self) -> None:
        self.query_one(Tree).focus()

    def action_pwd_edit(self) -> None:
        self.app.add_note("Editing password")

        input_url = self.query_one("#input_url")
        input_unm = self.query_one("#input_username")
        input_pwd = self.query_one("#input_password")

        if input_url.disabled:
            input_url.disabled = False
            input_unm.disabled = False
            input_pwd.disabled = False
        else:
            input_url.disabled = True
            input_unm.disabled = True
            input_pwd.disabled = True

    def action_pwd_add(self) -> None:
        self.app.add_note("Adding password")
        args = ["testurlll", "testus", pwd_tools.pwd_gen(20)]

        conn = db_tools.db_user_connect(app.USERNAME, app.PASSWORD)
        c = conn.cursor()
        c.execute(db_tools.sql("insert", args))

        conn.commit()
        conn.close()


if __name__ == "__main__":
    app = Login()

    r = app.run()
    print(r)