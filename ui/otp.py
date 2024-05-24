# Packages
import pyotp
import pyperclip
from datetime import datetime
from rich.console import RenderableType
from textual import work, on

# Textual
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer, Container, Grid
from textual.css.query import NoMatches
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Footer, Header, Static, RichLog, Digits, ProgressBar, Input
from textual.timer import Timer

# CAVERNA
import utils.db_tools as db_tools


class AddOTP(ModalScreen):
    ISSUER = None
    SECRET = None

    def compose(self) -> ComposeResult:
        yield Container(
            Input(placeholder="Issuer", classes="new_otp", id="input_issuer"),
            Input(placeholder="base64 Secret", classes="new_otp", id="input_secret"),
            id="new_input",
        )
        yield Grid(
            Button("Add", variant="success", id="add"),
            Button("Cancel", variant="primary", id="cancel"),
            id="new_btns",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            self.ISSUER = self.query_one("#input_issuer").value
            self.SECRET = self.query_one("#input_secret").value
            self.dismiss([self.ISSUER, self.SECRET])
        else:
            self.dismiss(["", ""])


class Issuer(Static):
    issuer = ""
    totp = None

    def __init__(self, issuer, secret):
        self.issuer = str(issuer)
        self.totp = pyotp.TOTP(str(secret))
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(renderable=self.issuer, id="issuer_label")
        yield Container(
            Button("📋 Copy", id="btn_copy", variant="success"),
            Button("✖  Remove", id="btn_remove", variant="error"),
            Digits("", classes="-hidden"),
            Static("• • • • • •", id="totp_hidden"),
        )

    def show_code(self) -> None:
        mask = self.query_one("#totp_hidden")
        code = self.query_one(Digits)

        if code.has_class("-hidden"):
            code.remove_class("-hidden")
            mask.add_class("-hidden")
        else:
            code.add_class("-hidden")
            mask.remove_class("-hidden")

    def update_code(self) -> None:
        self.query_one(Digits).update(str(self.totp.now()[:-3]) + " " + str(self.totp.now()[3:]))

    @on(Button.Pressed, "#btn_copy")
    def copy_pressed(self, event: Button.Pressed) -> None:
        self.update_code()
        self.show_code()
        pyperclip.copy(self.totp.now())
        self.app.add_note("📋 Code copied to clipboard")

    @on(Button.Pressed, "#btn_remove")
    def remove_pressed(self, event: Button.Pressed) -> None:
        root = self.app.query_one(OTP)
        try:
            if root.DEBUG: root.add_note(f"[Issuer]on_button_pressed(self, event: Button.Pressed): sent query {db_tools.sql_otp('delete', (self.issuer, self.totp.secret))}")
            root.VAULT_DB.execute(db_tools.sql_otp("delete", (self.issuer, self.totp.secret)))
            root.VAULT_CONN.commit()
        except Exception as e:
            self.app.add_note(f"[ERROR]❗failed to remove entry: {e}")

        root.clear_issuers()
        if root.DEBUG: root.add_note("[Issuer]on_button_pressed(self, event: Button.Pressed): cleared issuers")
        root.refresh_issuers()
        if root.DEBUG: root.add_note("[Issuer]on_button_pressed(self, event: Button.Pressed): refreshed issuers")


class OTP(Screen):
    # Authentication info
    USERNAME = None
    PASSWORD = None
    SECRET = None

    # Flags
    DEBUG = True

    # Vault Database
    VAULT_CONN = None
    VAULT_DB = None

    # Title
    TITLE = "CAVERNA"
    SUB_TITLE = "OTP"

    # CSS
    CSS_PATH = "..\css\otp.tcss"

    # Bindings
    BINDINGS = [
        ("f1", "app.toggle_class('RichLog', '-hidden')", "❗Log"),
        ("f2", "add_issuer", "🆕 Add Issuer"),
        ("ctrl+q", "back", "🔙 Back"),
        # Prevent Force Close
        Binding(key="ctrl+c", action="", show=False, priority=True),
    ]

    # Timer
    progress_timer: Timer

    # Issuers
    ISSUERS = []

    def __init__(self, USERNAME, PASSWORD, SECRET, DEBUG):
        self.DEBUG = DEBUG
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.SECRET = SECRET
        self.VAULT_CONN = db_tools.db_user_connect(USERNAME, SECRET, PASSWORD)
        self.VAULT_DB = self.VAULT_CONN.cursor()

        super().__init__()

    def action_back(self) -> None:
        self.VAULT_CONN.close()
        self.app.title = "CAVERNA"
        self.app.sub_title = "Menu"
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header()
        yield Footer()
        yield ProgressBar(total=60, show_percentage=False, show_eta=False)
        yield ScrollableContainer(id="otp_container")
        yield RichLog(classes="-hidden", wrap=True, highlight=True, markup=True)

    def add_note(self, renderable: RenderableType) -> None:
        self.query_one(RichLog).write(renderable)

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def refresh_issuers(self) -> None:
        try:
            self.VAULT_DB.execute(db_tools.sql_otp("print", ""))
            res = self.VAULT_DB.fetchall()
            self.VAULT_CONN.commit()

            issuers = self.app.query_one("#otp_container")
            self.app.ISSUERS = res
            for r in res:
                new = Issuer(r[0], r[1])
                issuers.mount(new)
        except Exception as e:
            self.app.add_note(f"[ERROR] failed to add entry: {e}")

        # Close connection to DB
        self.VAULT_CONN.close()
        if self.app.DEBUG: self.app.add_note(f"[OTP].refresh_issuers(self): Closed connection to database")

        # Resplit database
        if self.app.DEBUG: self.app.add_note(f"[OTP].refresh_issuers(self): Re-split database")
        db_tools.db_user_resplit(self.USERNAME, self.SECRET)

        # Re-connect to new database
        db_tools.db_user_join_splits(self.app.USERNAME, self.app.SECRET)
        self.VAULT_CONN = db_tools.db_user_connect(self.app.USERNAME, self.app.SECRET, self.app.PASSWORD)
        self.VAULT_DB = self.VAULT_CONN.cursor()
        self.app.add_note("✅ Saved changes to vault")

    def on_mount(self) -> None:
        self.app.add_note(f"🔑 Entered {self.app.USERNAME}'s OTP Vault")

        # Get current seconds
        now = int(datetime.now().strftime('%S'))
        if self.app.DEBUG: self.app.add_note(f"[OTP].on_ready: current time is {now} seconds")

        # DEPRECATED
        # I TRIED 20 DIFFERENT SYSTEMS TO CONVERT SECONDS TO PERCENTAGE TO HALFSECONDS TO PERCENTAGE TO MY GAWD
        # Convert from 0-60 to 0-30 on a 0-100 progress bar
        # now = ((now / 2) * 100) / 30
        # now /= 2
        # if now < 0:
        #     if self.app.DEBUG: self.app.add_note(f"[OTP].on_ready: converted time from base 60 to 30 -> {now}")
        #     now *= -1
        # if self.app.DEBUG: self.app.add_note(f"[OTP].on_ready: converted time to progress -> {now}")

        # Set progress
        self.progress_timer = self.set_interval(1, self.make_progress, pause=False)
        self.query_one(ProgressBar).update(progress=float(now))
        if self.app.DEBUG: self.app.add_note(f"[OTP].on_ready: set progress bar")

        # Add issuers
        self.refresh_issuers()

    def clear_issuers(self) -> None:
        node = self.query_one("#otp_container")
        try:
            while(1):
                c = node.get_child_by_type(Issuer)
                c.remove()
        except NoMatches:
            return

    def make_progress(self) -> None:
        bar = self.query_one(ProgressBar)
        bar.advance(2)

        # Check if completed
        if bar.progress >= 60.0:
            if self.app.DEBUG: self.app.add_note("[OTP].make_progress: completed progress")

            # Reset progress
            bar.progress = 0.0
            if self.app.DEBUG: self.app.add_note("[OTP].make_progress: reset progress to 0%")

            # Update TOTP code
            if len(self.ISSUERS) >= 1:
                code = self.query_one(Issuer)
                code.update_code()
                if self.app.DEBUG: self.app.add_note("[OTP].make_progress: updated totp code")

    @work
    async def action_add_issuer(self) -> None:
        # Wait for iser input
        res = await self.app.push_screen_wait(AddOTP())
        if res[0] == "" or res[1] == "": return
        if len(res[1]) % 4 != 0:
            self.app.add_note(f"[ERROR] ❗ Error in adding issuer: incorrect secret length")
            return

        issuer = res[0]
        secret = res[1]

        # Add new entry to user database
        try:
            self.VAULT_DB.execute(db_tools.sql_otp("insert_new", (issuer, secret)))
            self.VAULT_CONN.commit()
            if self.app.DEBUG: self.app.add_note(
                f"[OTP].action_add_issuer(self): sent query {db_tools.sql_otp('insert_new', (issuer, secret))}")
        except Exception as e:
            self.app.add_note(f"[ERROR] ❗ Error in adding issuer: {e}")

        # Add new entry to interface
        new = Issuer(issuer, secret)
        await self.app.query_one("#otp_container").mount(new)
        self.app.refresh()

    # BTM5DBJYSVPPP4MU
