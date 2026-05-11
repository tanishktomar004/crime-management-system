import tkinter as tk
from tkinter import ttk, messagebox, font
import sqlite3
from datetime import datetime
import re

# ─────────────────────────────────────────────
#  DATABASE SETUP
# ─────────────────────────────────────────────

DB_NAME = "crime_management.db"

def get_conn():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS criminals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            alias       TEXT,
            age         INTEGER,
            gender      TEXT,
            nationality TEXT,
            address     TEXT,
            photo_path  TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS crimes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            criminal_id   INTEGER REFERENCES criminals(id) ON DELETE CASCADE,
            crime_type    TEXT    NOT NULL,
            description   TEXT,
            location      TEXT,
            date_of_crime TEXT,
            status        TEXT    DEFAULT 'Under Investigation',
            severity      TEXT    DEFAULT 'Medium',
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS officers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            badge_no   TEXT UNIQUE NOT NULL,
            rank       TEXT,
            department TEXT,
            contact    TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            case_no       TEXT UNIQUE NOT NULL,
            crime_id      INTEGER REFERENCES crimes(id) ON DELETE CASCADE,
            officer_id    INTEGER REFERENCES officers(id),
            title         TEXT NOT NULL,
            description   TEXT,
            status        TEXT DEFAULT 'Open',
            priority      TEXT DEFAULT 'Medium',
            opened_date   TEXT,
            closed_date   TEXT,
            created_at    TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id     INTEGER REFERENCES cases(id) ON DELETE CASCADE,
            type        TEXT NOT NULL,
            description TEXT,
            location    TEXT,
            collected_by TEXT,
            date_collected TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
#  COLOURS & STYLE CONSTANTS
# ─────────────────────────────────────────────

BG       = "#0d1117"
SURFACE  = "#161b22"
CARD     = "#21262d"
BORDER   = "#30363d"
ACCENT   = "#f85149"        # red – law-enforcement vibe
ACCENT2  = "#388bfd"        # blue
SUCCESS  = "#3fb950"
WARNING  = "#d29922"
FG       = "#e6edf3"
FG_DIM   = "#8b949e"
ENTRY_BG = "#0d1117"

BTN_STYLE = {"bg": ACCENT, "fg": "#ffffff", "activebackground": "#da3633",
             "relief": "flat", "cursor": "hand2", "bd": 0}

SECONDARY_BTN = {"bg": ACCENT2, "fg": "#ffffff", "activebackground": "#1f6feb",
                 "relief": "flat", "cursor": "hand2", "bd": 0}

GREEN_BTN = {"bg": SUCCESS, "fg": "#ffffff", "activebackground": "#2ea043",
             "relief": "flat", "cursor": "hand2", "bd": 0}

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def styled_entry(parent, **kwargs):
    e = tk.Entry(parent, bg=ENTRY_BG, fg=FG, insertbackground=FG,
                 relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT2,
                 **kwargs)
    return e

def styled_label(parent, text, size=10, bold=False, color=None, **kwargs):
    f = ("Consolas", size, "bold" if bold else "normal")
    lbl = tk.Label(parent, text=text, font=f, bg=parent["bg"],
                   fg=color or FG, **kwargs)
    return lbl

def card_frame(parent, **kwargs):
    return tk.Frame(parent, bg=CARD, bd=0, highlightthickness=1,
                    highlightbackground=BORDER, **kwargs)

def section_header(parent, title):
    f = tk.Frame(parent, bg=SURFACE)
    f.pack(fill="x", pady=(0, 8))
    tk.Label(f, text=title, font=("Consolas", 12, "bold"),
             bg=SURFACE, fg=ACCENT).pack(side="left")
    tk.Frame(f, bg=BORDER, height=1).pack(side="left", fill="x",
                                          expand=True, padx=(10, 0), pady=6)

def make_table(parent, columns, col_widths):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.Treeview",
                    background=CARD, foreground=FG,
                    fieldbackground=CARD, rowheight=28,
                    font=("Consolas", 9))
    style.configure("Dark.Treeview.Heading",
                    background=SURFACE, foreground=FG_DIM,
                    font=("Consolas", 9, "bold"), relief="flat")
    style.map("Dark.Treeview",
              background=[("selected", ACCENT2)],
              foreground=[("selected", "#ffffff")])

    frame = tk.Frame(parent, bg=BG)
    frame.pack(fill="both", expand=True)

    sb = tk.Scrollbar(frame, orient="vertical", bg=SURFACE,
                      troughcolor=BG, activebackground=BORDER)
    sb.pack(side="right", fill="y")

    tree = ttk.Treeview(frame, columns=columns, show="headings",
                        style="Dark.Treeview", yscrollcommand=sb.set)
    for col, w in zip(columns, col_widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="w")
    tree.pack(fill="both", expand=True)
    sb.config(command=tree.yview)
    return tree

# ─────────────────────────────────────────────
#  MODAL BASE
# ─────────────────────────────────────────────

class Modal(tk.Toplevel):
    def __init__(self, parent, title, width=520, height=500):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=SURFACE)
        self.resizable(False, False)
        self.grab_set()
        sw = parent.winfo_screenwidth()
        sh = parent.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def field_row(self, parent, label, row, col=0, span=1, widget=None):
        tk.Label(parent, text=label, font=("Consolas", 9), bg=SURFACE,
                 fg=FG_DIM, anchor="w").grid(row=row, column=col*2,
                                              sticky="w", padx=(0, 6), pady=4)
        if widget is None:
            widget = styled_entry(parent)
        widget.grid(row=row, column=col*2+1, sticky="ew",
                    padx=(0, 10), pady=4, columnspan=span)
        return widget

# ─────────────────────────────────────────────
#  CRIMINALS MODULE
# ─────────────────────────────────────────────

class CriminalsFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE)
        self._build()
        self.refresh()

    def _build(self):
        # Top bar
        top = tk.Frame(self, bg=SURFACE)
        top.pack(fill="x", pady=(0, 10))
        styled_label(top, "CRIMINAL RECORDS", 14, True, ACCENT).pack(side="left")

        btn_frame = tk.Frame(top, bg=SURFACE)
        btn_frame.pack(side="right")
        tk.Button(btn_frame, text="+ Add Criminal", **BTN_STYLE,
                  font=("Consolas", 9, "bold"), padx=12, pady=5,
                  command=self.add_dialog).pack(side="left", padx=4)
        tk.Button(btn_frame, text="✎ Edit", **SECONDARY_BTN,
                  font=("Consolas", 9, "bold"), padx=12, pady=5,
                  command=self.edit_dialog).pack(side="left", padx=4)
        tk.Button(btn_frame, text="✕ Delete", bg="#6e7681", fg=FG,
                  activebackground=ACCENT, relief="flat", cursor="hand2", bd=0,
                  font=("Consolas", 9, "bold"), padx=12, pady=5,
                  command=self.delete).pack(side="left", padx=4)

        # Search
        sf = tk.Frame(self, bg=CARD, pady=8, padx=10)
        sf.pack(fill="x", pady=(0, 10))
        sf.configure(highlightthickness=1, highlightbackground=BORDER)
        tk.Label(sf, text="🔍 Search:", font=("Consolas", 9),
                 bg=CARD, fg=FG_DIM).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *_: self.refresh())
        se = tk.Entry(sf, textvariable=self.search_var,
                      bg=ENTRY_BG, fg=FG, insertbackground=FG,
                      relief="flat", font=("Consolas", 10), width=30)
        se.pack(side="left", padx=8)

        # Table
        cols = ("ID", "Name", "Alias", "Age", "Gender", "Nationality", "Address", "Registered")
        widths = (40, 130, 100, 40, 60, 100, 160, 120)
        self.tree = make_table(self, cols, widths)

    def refresh(self):
        q = self.search_var.get().strip()
        conn = get_conn()
        c = conn.cursor()
        if q:
            c.execute("""SELECT id, name, alias, age, gender, nationality, address,
                                created_at FROM criminals
                         WHERE name LIKE ? OR alias LIKE ? OR nationality LIKE ?""",
                      (f"%{q}%", f"%{q}%", f"%{q}%"))
        else:
            c.execute("SELECT id, name, alias, age, gender, nationality, address, created_at FROM criminals")
        rows = c.fetchall()
        conn.close()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in rows:
            self.tree.insert("", "end", values=r)

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a criminal record.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def add_dialog(self):
        CriminalDialog(self, "Add Criminal")

    def edit_dialog(self):
        cid = self._selected_id()
        if cid:
            conn = get_conn()
            row = conn.execute("SELECT * FROM criminals WHERE id=?", (cid,)).fetchone()
            conn.close()
            CriminalDialog(self, "Edit Criminal", row)

    def delete(self):
        cid = self._selected_id()
        if cid and messagebox.askyesno("Confirm", "Delete this criminal record?"):
            conn = get_conn()
            conn.execute("DELETE FROM criminals WHERE id=?", (cid,))
            conn.commit()
            conn.close()
            self.refresh()

class CriminalDialog(Modal):
    def __init__(self, parent_frame, title, data=None):
        super().__init__(parent_frame.winfo_toplevel(), title, 560, 420)
        self.parent_frame = parent_frame
        self.data = data
        self._build()
        if data:
            self._fill(data)

    def _build(self):
        tk.Label(self, text=self.title(), font=("Consolas", 12, "bold"),
                 bg=SURFACE, fg=ACCENT).pack(pady=(16, 10))
        grid = tk.Frame(self, bg=SURFACE)
        grid.pack(padx=24, pady=4, fill="both")
        grid.columnconfigure(1, weight=1); grid.columnconfigure(3, weight=1)

        self.name     = self.field_row(grid, "Full Name *", 0)
        self.alias    = self.field_row(grid, "Alias / Nick", 1)
        self.age      = self.field_row(grid, "Age", 2, col=0)

        self.gender   = ttk.Combobox(grid, values=["Male","Female","Other"],
                                     state="readonly", font=("Consolas", 9))
        self.field_row(grid, "Gender", 2, col=1, widget=self.gender)

        self.nationality = self.field_row(grid, "Nationality", 3)
        self.address  = self.field_row(grid, "Address", 4)

        tk.Button(self, text="Save Record", **GREEN_BTN,
                  font=("Consolas", 10, "bold"), padx=20, pady=7,
                  command=self.save).pack(pady=20)

    def _fill(self, d):
        self.name.insert(0, d[1] or "")
        self.alias.insert(0, d[2] or "")
        self.age.insert(0, d[3] or "")
        self.gender.set(d[4] or "")
        self.nationality.insert(0, d[5] or "")
        self.address.insert(0, d[6] or "")

    def save(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required.")
            return
        vals = (name, self.alias.get().strip(),
                self.age.get().strip() or None,
                self.gender.get(), self.nationality.get().strip(),
                self.address.get().strip())
        conn = get_conn()
        if self.data:
            conn.execute("""UPDATE criminals SET name=?,alias=?,age=?,gender=?,
                            nationality=?,address=? WHERE id=?""",
                         vals + (self.data[0],))
        else:
            conn.execute("""INSERT INTO criminals(name,alias,age,gender,nationality,address)
                            VALUES(?,?,?,?,?,?)""", vals)
        conn.commit(); conn.close()
        self.parent_frame.refresh()
        self.destroy()

# ─────────────────────────────────────────────
#  CRIMES MODULE
# ─────────────────────────────────────────────

class CrimesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE)
        self._build()
        self.refresh()

    def _build(self):
        top = tk.Frame(self, bg=SURFACE)
        top.pack(fill="x", pady=(0, 10))
        styled_label(top, "CRIME RECORDS", 14, True, ACCENT).pack(side="left")

        bf = tk.Frame(top, bg=SURFACE)
        bf.pack(side="right")
        for text, style, cmd in [
            ("+ Log Crime", BTN_STYLE, self.add_dialog),
            ("✎ Edit", SECONDARY_BTN, self.edit_dialog),
        ]:
            tk.Button(bf, text=text, **style, font=("Consolas", 9, "bold"),
                      padx=12, pady=5, command=cmd).pack(side="left", padx=4)
        tk.Button(bf, text="✕ Delete", bg="#6e7681", fg=FG,
                  activebackground=ACCENT, relief="flat", cursor="hand2", bd=0,
                  font=("Consolas", 9, "bold"), padx=12, pady=5,
                  command=self.delete).pack(side="left", padx=4)

        # Filter bar
        ff = tk.Frame(self, bg=CARD, pady=8, padx=10)
        ff.pack(fill="x", pady=(0, 10))
        ff.configure(highlightthickness=1, highlightbackground=BORDER)
        tk.Label(ff, text="Status:", font=("Consolas", 9), bg=CARD, fg=FG_DIM).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        cb = ttk.Combobox(ff, textvariable=self.filter_var,
                          values=["All", "Under Investigation", "Solved", "Closed", "Pending"],
                          state="readonly", width=20, font=("Consolas", 9))
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda _: self.refresh())

        cols = ("ID","Criminal","Type","Location","Date","Severity","Status")
        widths = (40, 130, 110, 130, 90, 70, 130)
        self.tree = make_table(self, cols, widths)

    def refresh(self):
        f = self.filter_var.get()
        conn = get_conn()
        q = """SELECT c.id, cr.name, c.crime_type, c.location,
                      c.date_of_crime, c.severity, c.status
               FROM crimes c LEFT JOIN criminals cr ON c.criminal_id=cr.id"""
        if f != "All":
            rows = conn.execute(q + " WHERE c.status=?", (f,)).fetchall()
        else:
            rows = conn.execute(q).fetchall()
        conn.close()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in rows:
            tag = "solved" if r[6] == "Solved" else ""
            self.tree.insert("", "end", values=r, tags=(tag,))
        self.tree.tag_configure("solved", foreground=SUCCESS)

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a crime record.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def add_dialog(self): CrimeDialog(self, "Log Crime")
    def edit_dialog(self):
        cid = self._selected_id()
        if cid:
            conn = get_conn()
            row = conn.execute("SELECT * FROM crimes WHERE id=?", (cid,)).fetchone()
            conn.close()
            CrimeDialog(self, "Edit Crime", row)

    def delete(self):
        cid = self._selected_id()
        if cid and messagebox.askyesno("Confirm", "Delete this crime record?"):
            conn = get_conn()
            conn.execute("DELETE FROM crimes WHERE id=?", (cid,))
            conn.commit(); conn.close()
            self.refresh()

class CrimeDialog(Modal):
    def __init__(self, pf, title, data=None):
        super().__init__(pf.winfo_toplevel(), title, 580, 520)
        self.pf = pf; self.data = data
        self._build()
        if data: self._fill(data)

    def _build(self):
        tk.Label(self, text=self.title(), font=("Consolas", 12, "bold"),
                 bg=SURFACE, fg=ACCENT).pack(pady=(16, 10))
        grid = tk.Frame(self, bg=SURFACE)
        grid.pack(padx=24, pady=4, fill="both")
        grid.columnconfigure(1, weight=1); grid.columnconfigure(3, weight=1)

        # Criminal dropdown
        conn = get_conn()
        criminals = conn.execute("SELECT id, name FROM criminals").fetchall()
        conn.close()
        self.criminal_map = {f"{r[1]} (ID:{r[0]})": r[0] for r in criminals}
        crim_cb = ttk.Combobox(grid, values=list(self.criminal_map.keys()),
                               state="readonly", font=("Consolas", 9))
        self.field_row(grid, "Criminal *", 0, widget=crim_cb, span=3)
        self.criminal_cb = crim_cb

        self.crime_type = self.field_row(grid, "Crime Type *", 1)
        self.location   = self.field_row(grid, "Location", 2)
        self.date       = self.field_row(grid, "Date (YYYY-MM-DD)", 3)

        self.severity = ttk.Combobox(grid, values=["Low","Medium","High","Critical"],
                                     state="readonly", font=("Consolas", 9))
        self.field_row(grid, "Severity", 4, col=0, widget=self.severity)

        self.status = ttk.Combobox(grid,
                                   values=["Under Investigation","Pending","Solved","Closed"],
                                   state="readonly", font=("Consolas", 9))
        self.field_row(grid, "Status", 4, col=1, widget=self.status)

        tk.Label(grid, text="Description", font=("Consolas", 9),
                 bg=SURFACE, fg=FG_DIM).grid(row=5, column=0, sticky="nw", pady=4)
        self.desc = tk.Text(grid, height=4, bg=ENTRY_BG, fg=FG,
                            insertbackground=FG, relief="flat",
                            font=("Consolas", 9))
        self.desc.grid(row=5, column=1, columnspan=3, sticky="ew", pady=4)

        tk.Button(self, text="Save Crime Record", **GREEN_BTN,
                  font=("Consolas", 10, "bold"), padx=20, pady=7,
                  command=self.save).pack(pady=16)

    def _fill(self, d):
        for k, v in self.criminal_map.items():
            if v == d[1]:
                self.criminal_cb.set(k); break
        self.crime_type.insert(0, d[2] or "")
        self.desc.insert("1.0", d[3] or "")
        self.location.insert(0, d[4] or "")
        self.date.insert(0, d[5] or "")
        self.status.set(d[6] or "")
        self.severity.set(d[7] or "")

    def save(self):
        ct = self.crime_type.get().strip()
        if not ct:
            messagebox.showerror("Error", "Crime Type is required."); return
        crim_key = self.criminal_cb.get()
        crim_id = self.criminal_map.get(crim_key)
        vals = (crim_id, ct, self.desc.get("1.0", "end").strip(),
                self.location.get().strip(), self.date.get().strip(),
                self.status.get() or "Under Investigation",
                self.severity.get() or "Medium")
        conn = get_conn()
        if self.data:
            conn.execute("""UPDATE crimes SET criminal_id=?,crime_type=?,description=?,
                            location=?,date_of_crime=?,status=?,severity=? WHERE id=?""",
                         vals + (self.data[0],))
        else:
            conn.execute("""INSERT INTO crimes(criminal_id,crime_type,description,
                            location,date_of_crime,status,severity) VALUES(?,?,?,?,?,?,?)""",
                         vals)
        conn.commit(); conn.close()
        self.pf.refresh(); self.destroy()

# ─────────────────────────────────────────────
#  OFFICERS MODULE
# ─────────────────────────────────────────────

class OfficersFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE)
        self._build(); self.refresh()

    def _build(self):
        top = tk.Frame(self, bg=SURFACE)
        top.pack(fill="x", pady=(0, 10))
        styled_label(top, "OFFICERS", 14, True, ACCENT2).pack(side="left")
        bf = tk.Frame(top, bg=SURFACE); bf.pack(side="right")
        tk.Button(bf, text="+ Add Officer", **SECONDARY_BTN,
                  font=("Consolas", 9, "bold"), padx=12, pady=5,
                  command=self.add_dialog).pack(side="left", padx=4)
        tk.Button(bf, text="✎ Edit", **BTN_STYLE,
                  font=("Consolas", 9, "bold"), padx=12, pady=5,
                  command=self.edit_dialog).pack(side="left", padx=4)
        tk.Button(bf, text="✕ Delete", bg="#6e7681", fg=FG,
                  activebackground=ACCENT, relief="flat", cursor="hand2", bd=0,
                  font=("Consolas", 9, "bold"), padx=12, pady=5,
                  command=self.delete).pack(side="left", padx=4)

        cols = ("ID", "Name", "Badge No.", "Rank", "Department", "Contact", "Added")
        widths = (40, 140, 90, 90, 120, 110, 120)
        self.tree = make_table(self, cols, widths)

    def refresh(self):
        conn = get_conn()
        rows = conn.execute("SELECT id,name,badge_no,rank,department,contact,created_at FROM officers").fetchall()
        conn.close()
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows: self.tree.insert("", "end", values=r)

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select an officer."); return None
        return self.tree.item(sel[0])["values"][0]

    def add_dialog(self): OfficerDialog(self, "Add Officer")
    def edit_dialog(self):
        oid = self._selected_id()
        if oid:
            conn = get_conn()
            row = conn.execute("SELECT * FROM officers WHERE id=?", (oid,)).fetchone()
            conn.close(); OfficerDialog(self, "Edit Officer", row)

    def delete(self):
        oid = self._selected_id()
        if oid and messagebox.askyesno("Confirm", "Delete this officer?"):
            conn = get_conn()
            conn.execute("DELETE FROM officers WHERE id=?", (oid,))
            conn.commit(); conn.close(); self.refresh()

class OfficerDialog(Modal):
    def __init__(self, pf, title, data=None):
        super().__init__(pf.winfo_toplevel(), title, 520, 380)
        self.pf = pf; self.data = data
        self._build()
        if data: self._fill(data)

    def _build(self):
        tk.Label(self, text=self.title(), font=("Consolas", 12, "bold"),
                 bg=SURFACE, fg=ACCENT2).pack(pady=(16, 10))
        grid = tk.Frame(self, bg=SURFACE)
        grid.pack(padx=24, pady=4, fill="both")
        grid.columnconfigure(1, weight=1); grid.columnconfigure(3, weight=1)
        self.name   = self.field_row(grid, "Full Name *", 0)
        self.badge  = self.field_row(grid, "Badge No. *", 1)
        self.rank   = self.field_row(grid, "Rank", 2)
        self.dept   = self.field_row(grid, "Department", 3)
        self.contact = self.field_row(grid, "Contact", 4)
        tk.Button(self, text="Save Officer", **GREEN_BTN,
                  font=("Consolas", 10, "bold"), padx=20, pady=7,
                  command=self.save).pack(pady=20)

    def _fill(self, d):
        self.name.insert(0, d[1] or "")
        self.badge.insert(0, d[2] or "")
        self.rank.insert(0, d[3] or "")
        self.dept.insert(0, d[4] or "")
        self.contact.insert(0, d[5] or "")

    def save(self):
        name = self.name.get().strip(); badge = self.badge.get().strip()
        if not name or not badge:
            messagebox.showerror("Error", "Name and Badge No. are required."); return
        vals = (name, badge, self.rank.get().strip(),
                self.dept.get().strip(), self.contact.get().strip())
        conn = get_conn()
        try:
            if self.data:
                conn.execute("""UPDATE officers SET name=?,badge_no=?,rank=?,
                                department=?,contact=? WHERE id=?""", vals+(self.data[0],))
            else:
                conn.execute("""INSERT INTO officers(name,badge_no,rank,department,contact)
                                VALUES(?,?,?,?,?)""", vals)
            conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Badge No. already exists.")
            return
        finally:
            conn.close()
        self.pf.refresh(); self.destroy()

# ─────────────────────────────────────────────
#  CASES MODULE
# ─────────────────────────────────────────────

class CasesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE)
        self._build(); self.refresh()

    def _build(self):
        top = tk.Frame(self, bg=SURFACE)
        top.pack(fill="x", pady=(0, 10))
        styled_label(top, "CASE MANAGEMENT", 14, True, WARNING).pack(side="left")
        bf = tk.Frame(top, bg=SURFACE); bf.pack(side="right")
        for text, style, cmd in [
            ("+ New Case", {"bg": WARNING, "fg": "#000", "activebackground": "#b08000",
                            "relief": "flat", "cursor": "hand2", "bd": 0}, self.add_dialog),
            ("✎ Edit", SECONDARY_BTN, self.edit_dialog),
        ]:
            tk.Button(bf, text=text, **style, font=("Consolas", 9, "bold"),
                      padx=12, pady=5, command=cmd).pack(side="left", padx=4)
        tk.Button(bf, text="✕ Delete", bg="#6e7681", fg=FG,
                  activebackground=ACCENT, relief="flat", cursor="hand2", bd=0,
                  font=("Consolas", 9, "bold"), padx=12, pady=5,
                  command=self.delete).pack(side="left", padx=4)

        cols = ("ID","Case No.","Title","Crime","Officer","Status","Priority","Opened")
        widths = (40, 90, 150, 90, 110, 90, 70, 100)
        self.tree = make_table(self, cols, widths)

    def refresh(self):
        conn = get_conn()
        rows = conn.execute("""
            SELECT ca.id, ca.case_no, ca.title,
                   cr.crime_type, o.name, ca.status, ca.priority, ca.opened_date
            FROM cases ca
            LEFT JOIN crimes cr ON ca.crime_id = cr.id
            LEFT JOIN officers o ON ca.officer_id = o.id
        """).fetchall()
        conn.close()
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows:
            tag = "closed" if r[5] == "Closed" else "open" if r[5] == "Open" else ""
            self.tree.insert("", "end", values=r, tags=(tag,))
        self.tree.tag_configure("closed", foreground=FG_DIM)
        self.tree.tag_configure("open", foreground=SUCCESS)

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a case."); return None
        return self.tree.item(sel[0])["values"][0]

    def add_dialog(self): CaseDialog(self, "New Case")
    def edit_dialog(self):
        cid = self._selected_id()
        if cid:
            conn = get_conn()
            row = conn.execute("SELECT * FROM cases WHERE id=?", (cid,)).fetchone()
            conn.close(); CaseDialog(self, "Edit Case", row)

    def delete(self):
        cid = self._selected_id()
        if cid and messagebox.askyesno("Confirm", "Delete this case?"):
            conn = get_conn()
            conn.execute("DELETE FROM cases WHERE id=?", (cid,))
            conn.commit(); conn.close(); self.refresh()

class CaseDialog(Modal):
    def __init__(self, pf, title, data=None):
        super().__init__(pf.winfo_toplevel(), title, 580, 500)
        self.pf = pf; self.data = data
        self._build()
        if data: self._fill(data)

    def _build(self):
        tk.Label(self, text=self.title(), font=("Consolas", 12, "bold"),
                 bg=SURFACE, fg=WARNING).pack(pady=(16, 10))
        grid = tk.Frame(self, bg=SURFACE)
        grid.pack(padx=24, pady=4, fill="both")
        grid.columnconfigure(1, weight=1); grid.columnconfigure(3, weight=1)

        self.case_no = self.field_row(grid, "Case No. *", 0)
        self.title_e = self.field_row(grid, "Title *", 1)

        conn = get_conn()
        crimes = conn.execute("SELECT id, crime_type FROM crimes").fetchall()
        officers = conn.execute("SELECT id, name FROM officers").fetchall()
        conn.close()
        self.crime_map = {f"{r[1]} (ID:{r[0]})": r[0] for r in crimes}
        self.officer_map = {f"{r[1]} (ID:{r[0]})": r[0] for r in officers}

        crime_cb = ttk.Combobox(grid, values=list(self.crime_map.keys()),
                                state="readonly", font=("Consolas", 9))
        self.field_row(grid, "Crime", 2, widget=crime_cb, span=3)
        self.crime_cb = crime_cb

        officer_cb = ttk.Combobox(grid, values=list(self.officer_map.keys()),
                                  state="readonly", font=("Consolas", 9))
        self.field_row(grid, "Assigned Officer", 3, widget=officer_cb, span=3)
        self.officer_cb = officer_cb

        self.status = ttk.Combobox(grid, values=["Open","Under Investigation","Pending","Closed"],
                                   state="readonly", font=("Consolas", 9))
        self.field_row(grid, "Status", 4, col=0, widget=self.status)

        self.priority = ttk.Combobox(grid, values=["Low","Medium","High","Critical"],
                                     state="readonly", font=("Consolas", 9))
        self.field_row(grid, "Priority", 4, col=1, widget=self.priority)

        self.opened_date = self.field_row(grid, "Opened Date", 5)

        tk.Label(grid, text="Description", font=("Consolas", 9),
                 bg=SURFACE, fg=FG_DIM).grid(row=6, column=0, sticky="nw", pady=4)
        self.desc = tk.Text(grid, height=3, bg=ENTRY_BG, fg=FG,
                            insertbackground=FG, relief="flat", font=("Consolas", 9))
        self.desc.grid(row=6, column=1, columnspan=3, sticky="ew", pady=4)

        tk.Button(self, text="Save Case", **GREEN_BTN,
                  font=("Consolas", 10, "bold"), padx=20, pady=7,
                  command=self.save).pack(pady=12)

    def _fill(self, d):
        self.case_no.insert(0, d[1] or "")
        for k, v in self.crime_map.items():
            if v == d[2]: self.crime_cb.set(k); break
        for k, v in self.officer_map.items():
            if v == d[3]: self.officer_cb.set(k); break
        self.title_e.insert(0, d[4] or "")
        self.desc.insert("1.0", d[5] or "")
        self.status.set(d[6] or "")
        self.priority.set(d[7] or "")
        self.opened_date.insert(0, d[8] or "")

    def save(self):
        cn = self.case_no.get().strip(); t = self.title_e.get().strip()
        if not cn or not t:
            messagebox.showerror("Error", "Case No. and Title are required."); return
        crime_id = self.crime_map.get(self.crime_cb.get())
        officer_id = self.officer_map.get(self.officer_cb.get())
        vals = (cn, crime_id, officer_id, t,
                self.desc.get("1.0","end").strip(),
                self.status.get() or "Open",
                self.priority.get() or "Medium",
                self.opened_date.get().strip())
        conn = get_conn()
        try:
            if self.data:
                conn.execute("""UPDATE cases SET case_no=?,crime_id=?,officer_id=?,title=?,
                                description=?,status=?,priority=?,opened_date=? WHERE id=?""",
                             vals + (self.data[0],))
            else:
                conn.execute("""INSERT INTO cases(case_no,crime_id,officer_id,title,
                                description,status,priority,opened_date) VALUES(?,?,?,?,?,?,?,?)""", vals)
            conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Case No. already exists."); return
        finally:
            conn.close()
        self.pf.refresh(); self.destroy()

# ─────────────────────────────────────────────
#  EVIDENCE MODULE
# ─────────────────────────────────────────────

class EvidenceFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE)
        self._build(); self.refresh()

    def _build(self):
        top = tk.Frame(self, bg=SURFACE)
        top.pack(fill="x", pady=(0, 10))
        styled_label(top, "EVIDENCE VAULT", 14, True, SUCCESS).pack(side="left")
        bf = tk.Frame(top, bg=SURFACE); bf.pack(side="right")
        tk.Button(bf, text="+ Add Evidence", **GREEN_BTN,
                  font=("Consolas", 9, "bold"), padx=12, pady=5,
                  command=self.add_dialog).pack(side="left", padx=4)
        tk.Button(bf, text="✕ Delete", bg="#6e7681", fg=FG,
                  activebackground=ACCENT, relief="flat", cursor="hand2", bd=0,
                  font=("Consolas", 9, "bold"), padx=12, pady=5,
                  command=self.delete).pack(side="left", padx=4)

        cols = ("ID","Case","Type","Description","Location","Collected By","Date")
        widths = (40, 90, 90, 170, 120, 110, 100)
        self.tree = make_table(self, cols, widths)

    def refresh(self):
        conn = get_conn()
        rows = conn.execute("""
            SELECT e.id, ca.case_no, e.type, e.description,
                   e.location, e.collected_by, e.date_collected
            FROM evidence e LEFT JOIN cases ca ON e.case_id=ca.id
        """).fetchall()
        conn.close()
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows: self.tree.insert("", "end", values=r)

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select an evidence entry."); return None
        return self.tree.item(sel[0])["values"][0]

    def add_dialog(self): EvidenceDialog(self, "Add Evidence")

    def delete(self):
        eid = self._selected_id()
        if eid and messagebox.askyesno("Confirm", "Delete this evidence record?"):
            conn = get_conn()
            conn.execute("DELETE FROM evidence WHERE id=?", (eid,))
            conn.commit(); conn.close(); self.refresh()

class EvidenceDialog(Modal):
    def __init__(self, pf, title):
        super().__init__(pf.winfo_toplevel(), title, 540, 420)
        self.pf = pf; self._build()

    def _build(self):
        tk.Label(self, text="Add Evidence", font=("Consolas", 12, "bold"),
                 bg=SURFACE, fg=SUCCESS).pack(pady=(16, 10))
        grid = tk.Frame(self, bg=SURFACE)
        grid.pack(padx=24, pady=4, fill="both")
        grid.columnconfigure(1, weight=1); grid.columnconfigure(3, weight=1)

        conn = get_conn()
        cases = conn.execute("SELECT id, case_no FROM cases").fetchall()
        conn.close()
        self.case_map = {f"{r[1]} (ID:{r[0]})": r[0] for r in cases}
        case_cb = ttk.Combobox(grid, values=list(self.case_map.keys()),
                               state="readonly", font=("Consolas", 9))
        self.field_row(grid, "Case *", 0, widget=case_cb, span=3)
        self.case_cb = case_cb

        self.etype = self.field_row(grid, "Evidence Type *", 1)
        self.location = self.field_row(grid, "Storage Location", 2)
        self.collected_by = self.field_row(grid, "Collected By", 3)
        self.date = self.field_row(grid, "Date Collected", 4)

        tk.Label(grid, text="Description", font=("Consolas", 9),
                 bg=SURFACE, fg=FG_DIM).grid(row=5, column=0, sticky="nw", pady=4)
        self.desc = tk.Text(grid, height=3, bg=ENTRY_BG, fg=FG,
                            insertbackground=FG, relief="flat", font=("Consolas", 9))
        self.desc.grid(row=5, column=1, columnspan=3, sticky="ew", pady=4)

        tk.Button(self, text="Save Evidence", **GREEN_BTN,
                  font=("Consolas", 10, "bold"), padx=20, pady=7,
                  command=self.save).pack(pady=12)

    def save(self):
        et = self.etype.get().strip()
        if not et:
            messagebox.showerror("Error", "Evidence Type is required."); return
        case_id = self.case_map.get(self.case_cb.get())
        vals = (case_id, et, self.desc.get("1.0","end").strip(),
                self.location.get().strip(), self.collected_by.get().strip(),
                self.date.get().strip())
        conn = get_conn()
        conn.execute("""INSERT INTO evidence(case_id,type,description,location,
                        collected_by,date_collected) VALUES(?,?,?,?,?,?)""", vals)
        conn.commit(); conn.close()
        self.pf.refresh(); self.destroy()

# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────

class DashboardFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE)
        self._build()

    def _build(self):
        styled_label(self, "DASHBOARD — OVERVIEW", 14, True, ACCENT).pack(anchor="w", pady=(0,16))
        self.stats_frame = tk.Frame(self, bg=SURFACE)
        self.stats_frame.pack(fill="x")
        self.refresh()

    def _stat_card(self, parent, title, value, color):
        c = card_frame(parent, padx=20, pady=16)
        c.pack(side="left", expand=True, fill="both", padx=8, pady=4)
        tk.Label(c, text=str(value), font=("Consolas", 32, "bold"),
                 bg=CARD, fg=color).pack()
        tk.Label(c, text=title, font=("Consolas", 9),
                 bg=CARD, fg=FG_DIM).pack()

    def refresh(self):
        for w in self.stats_frame.winfo_children(): w.destroy()
        conn = get_conn()
        n_criminals = conn.execute("SELECT COUNT(*) FROM criminals").fetchone()[0]
        n_crimes    = conn.execute("SELECT COUNT(*) FROM crimes").fetchone()[0]
        n_officers  = conn.execute("SELECT COUNT(*) FROM officers").fetchone()[0]
        n_cases     = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        n_open      = conn.execute("SELECT COUNT(*) FROM cases WHERE status='Open'").fetchone()[0]
        n_evidence  = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
        conn.close()

        for title, val, color in [
            ("CRIMINALS", n_criminals, ACCENT),
            ("CRIMES LOGGED", n_crimes, WARNING),
            ("OFFICERS", n_officers, ACCENT2),
            ("TOTAL CASES", n_cases, SUCCESS),
            ("OPEN CASES", n_open, ACCENT),
            ("EVIDENCE", n_evidence, FG_DIM),
        ]:
            self._stat_card(self.stats_frame, title, val, color)

        # Recent crimes table
        styled_label(self, "RECENT CRIMES", 11, True, FG_DIM).pack(anchor="w",
                                                                     pady=(24, 6))
        conn = get_conn()
        recent = conn.execute("""
            SELECT c.crime_type, cr.name, c.location, c.status, c.date_of_crime
            FROM crimes c LEFT JOIN criminals cr ON c.criminal_id=cr.id
            ORDER BY c.created_at DESC LIMIT 8
        """).fetchall()
        conn.close()

        cols = ("Crime Type", "Criminal", "Location", "Status", "Date")
        widths = (120, 130, 130, 130, 100)
        self.recent_tree = make_table(self, cols, widths)
        for r in recent:
            self.recent_tree.insert("", "end", values=r)

# ─────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Crime Management System")
        self.configure(bg=BG)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(1280, sw-80), min(820, sh-80)
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(900, 600)
        self._build_sidebar()
        self._build_content()
        self.show_tab("Dashboard")

    def _sidebar_btn(self, text, icon, key):
        f = tk.Frame(self.sidebar, bg=BG, cursor="hand2")
        f.pack(fill="x", pady=2)
        lbl = tk.Label(f, text=f"  {icon}  {text}", font=("Consolas", 10),
                       bg=BG, fg=FG_DIM, anchor="w", padx=8, pady=10)
        lbl.pack(fill="x")
        def on_enter(e):
            if self.active_tab != key:
                lbl.config(bg=CARD, fg=FG)
                f.config(bg=CARD)
        def on_leave(e):
            if self.active_tab != key:
                lbl.config(bg=BG, fg=FG_DIM)
                f.config(bg=BG)
        def on_click(e): self.show_tab(key)
        for w in (f, lbl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)
        self.nav_items[key] = (f, lbl)

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=BG, width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo area
        logo = tk.Frame(self.sidebar, bg=ACCENT, height=60)
        logo.pack(fill="x")
        logo.pack_propagate(False)
        tk.Label(logo, text="⚖  CMS", font=("Consolas", 16, "bold"),
                 bg=ACCENT, fg="#ffffff").pack(expand=True)

        tk.Label(self.sidebar, text="NAVIGATION",
                 font=("Consolas", 8), bg=BG, fg=FG_DIM,
                 padx=12).pack(anchor="w", pady=(14, 4))

        self.nav_items = {}
        self.active_tab = None
        self._sidebar_btn("Dashboard", "◈", "Dashboard")
        self._sidebar_btn("Criminals", "👤", "Criminals")
        self._sidebar_btn("Crimes", "⚠", "Crimes")
        self._sidebar_btn("Officers", "🛡", "Officers")
        self._sidebar_btn("Cases", "📁", "Cases")
        self._sidebar_btn("Evidence", "🔬", "Evidence")

        # Footer
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", side="bottom", pady=0)
        tk.Label(self.sidebar, text="Crime Mgmt System v1.0",
                 font=("Consolas", 7), bg=BG, fg=FG_DIM).pack(side="bottom", pady=6)

    def _build_content(self):
        self.content = tk.Frame(self, bg=SURFACE)
        self.content.pack(side="left", fill="both", expand=True)
        # Header bar
        self.header = tk.Frame(self.content, bg=SURFACE, height=50)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        tk.Frame(self.content, bg=BORDER, height=1).pack(fill="x")
        self.header_label = tk.Label(self.header, text="",
                                     font=("Consolas", 13, "bold"),
                                     bg=SURFACE, fg=FG, padx=20)
        self.header_label.pack(side="left", pady=12)
        self.date_label = tk.Label(self.header, text=datetime.now().strftime("%A, %d %B %Y"),
                                   font=("Consolas", 9), bg=SURFACE, fg=FG_DIM, padx=20)
        self.date_label.pack(side="right")
        # Page area
        self.page = tk.Frame(self.content, bg=SURFACE)
        self.page.pack(fill="both", expand=True, padx=20, pady=16)
        self.pages = {}

    def show_tab(self, key):
        if self.active_tab:
            f, lbl = self.nav_items[self.active_tab]
            lbl.config(bg=BG, fg=FG_DIM); f.config(bg=BG)
        self.active_tab = key
        f, lbl = self.nav_items[key]
        lbl.config(bg=CARD, fg=ACCENT); f.config(bg=CARD)
        self.header_label.config(text=key.upper())

        for w in self.page.winfo_children(): w.pack_forget()

        if key not in self.pages:
            frame_map = {
                "Dashboard": DashboardFrame,
                "Criminals": CriminalsFrame,
                "Crimes":    CrimesFrame,
                "Officers":  OfficersFrame,
                "Cases":     CasesFrame,
                "Evidence":  EvidenceFrame,
            }
            self.pages[key] = frame_map[key](self.page)
        else:
            if hasattr(self.pages[key], "refresh"):
                self.pages[key].refresh()

        self.pages[key].pack(fill="both", expand=True)

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()
