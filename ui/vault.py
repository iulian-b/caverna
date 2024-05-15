from __future__ import annotations

import atexit
import os

# Packages
import pyperclip
import sys

# Textual
from rich.console import RenderableType
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
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


    @on(Button.Pressed, "#add_btn")
    def add_pressed(self, event: Button.Pressed) -> None:
        btn = str(event.button.label)
        inp_url = self.query_one("#new_input_url").value
        inp_uname = self.query_one("#new_input_username").value
        inp_pwd = self.query_one("#new_input_password").value
        if self.app.DEBUG: self.app.add_note(
            f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): pressed {btn}")

        try:
            key = pwd_tools.pwd_encrypt_key(self.app.PASSWORD)
            if self.app.DEBUG: self.app.add_note(f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): encoded key({key.decode('ISO-8859-1')})")

            new_pwd, new_nonce = pwd_tools.pwd_encrypt(inp_pwd, key)
            if self.app.DEBUG: self.app.add_note(f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): encrypted input pwd with nonce({new_nonce}): {new_pwd}")

            if self.app.DEBUG: self.app.add_note(f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): sent query: {db_tools.sql('insert', (inp_url, inp_uname, new_pwd, new_nonce))}")
            self.screen.VAULT_DB.execute(db_tools.sql("insert", (inp_url, inp_uname, new_pwd, str(new_nonce))))

            self.screen.VAULT_CONN.commit()
            self.app.add_note(f"[INSERT] Inserted data UNAME:({inp_uname}) PASWD:({inp_pwd}) for new entry on -->{inp_url}")
        except Exception as e:
            self.app.bell()
            self.app.add_note("[INSERT] Failed to add new entry")
            self.app.add_note(e)

        self.despawn()
        if self.app.DEBUG: self.app.add_note(f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): despawned [NewPasswordInfo]")
        self.screen.INSERTING = False
        if self.app.DEBUG: self.app.add_note(f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): INSERTING -> False")

        self.app.query_one(Tree).disabled = False
        self.screen.tree_refresh()
        if self.app.DEBUG: self.app.add_note(f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): re-enabled Tree")
        self.app.add_note("[INSERT] Exited insert mode")
        self.sub_title = self.app.USERNAME

    @on(Button.Pressed, "#cancel_btn")
    def cancel_pressed(self, event: Button.Pressed) -> None:
        self.despawn()
        if self.app.DEBUG: self.app.add_note(f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): despawned [NewPasswordInfo]")
        self.screen.INSERTING = False
        if self.app.DEBUG: self.app.add_note(f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): INSERTING -> False")

        self.app.query_one(Tree).disabled = False
        self.screen.tree_refresh()
        if self.app.DEBUG: self.app.add_note(f"[NewPasswordInfo].on_button_press(self, event: Button.Pressed): re-enabled Tree")
        self.app.add_note("[INSERT] Exited insert mode")
        self.sub_title = self.app.USERNAME

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

    # FUCK YOU I DONT NEED THIS ON_INPUT_CHANGED BULLSHIT I CHANGED MY MIND
    # def on_input_changed(self, event: Input.Changed) -> None:
    #     if not self.STORED and self.app.EDITING:
    #         # I DONT KNOW WHY, I DONT WANT TO KNOW WHY, I SHOULDNT HAVE TO WONDER WHY, BUT FOR WATHEVER REASON
    #         # THIS STUPID THING DOESNT WORK UNLESS I USE A FUCKING FLAG TO SKIP THE LAST CHARACTER ON THE FIRST TIME
    #         # I READ AND STORE THE DATA.
    #         # MAY GOD HAVE MERCY ON MY SANITY AND PUT ME TO SLEEP ONE DAY.
    #         if not self.SKIP:
    #             event.input.value = event.input.value[:-1]
    #             self.SKIP = True
    #         else:
    #             self.old_url = self.query_one("#input_url").value
    #             self.old_uname = self.query_one("#input_username").value
    #             self.old_pwd = self.query_one("#input_password").value
    #             self.STORED = True

    @on(Button.Pressed, "#save_btn")
    def save_pressed(self, event: Button.Pressed) -> None:
        btn = str(event.button.label)
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): pressed {btn}")
        sel_url = self.query_one("#input_url").value
        sel_uname = self.query_one("#input_username").value
        sel_pwd = self.query_one("#input_password").value

        try:
            key = pwd_tools.pwd_encrypt_key(self.app.PASSWORD)
            if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): encrypted key({key.decode('ISO-8859-1')}")

            self.screen.VAULT_DB.execute(db_tools.sql("select_paswd", (self.old_url, self.old_uname)))
            res = self.screen.VAULT_DB.fetchone()
            old_ciphertext = res[0]
            if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): fetched old encrypted password({old_ciphertext}) from db")

            new_ciphertext, new_nonce = pwd_tools.pwd_encrypt(sel_pwd, key)
            if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): encrypted input pwd({sel_pwd}) with new nonce({new_nonce}) -> {new_ciphertext}")

            self.screen.VAULT_DB.execute(db_tools.sql("update_row",
                                                      (sel_url, sel_uname, new_ciphertext, new_nonce, self.old_url,
                                                       self.old_uname,old_ciphertext)))
            if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): executed query {db_tools.sql('update_row', (sel_url, sel_uname, new_ciphertext, new_nonce, self.old_url, self.old_uname, old_ciphertext))}")
            self.screen.VAULT_CONN.commit()

            self.screen.tree_refresh()
            if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): refreshing tree")
            self.app.add_note(f"[EDIT] Edited entry on --> {self.old_url}")

        except Exception as e:
            self.app.bell()
            self.app.add_note("[EDIT] Failed to edit entry")
            self.app.add_note(str(e))

    @on(Button.Pressed, "#delete_btn")
    def delete_pressed(self, event: Button.Pressed) -> None:
        btn = str(event.button.label)
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): pressed {btn}")
        sel_url = self.query_one("#input_url").value
        sel_uname = self.query_one("#input_username").value
        sel_pwd = self.query_one("#input_password").value

        try:
            self.screen.VAULT_DB.execute(db_tools.sql("delete", (sel_url, sel_uname, sel_pwd)))
            if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): executed query {db_tools.sql('delete', (sel_url, sel_uname, sel_pwd))}")

            self.screen.VAULT_CONN.commit()
            self.app.add_note(f"[EDIT] Removed entry on -->{sel_url} with username ({sel_uname})")

        except Exception as e:
            self.app.bell()
            self.app.add_note("[EDIT] Failed to remove entry")
            self.app.add_note(str(e))

        self.screen.tree_refresh()
        if self.app.DEBUG: self.app.add_note(f"[PasswordInfo].on_button_pressed(self, event: Button.Pressed): refreshing tree")


########################################################################################################################
# Vault: Textual App. Main body and logic of the vault. Contains the   #
#        all of the textual widgets and classes, Tree logic, and       #
#        bindings.                                                     #
########################################################################
class Vault(Screen):
    # CSS
    CSS_PATH = ["../css/login.tcss", "../css/vault.tcss"]

    # Authentication info
    USERNAME = None
    PASSWORD = None
    SECRET = None

    # Debug
    DEBUG = False

    # Flags
    EDITING = False
    INSERTING = False

    # Url Tree
    TREE_PWDS = []

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

    # REVISIT THIS
    BINDINGS = [
        Binding(key="f2", action="clip_username", description="📋 UNAME"),
        Binding(key="f3", action="clip_password", description="📋 PWSD"),
        Binding(key="f5", action="save", description="💾 Save"),
        Binding(key="ctrl+a", action="pwd_add", description="🆕 Insert"),
        Binding(key="ctrl+e", action="pwd_edit", description="🔄 Edit"),
        Binding(key="ctrl+q", action="back", priority=True, description="🔙 Back"),
    ]

    def action_back(self) -> None:
        self.VAULT_CONN.close()
        self.app.pop_screen()

    # DEPRECATED
    # def action_back(self) -> None:
    #     # Close connection to database
    #     self.VAULT_DB.close()
    #     if self.app.DEBUG: self.app.add_note(f"[Vault].action_back(self): Closed connection to database")
    #
    #     # Resplit database
    #     db_tools.db_user_resplit(self.USERNAME, self.SECRET)
    #     if self.app.DEBUG: self.app.add_note(f"[Vault].action_back(self): Re-split database")
    #
    #     # Exit
    #     self.app.exit(-1)

    def tree_initialize(self, tree):
        pwds = tree.root.children[0]

        self.VAULT_DB.execute(db_tools.sql("print", ""))
        urls = self.VAULT_DB.fetchall()
        self.VAULT_CONN.commit()

        self.TREE_PWDS = urls
        for u in urls:
            pwds.add_leaf(u[0])

        pwds.expand()

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
        self.sub_title = self.app.USERNAME

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
        self.app.add_note(f"🔑 Entered {self.app.USERNAME}'s Vault")
        self.query_one(NewPasswordInfo).add_class("-hidden")
        if self.app.DEBUG: self.app.add_note(
            f"[Vault].__init__(self, USERNAME, PASSWORD, DEBUG): opened vault with data: {self.USERNAME}, {self.PASSWORD}, {self.DEBUG}")
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
        tree = self.query_one(Tree)
        pwinfo = self.query_one(PasswordInfo)
        node_label = tree.cursor_node.label
        node_id = tree.cursor_node.id - 2

        if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): selected tree: {tree}")
        if self.app.DEBUG: self.app.add_note(
            f"[Vault].on_tree_node_selected(self): selected node: {node_label} id_{node_id + 2}")

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

        selected_url = self.TREE_PWDS[node_id][0]
        selected_username = self.TREE_PWDS[node_id][1]
        selected_password = self.TREE_PWDS[node_id][2]
        if self.app.DEBUG: self.app.add_note(
            f"[Vault].on_tree_node_selected(self): stored {selected_url}, {selected_username}, {selected_password}")

        if self.EDITING:
            pwinfo.show_btns()
            if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): showing PasswordInfo buttons")
            pwinfo.STORED = False
            if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): STORED -> False")

        self.app.add_note(f"--> {node_label}")
        pwinfo.spawn()
        if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): spawned PassowrdInfo")

        self.VAULT_DB.execute(db_tools.sql("select_nonce", (selected_username, selected_password)))
        if self.app.DEBUG: self.app.add_note(
            f"[Vault].on_tree_node_selected(self): executed query: {db_tools.sql('select_nonce', (selected_username, selected_password))}")

        crypto = self.VAULT_DB.fetchone()
        # nonce = base64.b64encode(crypto[0], 'utf-8')
        nonce = crypto[0]
        if self.app.DEBUG: self.app.add_note(
            f"[Vault].on_tree_node_selected(self): fetched nonce({nonce}) from db")
        key = pwd_tools.pwd_encrypt_key(self.app.PASSWORD)
        if self.app.DEBUG: self.app.add_note(
            f"[Vault].on_tree_node_selected(self): encrypted key({key.decode('ISO-8859-1')})")

        self.VAULT_CONN.commit()

        decrypted_pwd = pwd_tools.pwd_decrypt(selected_password, nonce, key)
        if self.app.DEBUG: self.app.add_note(f"{selected_password}, {nonce}, {key}")
        if self.app.DEBUG: self.app.add_note(
            f"[Vault].on_tree_node_selected(self): decrypted password({selected_password} -> {decrypted_pwd})")

        pwinfo.set_labels(selected_url, selected_username, decrypted_pwd)
        pyperclip.copy(str(self.app.PASSWORD))
        if self.app.DEBUG: self.app.add_note(f"[Vault].on_tree_node_selected(self): updated PasswordInfo labels")

    def action_pwd_edit(self) -> None:
        tree = self.query_one(Tree)
        pwinfo = self.query_one(PasswordInfo)
        node_id = tree.cursor_node.id - 1
        if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): editing on tree {tree}")
        if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): editing node id {node_id}")

        if node_id < 1:
            self.EDITING = False
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): EDITING -> False")
            pwinfo.hide_btns()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): hid PasswordInfo buttons")
            pwinfo.disable()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): disabled PasswordInfo")
            self.sub_title = self.app.USERNAME
            return

        if self.EDITING:
            self.app.add_note("[EDIT] Exited edit mode")
            pwinfo.hide_btns()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): hid PasswordInfo buttons")
            pwinfo.disable()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): disabled PasswordInfo")
            pwinfo.STORED = True
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): PasswordInfo STORED -> True")
            self.sub_title = self.app.USERNAME
            self.EDITING = False
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
            self.sub_title = f"{self.app.USERNAME}: Edit"
            self.EDITING = True
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_edit(self): EDITING -> True")

    def action_pwd_add(self) -> None:
        if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): INSERTING: {self.INSERTING}")
        if not self.INSERTING:
            self.INSERTING = True
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): INSERTING -> True")
            self.app.add_note("[INSERT] Insert mode")
            self.sub_title = f"{self.app.USERNAME}: Insert"

            pwi = self.query_one(PasswordInfo)
            pwi.disable()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): disabled PasswordInfo")
            pwi.hide_btns()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): hid PasswordInfo buttons")
            pwi.despawn()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): despawning PasswordInfo")
            self.query_one(NewPasswordInfo).spawn()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): spawned NewPasswordInfo")

            pwds = self.query_one(Tree).root.children[0]
            pwds.add_leaf(label="<NEW>")
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): added new node to Tree")
            self.query_one(Tree).disabled = True
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_pwd_add(self): disabled Tree")

        else:
            self.app.add_note("[INSERT] Already in insert mode")

    # NOT WORKING AS INTENDED
    def action_save(self) -> None:
        # Close connection to DB
        self.VAULT_CONN.commit()
        self.VAULT_CONN.close()
        if self.app.DEBUG: self.app.add_note(f"[Vault].action_save(self): Closed connection to database")

        # Delete old splits
        # db_tools.db_user_remove_splits(self.app.USERNAME, self.app.SECRET)
        # if self.app.DEBUG: self.app.add_note(f"[Vault].action_save(self): Removed old fragments")

        # Resplit database
        if self.app.DEBUG: self.app.add_note(f"[Vault].action_save(self): Re-split database")
        db_tools.db_user_resplit(self.USERNAME, self.SECRET)

        # Re-connect to new database
        db_tools.db_user_join_splits(self.app.USERNAME, self.app.SECRET)
        self.VAULT_CONN = db_tools.db_user_connect(self.app.USERNAME, self.app.SECRET, self.app.PASSWORD)
        self.VAULT_DB = self.VAULT_CONN.cursor()

        # Refreshed tree
        self.tree_refresh()
        if self.app.DEBUG: self.app.add_note(f"[Vault].action_save(self): Refreshed tree")
        self.app.add_note("✅ Saved changes to vault")

    def action_safe_exit(self) -> None:
        try:
            self.VAULT_CONN.commit()
            self.VAULT_CONN.close()
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_save(self): Closed connection to database")

            user_path = f"caves/{self.app.USERNAME}.cvrn"
            user_file = open(user_path, 'rw')
            user_file.close()
        #     os.remove(user_path)
        #
        except Exception as e:
            if self.app.DEBUG: self.app.add_note(f"[Vault].action_safe_exit(self): Safe Exit exception")
            print(e)

        # self.app.exit(1)
        self.app.pop_screen()

    def action_clip_username(self) -> None:
        if self.query_one(PasswordInfo).has_class("-hidden"):
            self.app.bell()
            self.app.add_note(f"Nothing to copy")
        elif self.EDITING:
            self.app.bell()
            self.app.add_note(f"[EDIT] Cannot copy while in edit mode")
        else:
            url = self.query_one(PasswordInfo).query_one("#input_url").value
            username = self.query_one(PasswordInfo).query_one("#input_username").value
            pyperclip.copy(username)
            self.app.add_note(f"Copied username on -->{url} to clipboard")

    def action_clip_password(self) -> None:
        if self.query_one(PasswordInfo).has_class("-hidden"):
            self.app.bell()
            self.app.add_note(f"Nothing to copy")
        elif self.EDITING:
            self.app.bell()
            self.app.add_note(f"[EDIT] Cannot copy while in edit mode")
        else:
            url = self.query_one(PasswordInfo).query_one("#input_url").value
            password = self.query_one(PasswordInfo).query_one("#input_password").value
            pyperclip.copy(password)
            self.app.add_note(f"Copied password on -->{url} to clipboard")
