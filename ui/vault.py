from __future__ import annotations

# Packages
import pyperclip
import sys

# Textual
from rich.console import RenderableType
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import (
Footer,
Header,
Input,
RichLog,
Static, Tree, Button,
)

# Caverna
import utils.db_tools as db_tools
import utils.pwd_tools as pwd_tools
from ui.utils import (
    Body,
    Section,
)


########################################################################################################################
# NewPasswordInfo: Textual Class. A similar copy of PasswordInfo, but  #
#                  used for gathering data required for inserting a    #
#                  new row into the vault.                             #
########################################################################
class NewPasswordInfo(Container):
    def compose(self) -> ComposeResult:
        yield Static("URL", classes="label")
        yield Input(placeholder="URL", type="text", id="new_input_url")
        yield Static("Username", classes="label")
        yield Input(placeholder="Username", type="text", id="new_input_username")
        yield Static("Password", classes="label")
        yield Input(placeholder="Password", type="text", id="new_input_password")
        yield Button(label="Add", variant="success", id="add_btn")
        yield Button(label="Cancel", variant="warning", id="cancel_btn")

    def spawn(self):
        new_pwd = pwd_tools.pwd_gen(30)
        self.remove_class("-hidden")
        self.query_one("#new_input_password").value = new_pwd
        if self.app.DEBUG: self.app.add_note(f"[NewPasswordInfo].spawn(self): generated {new_pwd}")

    def despawn(self):
        self.add_class("-hidden")
        self.query_one("#new_input_url").clear()
        self.query_one("#new_input_username").clear()
        self.query_one("#new_input_password").clear()
        if self.app.DEBUG: self.app.add_note(f"[NewPasswordInfo].despawn(self): cleared inputs")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = str(event.button.label)
        inp_url = self.app.query_one("#new_input_url").value
        inp_uname = self.app.query_one("#new_input_username").value
        inp_pwd = self.app.query_one("#new_input_password").value
        if self.app.DEBUG: self.app.add_note(
            f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): pressed {btn}")

        # Pressed Add button in insert mode
        if btn == "Add":
            try:
                conn = db_tools.db_user_connect(self.app.USERNAME, self.app.PASSWORD)
                c = conn.cursor()
                if self.app.DEBUG: self.app.add_note(
                    f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): connected to DB")

                key = pwd_tools.pwd_encrypt_key(self.app.PASSWORD)
                if self.app.DEBUG: self.app.add_note(
                    f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): encoded key({key.decode('ISO-8859-1')})")

                new_pwd, new_nonce = pwd_tools.pwd_encrypt(inp_pwd, key)
                if self.app.DEBUG: self.app.add_note(
                    f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): encrypted input pwd with nonce({new_nonce}): {new_pwd}")

                if self.app.DEBUG: self.app.add_note(
                    f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): sent query: {db_tools.sql('insert', (inp_url, inp_uname, new_pwd, new_nonce))}")
                c.execute(db_tools.sql("insert", (inp_url, inp_uname, new_pwd, str(new_nonce))))

                conn.commit()
                conn.close()
                self.app.add_note(
                    f"[INSERT] Inserted data UNAME:({inp_uname}) PASWD:({inp_pwd}) for new entry on -->{inp_url}")
            except Exception as e:
                self.app.bell()
                self.app.add_note("[INSERT] Failed to add new entry")
                self.app.add_note(e)

        self.despawn()
        if self.app.DEBUG: self.app.add_note(
            f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): despawned [NewPasswordInfo]")
        self.app.INSERTING = False
        if self.app.DEBUG: self.app.add_note(
            f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): INSERTING -> False")
        self.app.query_one(Tree).disabled = False
        self.app.tree_refresh()
        if self.app.DEBUG: self.app.add_note(
            f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): re-enabled Tree")
        self.app.add_note("[INSERT] Exited insert mode")
        self.app.sub_title = self.app.USERNAME


########################################################################################################################
# PasswordInfo: Textual Class. Show data about the selected url/unm/pw #
#               entry. Also stores buttons used in the edit mode.      #
########################################################################
class PasswordInfo(Container):
    old_url = ""
    old_uname = ""
    old_pwd = ""
    STORED = False
    SKIP = False

    def compose(self) -> ComposeResult:
        yield Static("URL", classes="label")
        yield Input(placeholder="URL", type="text", id="input_url", classes="disabled", disabled=True)
        yield Static("Username", classes="label")
        yield Input(placeholder="Username", type="text", id="input_username", classes="disabled", disabled=True)
        yield Static("Password", classes="label")
        yield Input(placeholder="Password", type="text", id="input_password", classes="disabled", disabled=True)
        yield Button(label="Save", variant="success", id="save_btn", classes="-hidden")
        yield Button(label="Delete", variant="error", id="delete_btn", classes="-hidden")

    def set_labels(self, url, username, password) -> None:
        self.query_one("#input_url").value = url
        self.query_one("#input_username").value = username
        self.query_one("#input_password").value = password
        if self.app.DEBUG: self.app.add_note(
            f"[PasswordInfo].set_labels(self, url, username, password): set labels to {url}, {username}, {password}")
        self.store_inputs()
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].set_labels(self, url, username, password): stored inputs")

    # Disable/enable input
    def disable(self) -> None:
        self.query_one("#input_url").disabled = True
        self.query_one("#input_username").disabled = True
        self.query_one("#input_password").disabled = True
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].disable(self): disabled self")

    def enable(self) -> None:
        self.query_one("#input_url").disabled = False
        self.query_one("#input_username").disabled = False
        self.query_one("#input_password").disabled = False
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].enable(self): enabled self")

    # Hide/unhide
    def spawn(self) -> None:
        self.remove_class("-hidden")
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].spawn(self): spawned self")

    def despawn(self) -> None:
        self.add_class("-hidden")
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].despawn(self): despawned self")

    # Hide/unhide buttons
    def show_btns(self) -> None:
        self.query_one("#save_btn").remove_class("-hidden")
        self.query_one("#delete_btn").remove_class("-hidden")
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].show_btns(self): showed buttons")

    def hide_btns(self) -> None:
        self.query_one("#save_btn").add_class("-hidden")
        self.query_one("#delete_btn").add_class("-hidden")
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].hide_btns(self): hid buttons")

    def _on_mount(self) -> None:
        self.disable()
        self.despawn()
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo]._on_mount(self): mounted self")

    def store_inputs(self) -> None:
        self.old_url = self.query_one("#input_url").value
        self.old_uname = self.query_one("#input_username").value
        self.old_pwd = self.query_one("#input_password").value
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].store_inputs(self): stored old inputs")

    # FUCK YOU, I DONT NEED THIS ON_INPUT_CHANGED BULLSHIT I CHANGED MY MIND
    # def on_input_changed(self, event: Input.Changed) -> None:
    #     if not self.STORED and self.app.EDITING:
    #         # I DONT KNOW WHY, I DONT WANT TO KNOW WHY, I SHOULDNT HAVE TO WONDER WHY, BUT FOR WATHEVER REASON
    #         # THIS STUPID SHIT DOESNT WORK UNLESS I USE A FUCKING FLAG TO SKIP THE LAST CHARACTER ON THE FIRST TIME
    #         # I STORE THE DATA.
    #         # MAY GOD HAVE MERCY ON MY SANITY AND PUT ME TO SLEEP ONE DAY.
    #         if not self.SKIP:
    #             event.input.value = event.input.value[:-1]
    #             self.SKIP = True
    #         else:
    #             self.old_url = self.query_one("#input_url").value
    #             self.old_uname = self.query_one("#input_username").value
    #             self.old_pwd = self.query_one("#input_password").value
    #             self.STORED = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = str(event.button.label)
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): pressed {btn}")
        sel_url = self.app.query_one("#input_url").value
        sel_uname = self.app.query_one("#input_username").value
        sel_pwd = self.app.query_one("#input_password").value

        # Pressed SAVE button in edit mode
        if btn == "Save":
            try:
                key = pwd_tools.pwd_encrypt_key(self.app.PASSWORD)
                if self.app.DEBUG: self.app.add_note(
                    f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): encrypted key({key.decode('ISO-8859-1')}")

                conn = db_tools.db_user_connect(self.app.USERNAME, self.app.PASSWORD)
                c = conn.cursor()
                if self.app.DEBUG: self.app.add_note(
                    f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): connected to db")

                c.execute(db_tools.sql("select_paswd", (self.old_url, self.old_uname)))
                res = c.fetchone()
                old_ciphertext = res[0]
                if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): fetched old encrypted password({old_ciphertext}) from db")

                new_ciphertext, new_nonce = pwd_tools.pwd_encrypt(sel_pwd, key)
                if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): encrypted input pwd({sel_pwd}) with new nonce({new_nonce}) -> {new_ciphertext}")

                c.execute(db_tools.sql("update_row",
                                       (sel_url, sel_uname, new_ciphertext, new_nonce, self.old_url, self.old_uname, old_ciphertext)))
                if self.app.DEBUG: self.app.add_note(
                    f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): executed query {db_tools.sql('update_row', (sel_url, sel_uname, new_ciphertext, new_nonce, self.old_url, self.old_uname, old_ciphertext))}")
                conn.commit()
                conn.close()

                self.app.tree_refresh()
                if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): refreshing tree")
                self.app.add_note(f"[EDIT] Edited entry on --> {self.old_url}")
            except Exception as e:
                self.app.bell()
                self.app.add_note("[EDIT] Failed to edit entry")
                self.app.add_note(str(e))

        # Pressed DELETE button in edit mode
        elif btn == "Delete":
            try:
                conn = db_tools.db_user_connect(self.app.USERNAME, self.app.PASSWORD)
                c = conn.cursor()
                if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): connected to db")
                c.execute(db_tools.sql("delete", (sel_url, sel_uname, sel_pwd)))
                if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): executed query {db_tools.sql('delete', (sel_url, sel_uname, sel_pwd))}")

                conn.commit()
                conn.close()
                self.app.add_note(f"[EDIT] Removed entry on -->{sel_url} with username ({sel_uname})")
            except Exception as e:
                self.app.bell()
                self.app.add_note("[EDIT] Failed to remove entry")
                self.app.add_note(str(e))
            self.app.tree_refresh()
            if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): refreshing tree")


########################################################################################################################
# Vault: Textual App. Main boy and logic of the vault. Contains the    #
#        all of the textual widgets and classes, Tree logic, and       #
#        bindings.                                                     #
########################################################################
class Vault(App[None]):
    CSS_PATH = ["../css/login.tcss", "../css/vault.tcss"]
    USERNAME = "None"
    PASSWORD = "None"
    DEBUG = False
    EDITING = False
    INSERTING = False
    TREE_PWDS = []

    def __init__(self, USERNAME, PASSWORD, DEBUG):
        if USERNAME == "None" and PASSWORD == "None":
            sys.exit("[ERROR]: Login module skipped. Aborting")
        self.DEBUG = DEBUG
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        super().__init__()

    BINDINGS = [
        Binding(key="f1", action="app.toggle_class('RichLog', '-hidden')", description="Log"),
        Binding(key="f2", action="clip_username", description="C:UNAME"),
        Binding(key="f3", action="clip_password", description="C:PWSD"),
        Binding(key="ctrl+a", action="pwd_add", description="Insert"),
        Binding(key="ctrl+e", action="pwd_edit", description="Edit"),
        Binding(key="f8", action="app.toggle_dark", description="Theme"),
        Binding(key="ctrl+q", action="app.quit", description="Quit"),
    ]

    def tree_initialize(self, tree):
        pwds = tree.root.children[0]

        conn = db_tools.db_user_connect(self.app.USERNAME, self.app.PASSWORD)
        c = conn.cursor()

        c.execute(db_tools.sql("print", ""))

        urls = c.fetchall()

        self.app.TREE_PWDS = urls
        for u in urls:
            pwds.add_leaf(u[0])

        pwds.expand()
        conn.commit()
        conn.close()

    def tree_refresh(self) -> None:
        tree = self.query_one(Tree)
        tree.clear()
        if self.app.DEBUG: self.app.add_note(f"[Vault].tree_refresh(self): cleared tree")
        tree.root.add_leaf(label="URLs")
        self.tree_initialize(tree)
        tree.cursor_line = 1
        tree.root.expand()
        if self.app.DEBUG: self.app.add_note(f"[Vault].tree_refresh(self): refreshed tree")

    def compose(self) -> ComposeResult:
        tree: Tree[dict] = Tree(self.app.USERNAME, id="vault-tree")
        tree.root.add_leaf(label="URLs")
        self.tree_initialize(tree)
        tree.root.expand()
        self.app.sub_title = self.app.USERNAME

        yield Container(
            Header(show_clock=True),
            RichLog(classes="-hidden", wrap=False, highlight=True, markup=True),
            Body(
                tree,
                Section(
                    PasswordInfo(),
                    NewPasswordInfo(),
                    id="vault-body"
                ),
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Tree).focus()
        self.app.add_note(f"Welcome, {self.app.USERNAME}")
        self.query_one(NewPasswordInfo).add_class("-hidden")
        if self.app.DEBUG: self.app.add_note(f"[Vault].__init__(self, USERNAME, PASSWORD, DEBUG): opened vault with data: {self.USERNAME}, {self.PASSWORD}, {self.DEBUG}")
        if self.app.DEBUG: self.app.add_note(f"[Vault].compose(self): initialized tree")
        if self.app.DEBUG: self.app.add_note(f"[Vault].compose(self): finished composing")
        if self.app.DEBUG: self.app.add_note(f"[Vault].on_mount(self): hid NewPasswordInfo")

    def add_note(self, renderable: RenderableType) -> None:
        self.query_one(RichLog).write(renderable)

    # Used for handling http links
    def action_open_link(self, link: str) -> None:
        self.app.bell()
        import webbrowser
        webbrowser.open(link)
        if self.app.DEBUG: self.app.add_note(f"[Vault].action_open_link(self): opened: {link}")

    def on_tree_node_selected(self) -> None:
        tree = self.app.query_one(Tree)
        pwinfo = self.app.query_one(PasswordInfo)
        node_label = tree.cursor_node.label
        node_id = tree.cursor_node.id - 2

        if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): selected tree: {tree}")
        if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): selected node: {node_label} id_{node_id + 2}")

        if node_id == -2:
            self.app.add_note(f"> {self.app.USERNAME} user")
            pwinfo.despawn()
            if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): despawned PasswordInfo")
            return

        if node_id == -1:
            self.app.add_note(f"-> {self.app.USERNAME} vault")
            if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): despawned PasswordInfo")
            pwinfo.despawn()
            return

        selected_url = self.app.TREE_PWDS[node_id][0]
        selected_username = self.app.TREE_PWDS[node_id][1]
        selected_password = self.app.TREE_PWDS[node_id][2]
        if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): stored {selected_url}, {selected_username}, {selected_password}")

        if self.app.EDITING:
            pwinfo.show_btns()
            if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): showing PasswordInfo buttons")
            pwinfo.STORED = False
            if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): STORED -> False")

        self.app.add_note(f"--> {node_label}")
        pwinfo.spawn()
        if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): spawned PassowrdInfo")

        conn = db_tools.db_user_connect(self.app.USERNAME, self.app.PASSWORD)
        c = conn.cursor()
        if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): connected to db")

        c.execute(db_tools.sql("select_nonce", (selected_username, selected_password)))
        if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): executed query: {db_tools.sql('select_nonce', (selected_username, selected_password))}")

        crypto = c.fetchone()
        # nonce = base64.b64encode(crypto[0], 'utf-8')
        nonce = crypto[0]
        if self.app.DEBUG: self.app.add_note(
            f"[Vault].on_tree_node_selected(self): fetched nonce({nonce}) from db")
        key = pwd_tools.pwd_encrypt_key(self.app.PASSWORD)
        if self.app.DEBUG: self.app.add_note(
            f"[Vault].on_tree_node_selected(self): encrypted key({key.decode('ISO-8859-1')})")

        conn.commit()
        conn.close()
        if self.app.DEBUG: self.app.add_note(
            f"[Vault].on_tree_node_selected(self): closed connection to db")

        decrypted_pwd = pwd_tools.pwd_decrypt(selected_password, nonce, key)
        if self.app.DEBUG: self.app.add_note(f"{selected_password}, {nonce}, {key}")
        if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): decrypted password({selected_password} -> {decrypted_pwd})")

        pwinfo.set_labels(selected_url, selected_username, decrypted_pwd)
        pyperclip.copy(str(self.app.PASSWORD))
        if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): updated PasswordInfo labels")

    def action_pwd_edit(self) -> None:
        tree = self.app.query_one(Tree)
        pwinfo = self.app.query_one(PasswordInfo)
        node_id = tree.cursor_node.id - 1
        if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): editing on tree {tree}")
        if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): editing node id {node_id}")

        if node_id < 1:
            self.app.EDITING = False
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): EDITING -> False")
            pwinfo.hide_btns()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): hid PasswordInfo buttons")
            pwinfo.disable()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): disabled PasswordInfo")
            self.app.sub_title = self.app.USERNAME
            return

        if self.app.EDITING:
            self.app.add_note("[EDIT] Exited edit mode")
            pwinfo.hide_btns()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): hid PasswordInfo buttons")
            pwinfo.disable()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): disabled PasswordInfo")
            pwinfo.STORED = True
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): PasswordInfo STORED -> True")
            self.app.sub_title = self.app.USERNAME
            self.app.EDITING = False
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): EDITING -> False")

        else:
            self.app.add_note("[EDIT] Editing password")
            pwinfo.enable()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): enabled PasswordInfo")
            pwinfo.show_btns()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): showing PasswordInfo buttons")
            pwinfo.store_inputs()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): stored PasswordInfo inputs")
            pwinfo.STORED = False
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): PasswordInfo STORED -> True")
            self.app.sub_title = f"{self.app.USERNAME}: Edit"
            self.app.EDITING = True
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): EDITING -> True")

    def action_pwd_add(self) -> None:
        if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): INSERTING: {self.app.INSERTING}")
        if not self.app.INSERTING:
            self.app.INSERTING = True
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): INSERTING -> True")
            self.app.add_note("[INSERT] Insert mode")
            self.app.sub_title = f"{self.app.USERNAME}: Insert"

            pwi = self.app.query_one(PasswordInfo)
            pwi.disable()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): disabled PasswordInfo")
            pwi.hide_btns()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): hid PasswordInfo buttons")
            pwi.despawn()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): despawning PasswordInfo")
            self.app.query_one(NewPasswordInfo).spawn()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): spawned NewPasswordInfo")

            pwds = self.app.query_one(Tree).root.children[0]
            pwds.add_leaf(label="<NEW>")
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): added new node to Tree")
            self.query_one(Tree).disabled = True
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): disabled Tree")

        else:
            self.app.add_note("[INSERT] Already in insert mode")

    def action_clip_username(self) -> None:
        if self.app.query_one(PasswordInfo).has_class("-hidden"):
            self.app.bell()
            self.app.add_note(f"Nothing to copy")
        elif self.app.EDITING:
            self.app.bell()
            self.app.add_note(f"[EDIT] Cannot copy while in edit mode")
        else:
            url = self.app.query_one(PasswordInfo).query_one("#input_url").value
            username = self.app.query_one(PasswordInfo).query_one("#input_username").value
            pyperclip.copy(username)
            self.app.add_note(f"Copied username on -->{url} to clipboard")

    def action_clip_password(self) -> None:
        if self.app.query_one(PasswordInfo).has_class("-hidden"):
            self.app.bell()
            self.app.add_note(f"Nothing to copy")
        elif self.app.EDITING:
            self.app.bell()
            self.app.add_note(f"[EDIT] Cannot copy while in edit mode")
        else:
            url = self.app.query_one(PasswordInfo).query_one("#input_url").value
            password = self.app.query_one(PasswordInfo).query_one("#input_password").value
            pyperclip.copy(password)
            self.app.add_note(f"Copied password on -->{url} to clipboard")
