#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BSM 筆順碼輸入法 v2.0.1 — 最終修復版
=========================================

作者: Community Rebuild (2026)
版本: 2.0.1

鍵位映射:
  - (減號)   → 逐個碼清（退格）
  + (加號)   → 一次過清空所有編碼
  BackSpace  → 逐個碼清（退格）
  =          → 上一頁候選字
  /          → 下一頁候選字
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
import io
import json

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

APP_NAME = "BSM 筆順碼輸入法"
APP_VERSION = "2.0.1"

STROKE_MAP = {
    '0': '組合型', '1': '橫(㇐)', '2': '豎(㇑)', '3': '撇(㇒)',
    '4': '點捺(㇏)', '5': '上挑鉤(㇀)', '6': '下挑鉤(㇂)',
    '7': '交叉(㇥)', '8': '人八型', '9': '方框型',
}

DEFAULT_DB_PATHS = [
    r"C:\Users\timch\AppData\Local\BSM_InputMethod\bsm.db",
    r"C:\Users\timch\.agnes\temporary\2026-07-24\20260724_1\work\bsm_final.db",
]
USER_DB_PATH = os.path.join(os.environ.get("LOCALAPPDATA", ""), "BSM_InputMethod", "user_words.db")


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.user_conn = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"DB Error: {e}")
            return False
        if not os.path.exists(USER_DB_PATH):
            conn = sqlite3.connect(USER_DB_PATH)
            conn.execute("""CREATE TABLE IF NOT EXISTS user_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(6), word NVARCHAR(10), frequency INTEGER DEFAULT 1000)""")
            conn.execute("CREATE INDEX idx_user_code ON user_words(code)")
            conn.commit()
            conn.close()
        try:
            self.user_conn = sqlite3.connect(USER_DB_PATH)
            self.user_cursor = self.user_conn.cursor()
        except Exception:
            pass
        return True

    def query_candidates(self, code, page=0, page_size=9):
        if not code:
            return [], 0
        min_len = max(len(code) - 1, 1)
        sql = "SELECT code, word, frequency FROM ime WHERE code LIKE ? AND length(code) >= ? GROUP BY word ORDER BY frequency ASC LIMIT ? OFFSET ?"
        self.cursor.execute(sql, (code + '%', min_len, page_size, page * page_size))
        results = self.cursor.fetchall()
        try:
            self.user_cursor.execute(sql, (code + '%', min_len, page_size, page * page_size))
            user_results = self.user_cursor.fetchall()
            seen = set(r[1] for r in results)
            for r in user_results:
                if r[1] not in seen:
                    results.append(r)
        except Exception:
            pass
        cnt_sql = "SELECT COUNT(DISTINCT word) FROM ime WHERE code LIKE ? AND length(code) >= ?"
        self.cursor.execute(cnt_sql, (code + '%', min_len))
        total = self.cursor.fetchone()[0]
        try:
            self.user_cursor.execute(cnt_sql, (code + '%', min_len))
            total += self.user_cursor.fetchone()[0]
        except Exception:
            pass
        return results, total

    def lookup_word(self, char):
        self.cursor.execute("SELECT DISTINCT code FROM ime WHERE word=? ORDER BY LENGTH(code), frequency LIMIT 5", (char,))
        return [r[0] for r in self.cursor.fetchall()]

    def add_user_word(self, code, word, frequency=1000):
        try:
            self.user_cursor.execute("INSERT OR REPLACE INTO user_words (code, word, frequency) VALUES (?, ?, ?)", (code, word, frequency))
            self.user_conn.commit()
            return True
        except Exception:
            return False

    def get_word_frequency(self, char):
        self.cursor.execute("SELECT MIN(frequency) FROM ime WHERE word=?", (char,))
        r = self.cursor.fetchone()
        return r[0] if r else 6000

    def close(self):
        if self.conn: self.conn.close()
        if self.user_conn: self.user_conn.close()


class BSMApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("750x600")
        self.minsize(600, 450)
        self.db_path = self._find_dictionary()
        self.db = DatabaseManager(self.db_path)
        if not self.db.connect():
            messagebox.showerror("錯誤", f"無法打開詞庫文件\n{self.db_path}")
            self.destroy()
            return
        self.input_buffer = ""
        self.candidates = []
        self.total_pages = 0
        self.current_page = 0
        self.selection_mode = False
        self.committed_text = ""
        self.page_size = 9
        self._setup_ui()
        self.bind('<Key>', self._on_key_press)
        self.status_var = tk.StringVar(value=f"[OK] 詞庫已加載: {os.path.basename(self.db_path)}")
        self.statusbar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _find_dictionary(self):
        config_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "BSM_InputMethod", "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                db_path = config.get('dictionary_path')
                if db_path and os.path.exists(db_path):
                    return db_path
            except Exception:
                pass
        for path in DEFAULT_DB_PATHS:
            if os.path.exists(path):
                return path
        pen_dir = r"D:\Pen"
        if os.path.exists(pen_dir):
            for root, dirs, files in os.walk(pen_dir):
                for f in files:
                    if f.endswith('.db'):
                        return os.path.join(root, f)
        return DEFAULT_DB_PATHS[0] if DEFAULT_DB_PATHS else ""

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 已輸入文字（可編輯）
        top_frame = ttk.LabelFrame(main_frame, text="已輸入文字（可直接編輯）", padding="5")
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.committed_text_widget = tk.Text(top_frame, height=6, width=80, font=("Microsoft JhengHei", 12), bg="#ffffff", relief=tk.SUNKEN, wrap=tk.WORD)
        self.committed_text_widget.pack(fill=tk.BOTH, expand=True)
        self.committed_text_widget.insert('1.0', '')

        # 編碼輸入
        mid_frame = ttk.LabelFrame(main_frame, text="當前編碼輸入", padding="5")
        mid_frame.pack(fill=tk.X, pady=(0, 5))
        input_label = ttk.Label(mid_frame, text="輸入:", font=("Microsoft JhengHei", 9))
        input_label.pack(anchor=tk.W)
        self.input_entry = ttk.Entry(mid_frame, font=("Consolas", 14, "bold"), width=30)
        self.input_entry.pack(fill=tk.X, pady=(0, 3))
        self.input_entry.focus_set()
        self.stroke_display = tk.Text(mid_frame, height=1, width=70, font=("Microsoft JhengHei", 8))
        self.stroke_display.pack(fill=tk.X)
        self.stroke_display.insert('1.0', self._format_stroke_map())
        self.stroke_display.config(state=tk.DISABLED)

        # 候選字
        bot_frame = ttk.LabelFrame(main_frame, text="候選字（點擊或按數字選擇）", padding="5")
        bot_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.page_var = tk.StringVar(value="第 1 / 1 頁")
        ttk.Label(bot_frame, textvariable=self.page_var, font=("Microsoft JhengHei", 9)).pack(anchor=tk.W)
        self.candidates_listbox = tk.Listbox(bot_frame, height=8, width=70, font=("Microsoft JhengHei", 11), selectmode=tk.SINGLE, bg="#fafafa", selectbackground="#4a90d9", selectforeground="white")
        self.candidates_listbox.pack(fill=tk.BOTH, expand=True, pady=(2, 2))
        self.candidates_listbox.bind('<Double-Button-1>', self._on_double_click)
        self.candidates_listbox.bind('<Return>', lambda e: self._key_enter())

        # 底部按鈕
        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X)
        ttk.Button(ctrl_frame, text="查詢編碼", command=self._show_lookup_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="添加詞庫", command=self._show_add_word_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="清空編碼", command=self._clear_input).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="退出", command=self._on_closing).pack(side=tk.RIGHT, padx=2)

    def _format_stroke_map(self):
        return ' '.join(f"{k}={STROKE_MAP[str(k)][:3]}" for k in range(10))

    def _update_input_display(self):
        self.input_entry.delete(0, tk.END)
        if self.input_buffer:
            marker = ""
            for ch in self.input_buffer:
                if ch in STROKE_MAP:
                    marker += f"{ch}({STROKE_MAP[ch][0]}) "
                else:
                    marker += ch + " "
            self.input_entry.insert(0, marker.strip())
        else:
            self.input_entry.insert(0, '(空)')
        self.input_entry.config(foreground='#333' if self.input_buffer else '#999')

    def _update_candidates(self):
        self.candidates, self.total_pages = self.db.query_candidates(self.input_buffer, self.current_page, self.page_size)
        self.candidates_listbox.delete(0, tk.END)
        if not self.candidates:
            self.candidates_listbox.insert(tk.END, "(無匹配)")
        else:
            for i, (code, word, freq) in enumerate(self.candidates):
                self.candidates_listbox.insert(tk.END, f"{i+1}. {word} [{code}]")
        if self.total_pages > 0:
            self.page_var.set(f"第 {self.current_page + 1} / {self.total_pages} 頁 ({len(self.candidates)} 個候選字)")
        else:
            self.page_var.set("第 0 / 0 頁")

    def _commit_text(self, text):
        self.committed_text += text
        self.committed_text_widget.insert(tk.END, text)
        self.committed_text_widget.see(tk.END)
        self.input_buffer = ""
        self.candidates = []
        self.current_page = 0
        self.selection_mode = False
        self._update_input_display()
        self._update_candidates()
        self.status_var.set(f"已輸入: '{text}'")

    def _on_key_press(self, event):
        key = event.keysym
        char = event.char

        # 數字鍵
        if char.isdigit() and len(char) == 1:
            self._append_digit(char)
            return "break"

        # - 減號：逐個碼清（退格）
        if char == '-' or key in ('minus', 'KP_Subtract'):
            self._key_minus()
            return "break"

        # + 加號：一次過清空
        if char == '+':  # + 一次過清空
            self._key_clear_all()
            return "break"

        # = 上一頁
        if char == '=' or key == 'equal':
            self._key_equals()
            return "break"

        # / 下一頁
        if char == '/' or key in ('slash', 'KP_Divide'):
            self._key_slash()
            return "break"

        # Enter / Space：確認輸入
        if key in ('Return', 'space', 'KP_Enter'):
            self._key_enter()
            return "break"

        # Esc / Clear：全部清除
        if key in ('Escape', 'Clear'):
            self._clear_all()
            return "break"

        # BackSpace：逐個碼清
        if key == 'BackSpace':
            self._key_backspace()
            return "break"

        # 萬用鍵
        if char == '*' or key == 'asterisk':
            self._key_wildcard()
            return "break"

        # 選字模式
        if char == '.' or key == 'period':
            self._key_dot()
            return "break"

        if self.selection_mode and char.isdigit() and int(char) <= 9:
            self._select_candidate(int(char) - 1)
            return "break"

        return None

    def _append_digit(self, digit):
        if self.selection_mode:
            self._select_candidate(int(digit) - 1)
            return
        if len(self.input_buffer) >= 6:
            self.bell()
            return
        self.input_buffer += digit
        self.current_page = 0
        self.selection_mode = False
        self._update_input_display()
        self._update_candidates()
        if self.candidates:
            self.status_var.set(f"輸入: '{digit}' → '{self.candidates[0][1]}'")
        else:
            self.status_var.set(f"輸入: '{digit}' → 無匹配")

    def _key_wildcard(self):
        if len(self.input_buffer) >= 6:
            self.bell()
            return
        if self.input_buffer:
            self.input_buffer = self.input_buffer[:-1] + '*'
        else:
            self.input_buffer = '*'
        self.current_page = 0
        self._update_input_display()
        self._update_candidates()
        self.status_var.set(f"萬用鍵: '{self.input_buffer}'")

    def _key_dot(self):
        self.selection_mode = True
        if self.candidates:
            self.status_var.set(f"選字模式: {len(self.candidates)} 個候選字 (按 1-9 選擇)")
        else:
            self.status_var.set("選字模式: 無候選字")

    def _key_minus(self):
        """減號 -: 逐個碼清（退格）"""
        if self.selection_mode:
            self.selection_mode = False
            self.status_var.set("退出選字模式")
            return
        if not self.input_buffer:
            return
        self.input_buffer = self.input_buffer[:-1]
        self.current_page = 0
        self.selection_mode = False
        self._update_input_display()
        self._update_candidates()
        if self.candidates:
            self.status_var.set(f"退格: '{self.input_buffer}' → '{self.candidates[0][1]}'")
        else:
            self.status_var.set(f"退格: '{self.input_buffer}' → 無匹配")

    def _key_backspace(self):
        """BackSpace 鍵：同 -，逐個碼清"""
        self._key_minus()

    def _key_clear_all(self):
        """加號 KP_Add +: 一次過清空所有編碼"""
        if self.selection_mode:
            self.selection_mode = False
            self.status_var.set("退出選字模式")
            return
        if not self.input_buffer:
            return
        self.input_buffer = ""
        self.current_page = 0
        self.selection_mode = False
        self._update_input_display()
        self._update_candidates()
        self.status_var.set("已清空所有編碼")

    def _key_equals(self):
        if self.current_page > 0:
            self.current_page -= 1
        else:
            self.current_page = max(0, self.total_pages - 1)
        self._update_candidates()
        self.status_var.set(f"上一頁: {self.current_page + 1}/{self.total_pages}")

    def _key_slash(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
        else:
            self.current_page = 0
        self._update_candidates()
        self.status_var.set(f"下一頁: {self.current_page + 1}/{self.total_pages}")

    def _key_enter(self):
        if self.selection_mode:
            self._select_candidate(0)
        elif self.candidates:
            word = self.candidates[0][1]
            self._commit_text(word)
        else:
            self.bell()

    def _select_candidate(self, index):
        if 0 <= index < len(self.candidates):
            word = self.candidates[index][1]
            self._commit_text(word)
        else:
            self.bell()

    def _clear_input(self):
        self.input_buffer = ""
        self.candidates = []
        self.current_page = 0
        self.selection_mode = False
        self._update_input_display()
        self._update_candidates()
        self.status_var.set("已清空編碼")

    def _clear_all(self):
        self._clear_input()
        self.committed_text_widget.delete('1.0', tk.END)
        self.committed_text = ""
        self.status_var.set("已清除全部")

    def _on_double_click(self, event):
        try:
            selection = self.candidates_listbox.curselection()
            if selection:
                index = selection[0]
                self._select_candidate(index)
        except Exception:
            pass

    def _show_lookup_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("查詢編碼")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        ttk.Label(dialog, text="輸入要查詢的字:").pack(pady=5)
        entry = ttk.Entry(dialog, width=30, font=("Microsoft JhengHei", 12))
        entry.pack(pady=5)
        entry.focus_set()
        result_text = tk.Text(dialog, height=10, width=40, font=("Consolas", 10))
        result_text.pack(pady=5, fill=tk.BOTH, expand=True)
        def on_query():
            char = entry.get().strip()
            if not char:
                result_text.delete('1.0', tk.END)
                result_text.insert('1.0', "請輸入要查詢的字")
                return
            codes = self.db.lookup_word(char)
            result_text.delete('1.0', tk.END)
            if codes:
                result_text.insert('1.0', f"'{char}' 的編碼:\n\n")
                for code in codes:
                    freq = self.db.get_word_frequency(char)
                    result_text.insert('1.0', f"  {code} (頻率: {freq})\n")
            else:
                result_text.insert('1.0', f"'{char}' 未在詞庫中找到")
        ttk.Button(dialog, text="查詢", command=on_query).pack(pady=5)
        dialog.bind('<Return>', lambda e: on_query())

    def _show_add_word_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("添加用戶詞庫")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        ttk.Label(dialog, text="編碼:").pack(anchor=tk.W, padx=10, pady=2)
        code_entry = ttk.Entry(dialog, width=30)
        code_entry.pack(padx=10, pady=2)
        ttk.Label(dialog, text="字詞:").pack(anchor=tk.W, padx=10, pady=2)
        word_entry = ttk.Entry(dialog, width=30)
        word_entry.pack(padx=10, pady=2)
        ttk.Label(dialog, text="頻率 (可選，默認 1000):").pack(anchor=tk.W, padx=10, pady=2)
        freq_entry = ttk.Entry(dialog, width=30)
        freq_entry.insert(0, "1000")
        freq_entry.pack(padx=10, pady=2)
        status_var = tk.StringVar(value="")
        ttk.Label(dialog, textvariable=status_var, foreground="blue").pack(pady=5)
        def on_add():
            code = code_entry.get().strip()
            word = word_entry.get().strip()
            freq_str = freq_entry.get().strip()
            if not code or not word:
                status_var.set("❌ 編碼和字詞不能為空")
                return
            try:
                freq = int(freq_str) if freq_str else 1000
            except ValueError:
                status_var.set("❌ 頻率必須是數字")
                return
            success = self.db.add_user_word(code, word, freq)
            if success:
                status_var.set(f"✅ 已添加: '{code}' -> '{word}' (freq={freq})")
                code_entry.delete(0, tk.END)
                word_entry.delete(0, tk.END)
            else:
                status_var.set("❌ 添加失敗")
        ttk.Button(dialog, text="添加", command=on_add).pack(pady=10)

    def _on_closing(self):
        self.db.close()
        self.destroy()


def main():
    app = BSMApp()
    app.update_idletasks()
    width = app.winfo_width()
    height = app.winfo_height()
    x = (app.winfo_screenwidth() // 2) - (width // 2)
    y = (app.winfo_screenheight() // 2) - (height // 2)
    app.geometry(f'+{x}+{y}')
    app.protocol("WM_DELETE_WINDOW", app._on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
