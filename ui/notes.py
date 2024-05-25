# Packages
import sys

# Textual
from rich.console import RenderableType
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer, Grid
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Tree,
    Header,
    RichLog,
    Footer,
    TextArea,
    Static,
    Markdown,
    Button,
    Input
)

# Caverna
from utils import db_tools as db_tools
from utils.ui_utils import Body, Section


########################################################################################################################
# AddNote(ModalScreen): Gathers the filename for a newly created       #
#                       note entry to be added to the vault.           #
########################################################################
class AddNote(ModalScreen):
    NEW_FILENAME = None

    def compose(self) -> ComposeResult:
        yield Container(
            Input(placeholder="Enter new note FILENAME", classes="new_note", id="input_filename"),
            id="new_input",
        )
        yield Grid(
            Button("Add", variant="success", id="add"),
            Button("Cancel", variant="primary", id="cancel"),
            id="new_btns",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            self.NEW_FILENAME = self.query_one("#input_filename").value
            self.dismiss(self.NEW_FILENAME)
        else:
            self.dismiss(None)


########################################################################################################################
# TextEdit(Widget): Displays the content of the notes through a        #
#                   modifiable textarea.                               #
########################################################################
class TextEdit(Container):
    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield TextArea.code_editor(language="markdown", id="content")

    # Hide/Unhide
    def spawn(self):
        self.remove_class("-hidden")
        if self.app.DEBUG: self.app.add_note(f"[TextEdit].spawn(self): spawned self")

    def despawn(self):
        self.add_class("-hidden")
        if self.app.DEBUG: self.app.add_note(f"[TextEdit].despawn(self): despawned self")

    # Set text content
    def set_content(self, content) -> None:
        self.query_one("#content").text = content

    # Get the text content
    def get_content(self) -> str:
        return self.query_one("#content").text

    def _on_mount(self) -> None:
        # self.disable()
        self.despawn()
        if self.app.DEBUG: self.app.add_note(f"[TextEdit]._on_mount(self): mounted self")


########################################################################################################################
# TextView(Widget): Displays the content of the notes through a        #
#                   markdown renderer.                                 #
########################################################################
class TextView(Container):
    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield Markdown()

    # Hide/Unhide
    def spawn(self):
        self.remove_class("-hidden")
        if self.app.DEBUG: self.app.add_note(f"[TextView].spawn(self): spawned self")

    def despawn(self):
        self.add_class("-hidden")
        if self.app.DEBUG: self.app.add_note(f"[TextView].despawn(self): despawned self")

    # Set text content
    def set_content(self, content) -> None:
        self.query_one(Markdown).update(content)

    def _on_mount(self) -> None:
        # self.disable()
        self.despawn()
        if self.app.DEBUG: self.app.add_note(f"[TextView]._on_mount(self): mounted self")


########################################################################################################################
# Notes(Screen): Main body and logic of the vault.                     #
#                Contains all of the textual widgets and classes,      #
#                Tree logic, and bindings.                             #
########################################################################
class Notes(Screen):
    # CSS
    CSS_PATH = "../css/notes.tcss"

    # Authentication info
    USERNAME = None
    PASSWORD = None
    SECRET = None

    # Network SSID
    SSID = "Net"

    # Debug
    DEBUG = False

    # Flags
    EDITING = False
    UNSAVED = False
    TITLE = "CAVERNA"
    SUB_TITLE = "Notes"
    # Notes Tree
    TREE_NOTES = []

    # Vault Database
    VAULT_CONN = None
    VAULT_DB = None

    def __init__(self, USERNAME, PASSWORD, SECRET, DEBUG):
        if USERNAME is None and PASSWORD is None:
            sys.exit("[ERROR]: Login module skipped. Aborting")
        self.DEBUG = DEBUG
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.SECRET = SECRET
        self.VAULT_CONN = db_tools.db_user_connect(USERNAME, SECRET, PASSWORD)
        self.VAULT_DB = self.VAULT_CONN.cursor()
        super().__init__()

    BINDINGS = [
        Binding(key="f1", action="app.toggle_class('RichLog', '-hidden')", description="❗ Log"),
        Binding(key="f5", action="save", priority=True, description="💾 Save"),

        Binding(key="f8", action="note_edit", description="🔄 Edit"),
        Binding(key="ctrl+a", action="note_add", description="🆕 Insert"),
        Binding(key="ctrl+r", action="note_delete", description="⛔ Delete"),
        Binding(key="ctrl+q", action="back", priority=True, description="🔙 Back"),
        # Prevent force close
        Binding(key="ctrl+c", action="", show=False, priority=True),
    ]

    def action_back(self) -> None:
        self.VAULT_CONN.close()
        self.app.title = "CAVERNA"
        self.app.sub_title = "Menu"
        self.app.pop_screen()

    def tree_initialize(self, tree) -> None:
        notes = tree.root.children[0]

        self.VAULT_DB.execute(db_tools.sql_notes("print", ""))
        res = self.VAULT_DB.fetchall()
        self.VAULT_CONN.commit()

        self.TREE_NOTES = res
        for r in res:
            notes.add_leaf(r[0])

        notes.expand()

    def tree_refresh(self) -> None:
        tree = self.query_one(Tree)
        tree.clear()
        if self.app.DEBUG: self.app.add_note(f"[Notes].tree_refresh(self): cleared tree")

        tree.root.add_leaf(label="Notes")
        self.tree_initialize(tree)
        tree.cursor_line = 1

        tree.root.expand()
        tree.disabled = False
        if self.app.DEBUG: self.app.add_note(f"[Noes].tree_refresh(self): refreshed tree")

    def compose(self) -> ComposeResult:
        tree: Tree[dict] = Tree(self.USERNAME, id="vault-tree")
        tree.root.add_leaf(label="Notes")
        self.tree_initialize(tree)
        tree.root.expand()
        self.app.TITLE = "CAVERNA - Notes"
        self.app.sub_title = self.USERNAME

        yield Container(
            Header(show_clock=True),
            RichLog(classes="-hidden", wrap=True, highlight=True, markup=True),
            Body(
                tree,
                Section(
                    Static("", id="lbl_file"),
                    TextView(),
                    TextEdit(),
                    id="vault-body"
                ),
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Tree).focus()
        self.app.add_note(f"🔑 Entered {self.app.USERNAME}'s Vault")
        self.query_one(TextEdit).despawn()

        # if self.app.DEBUG: self.app.add_note(
        #     f"[Notes].__init__(self, USERNAME, PASSWORD, DEBUG): opened vault with data: {self.USERNAME}, {self.PASSWORD}, {self.DEBUG}")
        if self.app.DEBUG: self.app.add_note(f"[Notes].compose(self): initialized tree")
        if self.app.DEBUG: self.app.add_note(f"[Notes].compose(self): finished composing")
        if self.app.DEBUG: self.app.add_note(f"[Notes].on_mount(self): hid TextEdit")

    def add_note(self, renderable: RenderableType) -> None:
        self.query_one(RichLog).write(renderable)

    def on_tree_node_selected(self) -> None:
        tree = self.query_one(Tree)
        txtEdit = self.query_one(TextEdit)
        txtView = self.query_one(TextView)
        node_label = tree.cursor_node.label
        node_id = tree.cursor_node.id - 2

        if self.app.DEBUG: self.app.add_note(f"[Notes].on_tree_node_selected(self): selected tree: {tree}")
        if self.app.DEBUG: self.app.add_note(f"[Notes].on_tree_node_selected(self): selected node: {node_label} id_{node_id + 2}")

        lbl_file = self.query_one("#lbl_file")
        lbl_file.update(f"{self.SSID}:://CAVERNA/{self.USERNAME}/notes/{node_label}")
        if self.app.DEBUG: self.app.add_note(f"[Notes].on_tree_node_selected(self): updated renderable for -> {lbl_file}")

        if node_id == -2:
            self.app.add_note(f"> {self.USERNAME}")
            txtEdit.despawn()
            txtView.despawn()
            if self.app.DEBUG: self.app.add_note(f"[Notes].on_tree_node_selected(self): despawned TextEdit")
            lbl_file.update(f"")
            if self.app.DEBUG: self.app.add_note(f"[Notes].on_tree_node_selected(self): cleared file label")
            return

        if node_id == -1:
            self.app.add_note(f"-> {self.app.USERNAME}'s notes")
            txtEdit.despawn()
            txtView.despawn()
            if self.app.DEBUG: self.app.add_note(f"[Notes].on_tree_node_selected(self): despawned TextEdit")
            lbl_file.update(f"")
            if self.app.DEBUG: self.app.add_note(f"[Notes].on_tree_node_selected(self): cleared file label")
            return

        self.app.add_note(f"--> {node_label}")
        self.VAULT_DB.execute(db_tools.sql_notes("select", node_label))
        self.VAULT_CONN.commit()
        note = self.VAULT_DB.fetchall()
        node_content = note[0]

        # First run
        if not self.EDITING:
            txtView.spawn()
            if self.app.DEBUG: self.app.add_note(f"[Notes].on_tree_node_selected(self): spawned TextView")

        txtEdit.set_content(node_content[-1])
        if self.app.DEBUG: self.app.add_note(f"[Notes].on_tree_node_selected(self): updated TextEdit")
        txtView.set_content(node_content[-1])
        if self.app.DEBUG: self.app.add_note(f"[Notes].on_tree_node_selected(self): updated TextView")

    def action_note_edit(self) -> None:
        tree = self.query_one(Tree)
        txtView = self.query_one(TextView)
        txtEdit = self.query_one(TextEdit)
        node_id = tree.cursor_node.id - 1

        # Check if cursor node is a note
        if node_id < 1:
            self.EDITING = False
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_edit(self): EDITING -> False")

            # Despawn both windows
            txtView.despawn()
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_edit(self): despawned TextView")

            txtEdit.despawn()
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_edit(self): despawned TextEdit")

            self.sub_title = self.app.USERNAME
            return

        # Enter Edit mode
        if not self.EDITING:
            self.EDITING = True
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_edit(self): EDITING -> True")

            txtView.despawn()
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_edit(self): despawned TextView")

            txtEdit.spawn()
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_edit(self): spawned TextEdit")

            tree.disabled = True
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_edit(self): disabled Tree")

            self.sub_title = f"{self.app.USERNAME}: Edit"


        # Exit edit after save
        elif self.UNSAVED:
            self.UNSAVED = False
            self.EDITING = False
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_delete(self): UNSAVED -> False")
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_delete(self): EDITING -> False")

            self.app.query_one("#lbl_file").update("")
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_delete(self): cleared filename label")

            txtEdit.despawn()
            txtView.despawn()
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_delete(self): despawned TextEdit")
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_delete(self): despawned TextView")

            self.tree_refresh()
            self.sub_title = self.app.USERNAME

        # Exit Edit mode
        else:
            self.EDITING = False
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_edit(self): EDITING -> False")

            txtEdit.despawn()
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_edit(self): despawned TextEdit")

            txtView.spawn()
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_edit(self): spawned TextView")

            tree.disabled = False
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_edit(self): enabled Tree")

            self.sub_title = self.app.USERNAME


    @work
    async def action_note_add(self) -> None:
        tree = self.query_one(Tree)

        # Wait for user input
        self.sub_title = f"{self.app.USERNAME}: Insert"
        filename = await self.app.push_screen_wait(AddNote())
        if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_add(self): @awaited filename from AddNote()")

        # If filename is void, or user cancelled interaction
        if filename is None:
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_open_link(self): filename returned None (user canceled interaction)")
            return
        # If filename is correct
        if self.app.DEBUG: self.app.add_note(f"[Notes].action_open_link(self): filename returned {filename}")

        # Add node to tree
        tree.root.children[0].add_leaf(f"{filename}")
        if self.app.DEBUG: self.app.add_note(f"[Notes].action_open_link(self): added leaf to tree")

        # Focus tree on added node
        last_index = len(self.TREE_NOTES) + 2
        tree.cursor_line = last_index

        # Insert row into database
        dummy_markdown= f"""# {filename} (New Note)"""
        try:
            self.VAULT_DB.execute(db_tools.sql_notes("insert_new", (filename, dummy_markdown)))
            self.VAULT_CONN.commit()
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_add(self): sent query {db_tools.sql_notes('insert_new',(filename, '[CONTENT]'))}")
        except Exception as e:
            self.app.add_note(f"[ERROR] ❗ Error in adding file: {e}")

        self.sub_title = self.app.USERNAME
        self.tree_refresh()

    def action_note_delete(self) -> None:
        tree = self.app.query_one(Tree)
        node_label = tree.cursor_node.label
        node_id = tree.cursor_node.id

        # Check if tree cursor is a note
        if node_id < 1:
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_delete(self): nothing to delete. aborting")
            return

        # Despawn active text window
        if not self.EDITING:
            txtView = self.query_one(TextView)
            txtView.despawn()
        else:
            txtEdit = self.query_one(TextEdit)
            txtEdit.despawn()

        # Delete database row
        self.VAULT_DB.execute(db_tools.sql_notes("delete", node_label))
        self.VAULT_CONN.commit()
        if self.app.DEBUG: self.app.add_note(f"[Notes].action_note_delete(self): sent query: {db_tools.sql_notes('delete', node_label)}")

        # Refresh tree
        self.tree_refresh()

    def action_save(self) -> None:
        tree = self.app.query_one(Tree)
        node_label = tree.cursor_node.label
        node_id = tree.cursor_node.id
        txtEdit = self.query_one(TextEdit)

        # Check if tree cursor is a note and Edit mode is on
        if node_id < 1 or not self.EDITING:
            if self.app.DEBUG: self.app.add_note(f"[Notes].action_save(self): nothing to save. aborting")
            return

        # Get text from TextEdit
        selected_md = txtEdit.get_content()
        if self.app.DEBUG: self.app.add_note(f"[Notes].action_save(self): retireved content from TextEdit")

        # Update row in database
        self.VAULT_DB.execute(db_tools.sql_notes("update_content", (selected_md, node_label)))
        self.VAULT_CONN.commit()
        if self.app.DEBUG: self.app.add_note(f"[Notes].action_save(self): sent query: {db_tools.sql_notes('update_content', ('[CONTENT]', node_label))}")

        self.UNSAVED = True

        # Close connection to DB
        self.VAULT_CONN.close()
        if self.app.DEBUG: self.app.add_note(f"[Notes].action_save(self): Closed connection to database")

        # Resplit database
        if self.app.DEBUG: self.app.add_note(f"[Notes].action_save(self): Re-split database")
        db_tools.db_user_resplit(self.USERNAME, self.SECRET)

        # Re-connect to new database
        db_tools.db_user_join_splits(self.app.USERNAME, self.app.SECRET)
        self.VAULT_CONN = db_tools.db_user_connect(self.app.USERNAME, self.app.SECRET, self.app.PASSWORD)
        self.VAULT_DB = self.VAULT_CONN.cursor()

        # Refreshed tree
        self.tree_refresh()
        if self.app.DEBUG: self.app.add_note(f"[Notes].action_save(self): Refreshed tree")
        self.app.add_note("✅ Saved changes to vault")
        self.app.notify("✅ Saved changes to vault", title="SUCCESS", severity="information", timeout=3)

    def action_open_link(self, link: str) -> None:
        self.app.bell()
        import webbrowser
        webbrowser.open(link)
        if self.app.DEBUG: self.app.add_note(f"[Notes].action_open_link(self): opened: {link}")