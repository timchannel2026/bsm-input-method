#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BSM 筆順碼輸入法 — 完整 Python 桌面應用
=========================================

一個完整的圖形界面筆順碼輸入法，支持：
- 十劃映射輸入（0-9）
- 候選字選擇（1-9 數字鍵或滑鼠點擊）
- 多頁翻頁（/ =）
- 萬用鍵 *
- 符號輸入
- 用戶自訂詞庫
- 編碼查詢
- 字頻排序

作者: Community Rebuild (2026)
原始開發: FreeFire Limited (~2000年)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import sys
import io
import json
import threading
from datetime import datetime

# Force UTF-8 output
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# ============================================================
# 配置常量
# ============================================================

APP_NAME = "BSM 筆順碼輸入法"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Community Rebuild"

# 十劃映射
STROKE_MAP = {
    '0': '組合型',
    '1': '橫(㇐)',
    '2': '豎(㇑)',
    '3': '撇(㇒)',
    '4': '點捺(㇏)',
    '5': '上挑鉤(㇀)',
    '6': '下挑鉤(㇂)',
    '7': '交叉(㇥)',
    '8': '人八型',
    '9': '方框型',
}

# 符號編碼範圍
SYMBOL_CODES = {
    '60': ['，', '。', '！', '？', '：', '；', '、'],
    '61': ['「', '」'],
    '62': ['『', '』'],
    '933': ['—'],
    '934': ['…'],
    '935': ['（', '）'],
    '936': ['【', '】'],
    '937': ['《', '》'],
    '938': ['〔', '〕'],
    '939': ['〖', '〗'],
}

# 默認詞庫路徑
DEFAULT_DB_PATHS = [
    r"C:\Users\timch\AppData\Local\BSM_InputMethod\bsm.db",
    r"C:\Users\timch\.agnes\temporary\2026-07-24\20260724_1\work\bsm_final.db",
]

# 用戶詞庫路徑
USER_DB_PATH = os.path.join(os.environ.get("LOCALAPPDATA", ""), "BSM_InputMethod", "user_words.db")


# ============================================================
# 數據庫管理器
# ============================================================

class DatabaseManager:
    """詞庫數據庫管理"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.user_conn = None
    
    def connect(self):
        """連接主詞庫和用戶詞庫"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"Error connecting to main DB: {e}")
            return False
        
        # Create user database if not exists
        if not os.path.exists(USER_DB_PATH):
            self._create_user_db()
        
        try:
            self.user_conn = sqlite3.connect(USER_DB_PATH)
            self.user_cursor = self.user_conn.cursor()
        except Exception as e:
            print(f"Error connecting to user DB: {e}")
            return False
        
        return True
    
    def _create_user_db(self):
        """創建用戶詞庫"""
        self.user_conn = sqlite3.connect(USER_DB_PATH)
        self.user_cursor = self.user_conn.cursor()
        self.user_cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(6) NOT NULL,
                word NVARCHAR(10) NOT NULL,
                frequency INTEGER DEFAULT 1000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.user_cursor.execute("CREATE INDEX idx_user_code ON user_words(code)")
        self.user_conn.commit()
        self.user_conn.close()
    
    def query_candidates(self, code, page=0, page_size=9):
        """查詢候選字"""
        if not code:
            return [], 0
        
        min_len = max(len(code) - 1, 1)
        
        # Query main dictionary
        sql = """
            SELECT code, word, frequency FROM ime 
            WHERE code LIKE ? AND length(code) >= ?
            GROUP BY word 
            ORDER BY frequency ASC, code ASC, word ASC
            LIMIT ? OFFSET ?
        """
        
        self.cursor.execute(sql, (code + '%', min_len, page_size, page * page_size))
        results = self.cursor.fetchall()
        
        # Query user dictionary
        try:
            self.user_cursor.execute(sql, (code + '%', min_len, page_size, page * page_size))
            user_results = self.user_cursor.fetchall()
            
            # Merge and deduplicate
            all_results = list(results)
            seen = set(r[1] for r in results)  # word is column 1
            for r in user_results:
                if r[1] not in seen:
                    all_results.append(r)
            results = all_results
        except:
            pass
        
        # Get total count
        count_sql = """
            SELECT COUNT(DISTINCT word) FROM ime 
            WHERE code LIKE ? AND length(code) >= ?
        """
        self.cursor.execute(count_sql, (code + '%', min_len))
        total = self.cursor.fetchone()[0]
        
        # Add user words count
        try:
            self.user_cursor.execute(count_sql, (code + '%', min_len))
            user_total = self.user_cursor.fetchone()[0]
            total += user_total
        except:
            pass
        
        return results, total
    
    def lookup_word(self, char):
        """查詢某字的編碼"""
        sql = "SELECT DISTINCT code FROM ime WHERE word=? ORDER BY LENGTH(code), frequency LIMIT 5"
        self.cursor.execute(sql, (char,))
        return [row[0] for row in self.cursor.fetchall()]
    
    def add_user_word(self, code, word, frequency=1000):
        """添加用戶自訂詞"""
        try:
            self.user_cursor.execute(
                "INSERT OR REPLACE INTO user_words (code, word, frequency) VALUES (?, ?, ?)",
                (code, word, frequency)
            )
            self.user_conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user word: {e}")
            return False
    
    def get_word_frequency(self, char):
        """獲取字頻"""
        sql = "SELECT MIN(frequency) FROM ime WHERE word=?"
        self.cursor.execute(sql, (char,))
        result = self.cursor.fetchone()
        return result[0] if result else 6000
    
    def close(self):
        """關閉連接"""
        if self.conn:
            self.conn.close()
        if self.user_conn:
            self.user_conn.close()


# ============================================================
# 主應用窗口
# ============================================================

class BSMApp(tk.Tk):
    """BSM 筆順碼輸入法主應用"""
    
    def __init__(self):
        super().__init__()
        
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("700x550")
        self.resizable(True, True)
        self.minsize(600, 450)
        
        # Initialize database
        self.db_path = self._find_dictionary()
        self.db = DatabaseManager(self.db_path)
        if not self.db.connect():
            messagebox.showerror("錯誤", f"無法打開詞庫文件：\n{self.db_path}")
            self.destroy()
            return
        
        # Input state
        self.input_buffer = ""
        self.candidates = []
        self.total_pages = 0
        self.current_page = 0
        self.selection_mode = False
        self.committed_text = ""
        self.page_size = 9
        
        # Setup UI
        self._setup_ui()
        
        # Bind keyboard events
        self.bind('<Key>', self._on_key_press)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"[OK] 詞庫已加載: {os.path.basename(self.db_path)}")
        self.statusbar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _find_dictionary(self):
        """自動查找詞庫文件"""
        # Try config first
        config_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "BSM_InputMethod", "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                db_path = config.get('dictionary_path')
                if db_path and os.path.exists(db_path):
                    return db_path
            except:
                pass
        
        # Try default paths
        for path in DEFAULT_DB_PATHS:
            if os.path.exists(path):
                return path
        
        # Search D:\Pen
        pen_dir = r"D:\Pen"
        if os.path.exists(pen_dir):
            for root, dirs, files in os.walk(pen_dir):
                for f in files:
                    if f.endswith('.db') or f.endswith('.IMF'):
                        return os.path.join(root, f)
        
        return DEFAULT_DB_PATHS[0] if DEFAULT_DB_PATHS else ""
    
    def _setup_ui(self):
        """設置用戶界面"""
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top section: Input display and committed text
        top_frame = ttk.LabelFrame(main_frame, text="輸入區", padding="5")
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Committed text display
        self.committed_var = tk.StringVar(value="")
        committed_label = ttk.Label(top_frame, text="已輸入:", font=("Microsoft JhengHei", 9))
        committed_label.pack(anchor=tk.W)
        
        self.committed_display = tk.Text(top_frame, height=3, width=70, 
                                         font=("Consolas", 11),
                                         bg="#f0f0f0", relief=tk.SUNKEN)
        self.committed_display.pack(fill=tk.X, pady=(0, 5))
        self.committed_display.insert('1.0', '')
        self.committed_display.config(state=tk.DISABLED)
        
        # Input buffer display
        input_label = ttk.Label(top_frame, text="當前編碼:", font=("Microsoft JhengHei", 9))
        input_label.pack(anchor=tk.W)
        
        self.input_display = tk.Text(top_frame, height=2, width=70,
                                     font=("Consolas", 12, "bold"),
                                     bg="#ffffff", relief=tk.SUNKEN)
        self.input_display.pack(fill=tk.X)
        self.input_display.insert('1.0', '(空)')
        self.input_display.config(state=tk.DISABLED)
        
        # Middle section: Candidates
        mid_frame = ttk.LabelFrame(main_frame, text="候選字", padding="5")
        mid_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Page info
        self.page_var = tk.StringVar(value="第 1 / 1 頁")
        page_label = ttk.Label(mid_frame, textvariable=self.page_var, font=("Microsoft JhengHei", 9))
        page_label.pack(anchor=tk.W)
        
        # Candidates listbox
        self.candidates_listbox = tk.Listbox(mid_frame, height=9, width=70,
                                             font=("Microsoft JhengHei", 11),
                                             selectmode=tk.SINGLE,
                                             bg="#fafafa",
                                             selectbackground="#4a90d9",
                                             selectforeground="white")
        self.candidates_listbox.pack(fill=tk.BOTH, expand=True, pady=(2, 2))
        self.candidates_listbox.bind('<Double-Button-1>', self._on_double_click)
        
        # Bottom section: Controls and info
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        
        # Stroke map display
        stroke_frame = ttk.LabelFrame(bottom_frame, text="十劃映射", padding="5")
        stroke_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.stroke_display = tk.Text(stroke_frame, height=2, width=60,
                                      font=("Microsoft JhengHei", 8))
        self.stroke_display.pack(fill=tk.X)
        self.stroke_display.insert('1.0', self._format_stroke_map())
        self.stroke_display.config(state=tk.DISABLED)
        
        # Control buttons
        ctrl_frame = ttk.LabelFrame(bottom_frame, text="快捷操作", padding="5")
        ctrl_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        ttk.Button(ctrl_frame, text="查詢編碼", command=self._show_lookup_dialog).pack(fill=tk.X, pady=1)
        ttk.Button(ctrl_frame, text="添加詞庫", command=self._show_add_word_dialog).pack(fill=tk.X, pady=1)
        ttk.Button(ctrl_frame, text="清空", command=self._clear_all).pack(fill=tk.X, pady=1)
        ttk.Button(ctrl_frame, text="退出", command=self._on_closing).pack(fill=tk.X, pady=1)
        
        # Update stroke display
        self._update_input_display()
    
    def _format_stroke_map(self):
        """格式化顯示十劃映射"""
        lines = []
        for key in range(10):
            digit = str(key)
            name = STROKE_MAP[digit]
            lines.append(f"{digit}={name}")
        return '\n'.join(lines)
    
    def _update_input_display(self):
        """更新輸入顯示"""
        self.input_display.config(state=tk.NORMAL)
        self.input_display.delete('1.0', tk.END)
        
        if self.input_buffer:
            # Show stroke symbols
            marker = ""
            for ch in self.input_buffer:
                if ch in STROKE_MAP:
                    marker += f"{ch}({STROKE_MAP[ch][0]}) "
                else:
                    marker += ch + " "
            self.input_display.insert('1.0', f"[{marker.strip()}]")
        else:
            self.input_display.insert('1.0', '(空)')
        
        self.input_display.config(state=tk.DISABLED)
    
    def _update_candidates(self):
        """更新候選字列表"""
        self.candidates, self.total_pages = self.db.query_candidates(
            self.input_buffer, self.current_page, self.page_size
        )
        
        # Update listbox
        self.candidates_listbox.delete(0, tk.END)
        
        if not self.candidates:
            self.candidates_listbox.insert(tk.END, "(無匹配)")
        else:
            for i, (code, word, freq) in enumerate(self.candidates):
                # Display with number prefix for selection
                num = i + 1
                self.candidates_listbox.insert(tk.END, f"{num}. {word} [{code}] (freq={freq})")
        
        # Update page info
        if self.total_pages > 0:
            self.page_var.set(f"第 {self.current_page + 1} / {self.total_pages} 頁 ({len(self.candidates)} 個候選字)")
        else:
            self.page_var.set("第 0 / 0 頁")
    
    def _commit_text(self, text):
        """提交文本"""
        self.committed_text += text
        self.committed_display.config(state=tk.NORMAL)
        self.committed_display.delete('1.0', tk.END)
        self.committed_display.insert('1.0', self.committed_text)
        self.committed_display.config(state=tk.DISABLED)
        self.committed_display.see(tk.END)
    
    def _on_key_press(self, event):
        """鍵盤事件處理"""
        key = event.keysym
        char = event.char
        
        # Handle digit keys
        if char.isdigit() and len(char) == 1:
            self._append_digit(char)
            return "break"
        
        # Handle wildcard *
        if key == 'asterisk' or char == '*':
            self._key_wildcard()
            return "break"
        
        # Handle dot .
        if key == 'period' or char == '.':
            self._key_dot()
            return "break"
        
        # Handle minus/hyphen -
        if key == 'minus' or key == 'KP_Subtract' or char == '-':
            self._key_minus()
            return "break"
        
        # Handle equals =
        if key == 'equal' or key == 'KP_Add' or char == '=':
            self._key_equals()
            return "break"
        
        # Handle slash /
        if key == 'slash' or key == 'KP_Divide' or char == '/':
            self._key_slash()
            return "break"
        
        # Handle Enter/Space
        if key in ('Return', 'space', 'KP_Enter'):
            self._key_enter()
            return "break"
        
        # Handle Clear/Esc
        if key in ('Escape', 'Clear'):
            self._clear_all()
            return "break"
        
        # Handle BackSpace
        if key == 'BackSpace':
            self._key_minus()
            return "break"
        
        # Handle selection mode digits (1-9)
        if self.selection_mode and char.isdigit() and int(char) <= 9:
            self._select_candidate(int(char) - 1)
            return "break"
        
        return None
    
    def _append_digit(self, digit):
        """添加筆順碼"""
        if self.selection_mode:
            # In selection mode, digit selects candidate
            self._select_candidate(int(digit) - 1)
            return
        
        if len(self.input_buffer) >= 6:
            self.bell()  # Beep: max length reached
            return
        
        self.input_buffer += digit
        self.current_page = 0
        self.selection_mode = False
        self._update_input_display()
        self._update_candidates()
        
        if self.candidates:
            first_word = self.candidates[0][1]
            self.status_var.set(f"輸入: '{digit}' → '{first_word}'")
        else:
            self.status_var.set(f"輸入: '{digit}' → 無匹配")
    
    def _key_wildcard(self):
        """萬用鍵"""
        if self.selection_mode:
            self.status_var.set("萬用鍵模式")
            return
        
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
        
        if self.candidates:
            self.status_var.set(f"萬用鍵: '{self.input_buffer}' → {len(self.candidates)} 個匹配")
        else:
            self.status_var.set("萬用鍵: 無匹配")
    
    def _key_dot(self):
        """進入選字模式"""
        self.selection_mode = True
        if self.candidates:
            self.status_var.set(f"選字模式: {len(self.candidates)} 個候選字 (按 1-9 選擇)")
        else:
            self.status_var.set("選字模式: 無候選字")
    
    def _key_minus(self):
        """退格"""
        if self.selection_mode:
            self.selection_mode = False
            self.status_var.set("退出選字模式")
            return
        
        if not self.input_buffer:
            self.bell()
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
    
    def _key_equals(self):
        """上一頁"""
        if self.current_page > 0:
            self.current_page -= 1
        else:
            self.current_page = max(0, self.total_pages - 1)
        self._update_candidates()
        self.status_var.set(f"上一頁: {self.current_page + 1}/{self.total_pages}")
    
    def _key_slash(self):
        """下一頁"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
        else:
            self.current_page = 0
        self._update_candidates()
        self.status_var.set(f"下一頁: {self.current_page + 1}/{self.total_pages}")
    
    def _key_enter(self):
        """Enter: 選擇第一個候選字"""
        if self.selection_mode:
            # In selection mode, enter selects first candidate
            self._select_candidate(0)
        elif self.candidates:
            word = self.candidates[0][1]
            self._commit_text(word)
            self.status_var.set(f"已輸入: '{word}'")
        else:
            self.bell()
    
    def _select_candidate(self, index):
        """選擇候選字"""
        if 0 <= index < len(self.candidates):
            word = self.candidates[index][1]
            self._commit_text(word)
            self.status_var.set(f"已選擇: '{word}'")
            self.reset()
        else:
            self.bell()
    
    def reset(self):
        """重置輸入狀態"""
        self.input_buffer = ""
        self.candidates = []
        self.current_page = 0
        self.total_pages = 0
        self.selection_mode = False
        self._update_input_display()
        self._update_candidates()
    
    def _clear_all(self):
        """清除全部"""
        self.reset()
        self.status_var.set("已清除")
    
    def _on_double_click(self, event):
        """雙擊選擇候選字"""
        try:
            selection = self.candidates_listbox.curselection()
            if selection:
                index = selection[0]
                self._select_candidate(index)
        except:
            pass
    
    def _show_lookup_dialog(self):
        """顯示查詢編碼對話框"""
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
        """顯示添加詞庫對話框"""
        dialog = tk.Toplevel(self)
        dialog.title("添加用戶詞庫")
        dialog.geometry("400x350")
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
        """關閉應用"""
        self.db.close()
        self.destroy()


# ============================================================
# 主入口
# ============================================================

def main():
    print("=" * 60)
    print(f"{APP_NAME} v{APP_VERSION}")
    print(f"作者: {APP_AUTHOR}")
    print("=" * 60)
    
    app = BSMApp()
    
    # Center window
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
