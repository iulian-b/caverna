from __future__ import annotations

import hashlib
import sys
from importlib.metadata import version
from pathlib import Path

import argon2
from rich import box
from rich.console import RenderableType
from rich.json import JSON
from rich.markdown import Markdown
from rich.markup import escape
from rich.pretty import Pretty
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

import db_tools
import pwd_tools
from textual import events

from textual.app import App, ComposeResult, on
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.css.query import NoMatches
from textual.reactive import reactive, Reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    RichLog,
    Static,
    Switch,
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


class Body(ScrollableContainer):
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


# class Welcome(Container):
#     def compose(self) -> ComposeResult:
#         yield Static(Markdown(CSS_MD))
#         yield Button("LOGIN", variant="success")
#
#     def on_button_pressed(self, event: Button.Pressed) -> None:
#         #self.app.add_note("[b magenta]Start!")
#         self.app.query_one(".location-first").scroll_visible(duration=0.5, top=True)


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


class TextContent(Static):
    pass


class QuickAccess(Container):
    pass


class LocationLink(Static):
    def __init__(self, label: str, reveal: str) -> None:
        super().__init__(label)
        self.reveal = reveal

    def on_click(self) -> None:
        self.app.query_one(self.reveal).scroll_visible(top=False, duration=0.5)
        self.app.add_note(f"Scrolling to [b]{self.reveal}[/b]")


class LoginForm(Container):
    input_uname = Input(placeholder="Username", classes="Input", name="input_username")

    def compose(self, input_uname=input_uname) -> ComposeResult:
        yield Static("Username", classes="label")
        yield input_uname
        yield Static("Password", classes="label")
        yield Input(placeholder="Master Password", classes="Input", password=True, name="input_password")
        yield Static()
        yield Button("Login", variant="primary")


class Window(Container):
    pass


class SubTitle(Static):
    pass


class Caverna(App[None]):
    CSS_PATH = "interface.tcss"
    TITLE = "Caverna"
    BINDINGS = [
        ("f1", "app.toggle_class('RichLog', '-hidden')", "Log"),
        ("ctrl+t", "app.toggle_dark", "Theme"),
        # ("ctrl+s", "app.screenshot()", "Screenshot"),
        ("ctrl+b", "toggle_sidebar", "About"),
        Binding("ctrl+q", "app.quit", "Quit", show=True),
    ]

    show_sidebar = reactive(False)

    def add_note(self, renderable: RenderableType) -> None:
        self.query_one(RichLog).write(renderable)

    def compose(self) -> ComposeResult:
        # example_css = Path(self.css_path[0]).read_text()
        yield Container(
            Sidebar(classes="-hidden"),
            Header(show_clock=True),
            RichLog(classes="-hidden", wrap=False, highlight=True, markup=True),
            Body(
                # QuickAccess(
                #     LocationLink("TOP", ".location-top"),
                #     LocationLink("Widgets", ".location-widgets"),
                #     LocationLink("Rich content", ".location-rich"),
                #     LocationLink("CSS", ".location-css"),
                # ),
                # AboveFold(Welcome(), classes="location-top"),
                Column(
                    Section(
                        SectionTitle(LOGO_ASCII),
                        # TextContent(Markdown(WIDGETS_MD)),
                        LoginForm(),
                        # DataTable(),
                    ),
                    classes="location-widgets location-first",
                ),
                # Column(
                #     Section(
                #         SectionTitle("Rich"),
                #         TextContent(Markdown(RICH_MD)),
                #         SubTitle("Pretty Printed data (try resizing the terminal)"),
                #         Static(Pretty(DATA, indent_guides=True), classes="pretty pad"),
                #         SubTitle("JSON"),
                #         Window(Static(JSON(JSON_EXAMPLE), expand=True), classes="pad"),
                #         SubTitle("Tables"),
                #         Static(example_table, classes="table pad"),
                #     ),
                #     classes="location-rich",
                # ),
                # Column(
                #     Section(
                #         SectionTitle("CSS"),
                #         TextContent(Markdown(CSS_MD)),
                #         Window(
                #             Static(
                #                 Syntax(
                #                     example_css,
                #                     "css",
                #                     theme="material",
                #                     line_numbers=True,
                #                 ),
                #                 expand=True,
                #             )
                #         ),
                #     ),
                #     classes="location-css",
                # ),
            ),
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

    @on(Button.Pressed)
    @on(Input.Submitted)
    def login_user(self):
        input_uname = ""
        input_paswd = ""
        DEBUG = True

        for inp in self.query("Input").results(Input):
            if inp.name == "input_username":
                input_uname = str(inp.value)
                self.app.add_note(f"USERNAME: [b]{inp.value}[/b]")
            if inp.name == "input_password":
                self.app.add_note(f"PASSWORD: [b]{inp.value}[/b]")
                input_paswd = str(inp.value)

            self.app.add_note(f"U: [b]{len(input_uname)}[/b]")
            self.app.add_note(f"P: [b]{len(input_paswd)}[/b]")
            if len(input_uname) > 0 and len(input_paswd) > 0:
                try:
                    # generate hash
                    ph = argon2.PasswordHasher()
                    usr_salt = db_tools.db_user_get_salt(input_uname)
                    usr_salt = pwd_tools.pwd_b64decode(usr_salt)
                    usr_hash = ph.hash(password=input_paswd, salt=usr_salt)

                    try:
                        ph.verify(usr_hash, input_paswd)
                        self.app.add_note("GOOD")
                    except:
                        self.app.add_note("BAD")

                    # connect to db
                    conn = db_tools.db_user_connect(input_uname, usr_hash)
                    c = conn.cursor()
                    self.app.add_note("Printing db: ")

                    out = c.execute(db_tools.sql("print_pwds"))
                    record = c.fetchall()

                    self.app.add_note("Fetched")
                    for i in range(len(record)):
                        entry = record[i]
                        for j in range(len(entry)):
                            titles = ["ID: ", "URL: ", "UNAME: ", "PASWD: "]
                            self.app.add_note(f"{str(titles[j]) + str(entry[j])}")
                except:
                    for inv in self.query("Input").results(Input):
                        inv.add_class("-invalid")
                    self.app.add_note("Login Failed")

            #     except:
            #         self.app.add_note("Failure to connect")
            # # else:
            #     self.app.add_note(":(")

            #
            # mpwd_input = "spiruharet123!".encode()
            # twofa = "dee boo dah".encode()
            # mpwd_hash = hashlib.sha256(mpwd_input + twofa).hexdigest()
            #
            # conn = db_tools.db_connect()
            # cursor = conn.cursor()
            #
            # cursor.execute(db_tools.sql("print"))
            # record = cursor.fetchall()
            #

    # def action_screenshot(self, filename: str | None = None, path: str = "./") -> None:
    #     """Save an SVG "screenshot". This action will save an SVG file containing the current contents of the screen.
    #
    #     Args:
    #         filename: Filename of screenshot, or None to auto-generate.
    #         path: Path to directory.
    #     """
    #     self.bell()
    #     path = self.save_screenshot(filename, path)
    #     message = f"Screenshot saved to [bold green]'{escape(str(path))}'[/]"
    #     self.add_note(Text.from_markup(message))
    #     self.notify(message)


app = Caverna()
if __name__ == "__main__":
    app.run()
