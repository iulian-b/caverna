from __future__ import annotations

import sys

# Libs

# Caverna
import utils.db_tools as db_tools
import utils.pwd_tools as pwd_tools

# Textual
from rich.console import RenderableType
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import (
    Footer,
    Header,
    Input,
    RichLog,
    Static, Tree, Button,
)

from ui.utils import (
    Sidebar,
    Body,
    Section,
    SectionTitle
)


class PasswordInfo(Container):
    def compose(self) -> ComposeResult:
        yield Static("URL", classes="label")
        yield Input(placeholder="URL", type="text", id="input_url", classes="disabled", disabled=True)
        yield Static("Username", classes="label")
        yield Input(placeholder="Username", type="text", id="input_username", classes="disabled", disabled=True)
        yield Static("Password", classes="label")
        yield Input(placeholder="Password", type="text", id="input_password", classes="disabled", disabled=True)

    def set_labels(self, url, username, password) -> None:
        self.query_one("#input_url").value = url
        self.query_one("#input_username").value = username
        self.query_one("#input_password").value = password

    def disable(self) -> None:
        self.query_one("#input_url").disabled = True
        self.query_one("#input_username").disabled = True
        self.query_one("#input_password").disabled = True

    def enable(self) -> None:
        self.query_one("#input_url").disabled = False
        self.query_one("#input_username").disabled = False
        self.query_one("#input_password").disabled = False

    def unhide(self) -> None:
        self.remove_class("-hidden")

    def hide(self) -> None:
        self.add_class("-hidden")

    def _on_mount(self) -> None:
        self.disable()
        self.hide()


class PasswordButtons(Container):
    def compose(self) -> ComposeResult:
        yield Button(label="Save", variant="success")
        yield Button(label="Remove", variant="error")

    def hide(self) -> None:
        self.add_class("-hidden")

    def unhide(self) -> None:
        self.remove_class("-hidden")

    def _on_mount(self) -> None:
        self.hide()


class Vault(App[None]):
    CSS_PATH = ["../css/login.tcss", "../css/vault.tcss"]
    USERNAME = "None"
    PASSWORD = "None"
    EDITING = False

    def __init__(self, USERNAME, PASSWORD):
        if USERNAME == "None" and PASSWORD == "None":
            sys.exit("[ERROR]: Login module skipped. Aborting")
        super().__init__()

    BINDINGS = [
        Binding(key="f1", action="app.toggle_class('RichLog', '-hidden')", description="Log"),
        Binding(key="f2", action="a", description="C:UNAME"),
        Binding(key="f3", action="b", description="C:PWSD"),
        # Binding(key="ctrl+a", action="pwd_add", description="Add"),
        Binding(key="ctrl+e", action="pwd_edit", description="Edit"),
        Binding(key="f8", action="app.toggle_dark", description="Theme"),
        Binding(key="ctrl+q", action="app.quit", description="Quit"),
    ]

    def get_urls(self, tree):
        pwds = tree.root.children[0]

        conn = db_tools.db_user_connect(self.app.USERNAME, self.app.PASSWORD)
        c = conn.cursor()
        c.execute(db_tools.sql("print", ""))
        urls = c.fetchall()

        for u in urls:
            pwds.add_leaf(u[0])

        pwds.expand()
        conn.commit()
        conn.close()

    def get_paswds(self):
        conn = db_tools.db_user_connect(self.app.USERNAME, self.app.PASSWORD)
        c = conn.cursor()
        c.execute(db_tools.sql("print", ""))

    def compose(self) -> ComposeResult:
        tree: Tree[dict] = Tree(self.app.USERNAME, id="vault-tree")
        tree.root.add_leaf(label="URLs")
        self.get_urls(tree)
        tree.root.expand()
        self.app.sub_title = self.app.USERNAME

        yield Container(
            # Sidebar(classes="-hidden"),
            Header(show_clock=True),
            RichLog(classes="-hidden", wrap=False, highlight=True, markup=True),
            Body(
                tree,
                Section(
                    PasswordInfo(),
                    PasswordButtons(),
                    id="vault-body"
                ),
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Tree).focus()
        self.app.add_note(f"Welcome, {self.app.USERNAME}")
        # self.app.add_note(self.app.PASSWORD)

    def add_note(self, renderable: RenderableType) -> None:
        self.query_one(RichLog).write(renderable)

    # Used for handling http links
    def action_open_link(self, link: str) -> None:
        self.app.bell()
        import webbrowser
        webbrowser.open(link)

    def on_tree_node_selected(self) -> None:
        tree = self.app.query_one(Tree)
        pwinfo = self.app.query_one(PasswordInfo)
        pwinfobtns = self.app.query_one(PasswordButtons)
        node_label = tree.cursor_node.label
        node_id = tree.cursor_node.id - 1

        if node_id == -1:
            self.app.add_note(f"|> {self.app.USERNAME} user")
            pwinfo.hide()
            return

        if node_id == 0:
            self.app.add_note(f"|-> {self.app.USERNAME} vault")
            pwinfo.hide()
            return

        conn = db_tools.db_user_connect(self.app.USERNAME, self.app.PASSWORD)
        c = conn.cursor()
        c.execute(db_tools.sql("select", str(node_id)))
        pwd = c.fetchall()

        pwinfo.unhide()
        # selected_id = pwd[0][0]
        selected_url = pwd[0][1]
        selected_username = pwd[0][2]
        selected_password = pwd[0][3]

        conn.commit()
        conn.close()

        self.app.add_note(f"|--> {node_label}")
        pwinfo.set_labels(selected_url, selected_username, selected_password)

    def action_pwd_edit(self) -> None:
        tree = self.app.query_one(Tree)
        pwinfo = self.app.query_one(PasswordInfo)
        pwinfobtns = self.app.query_one(PasswordButtons)
        node_id = tree.cursor_node.id - 1

        if node_id < 1:
            self.app.EDITING = False
            pwinfobtns.hide()
            pwinfo.disable()
            return

        if self.app.EDITING:
            self.app.add_note("Exited edit mode")
            pwinfo.disable()
            pwinfobtns.hide()
            self.app.sub_title = self.app.USERNAME
            self.app.EDITING = False
        else:
            self.app.add_note("Editing password")
            pwinfo.enable()
            pwinfobtns.unhide()
            self.app.sub_title = f"{self.app.USERNAME}: Editing"
            self.app.EDITING = True

    def action_pwd_add(self) -> None:
        self.app.add_note("Adding password")
        URL = ""
        USERNAME = ""

        pwds = self.app.query_one(Tree).root.children[0]
        args = ["testurlll", "testus", pwd_tools.pwd_gen(20)]

        conn = db_tools.db_user_connect(self.app.USERNAME, self.app.PASSWORD)
        c = conn.cursor()
        c.execute(db_tools.sql("insert", args))

        conn.commit()
        conn.close()

        pwds.add_leaf(label=URL)
