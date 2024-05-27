# Packages
import pyperclip

# Textual Packages
from textual.binding import Binding
from textual.screen import Screen
from textual import events
from textual.app import ComposeResult
from textual.widgets import Label, Markdown, TabbedContent, TabPane, Footer, Header
from tempmail import EMail

EMAIL_ADDRESS = EMail()
MD_ADDRESS = f"""
# {EMAIL_ADDRESS.address}

E-mail address automatically copied to clipboard.

- [F5] refresh inbox.

- [CTRL+M1] open link.
"""


class TempMail(Screen):
    EMAILS_N = 0
    TITLE = "CAVERNA"
    SUB_TITLE = "TempMail"
    CSS = """
    RichLog {
        background: $surface;
        color: $text;
        height: 50vh;
        dock: bottom;
        layer: notes;
        border-top: hkey $primary;
        offset-y: 0;
        transition: offset 400ms in_out_cubic;
        padding: 0 1 1 1;
    }
    
    RichLog:focus {
        offset: 0 0 !important;
    }
    
    RichLog.-hidden {
        offset-y: 100%;
    }
    """

    # FIX RICHLOG
    BINDINGS = [
        Binding(key="f1", action="app.toggle_class('RichLog', '-hidden')", priority=True, show=True, description="❗Log"),
        Binding(key="f2", action="clip_address", priority=True, description="📋 Address"),
        Binding(key="f5", action="refresh", priority=True, description="🔃 Fetch"),
        Binding(key="ctrl+q", action="back", priority=True, description="🔙 Back"),
        # Prevent force close
        Binding(key="ctrl+c", action="", priority=True, show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        # NOT WORKING ATM
        # yield RichLog(classes="-hidden", wrap=True, highlight=True, markup=True)
        with TabbedContent(initial="address"):
            with TabPane(f"📧 {EMAIL_ADDRESS.address}", id="address"):
                yield Markdown(MD_ADDRESS)
                with TabbedContent("{email}", id="mails_tabs"):
                    yield TabPane("📥 Inbox |", Label("Inbox currently empty"))
        yield Footer()

    def _on_mount(self, event: events.Mount) -> None:
        pyperclip.copy(EMAIL_ADDRESS.address)
        self.notify("✅ Email Address copied to clipboard", title="SUCCESS", severity="information", timeout=3)

        self.app.sub_title = "TempMail"
        self.refresh()

    def action_back(self) -> None:
        self.app.title = "CAVERNA"
        self.app.sub_title = "Menu"
        self.app.pop_screen()

    def action_show_tab(self, tab: str) -> None:
        self.get_child_by_type(TabbedContent).active = tab

    def action_refresh(self) -> None:
        # self.app.bell()
        if self.EMAILS_N >= 1:
            self.app.sub_title = f"TempMail ({self.EMAILS_N})"

        Tabs = self.app.query_one("#mails_tabs")
        Tabs.clear_panes()

        try:
            EMAIL_ADDRESS.wait_for_message(1)
        except:
            pass

        inbox = EMAIL_ADDRESS.get_inbox()
        if len(inbox) > 0:
            Tabs.add_pane(TabPane("📥 Inbox |", Label(f"{self.EMAILS_N + 1} New Email/s")))
            for msg_info in inbox:
                self.EMAILS_N += 1
                self.add_tab(msg_info)
                self.app.bell()
        else:
            Tabs.add_pane(TabPane("📥 Inbox |", Label("Inbox currently empty")))

    def add_tab(self, mail) -> None:
        Id = mail.id
        Head = mail.subject
        From = mail.from_addr
        Date = mail.date_str
        Body = mail.message.body

        MD_MAIL = f"""
        - ID: {Id}
        - From: {From}
        - At: {Date}

        {Body}
        """

        newTab = TabPane(Head, Markdown(MD_MAIL))
        self.app.query_one("#mails_tabs").add_pane(newTab)

    def action_clip_address(self) -> None:
        pyperclip.copy(EMAIL_ADDRESS.address)
