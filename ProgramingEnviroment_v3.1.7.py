# filename: ProgramingEnviroment_v3.1.7.py
import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
import sys
import git
import re
import json
import threading
import subprocess
import shutil
import importlib.util
from datetime import datetime
import time

# --- バージョン定義 ---
APP_NAME = "ProgramingEnviroment"
VERSION = "3.1.7"
TARGET_PYTHON = "3.13"

class ProgramingEnviromentApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - v{VERSION}")
        self.root.geometry("950x1000")
        self.root.configure(bg="#f8f9fa")
        
        self.config_file = "config.json"
        self.sync_active = False
        self.last_sync_content = ""
        
        self.load_config()
        self.setup_ui()
        
        # 起動直後の自動Sync
        self.log(f"Welcome to {APP_NAME} v{VERSION}")
        self.root.after(800, self.toggle_sync)

    def load_config(self):
        default_base = r"E:\gemini" if os.path.exists("E:") else os.path.join(os.getcwd(), "Projects")
        default_config = {
            "base_dir": default_base,
            "github_url": "https://github.com/ktakamuki-git/Programing_Enviroment.git"
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = {**default_config, **json.load(f)}
            except: self.config = default_config
        else: self.config = default_config

    def save_config(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#f8f9fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        header = tk.Frame(main_frame, bg="#f8f9fa")
        header.pack(fill="x")
        tk.Label(header, text=f"{APP_NAME}", font=("Segoe UI", 18, "bold"), bg="#f8f9fa", fg="#1a73e8").pack(side="left")
        
        self.sync_btn = tk.Button(header, text="🌐 Sync: OFF", command=self.toggle_sync, bg="#6c757d", fg="white", bd=0, padx=15, font=("Segoe UI", 9, "bold"))
        self.sync_btn.pack(side="left", padx=20)
        
        tk.Button(header, text="⚙ Settings", command=self.open_settings, bg="#dee2e6", bd=0, padx=10).pack(side="right")

        self.path_label = tk.Label(main_frame, text=f"Base Dir: {self.config['base_dir']}", bg="#f8f9fa", fg="#5f6368")
        self.path_label.pack(anchor="w", pady=(0, 5))

        tk.Label(main_frame, text="Target File Name:", bg="#f8f9fa", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.file_name_entry = tk.Entry(main_frame, font=("Consolas", 11), bd=1, relief="solid")
        self.file_name_entry.pack(fill="x", pady=(0, 10))
        self.file_name_entry.insert(0, f"{APP_NAME}_v{VERSION}.py")

        code_header = tk.Frame(main_frame, bg="#f8f9fa")
        code_header.pack(fill="x")
        tk.Label(code_header, text="Source Code:", bg="#f8f9fa", font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Button(code_header, text="Clear Code", command=self.clear_code, font=("Segoe UI", 8), bg="#ffebee", fg="#c62828", bd=0, padx=5).pack(side="right")

        self.code_area = scrolledtext.ScrolledText(main_frame, height=20, font=("Consolas", 10), bd=1, relief="solid")
        self.code_area.pack(fill="both", expand=True, pady=(0, 10))
        self.code_area.bind("<KeyRelease>", self.auto_extract_filename)

        self.action_btn = tk.Button(main_frame, text="🚀 Save, Push & Build EXE", command=self.start_process, 
                                   bg="#1a73e8", fg="white", font=("Segoe UI", 12, "bold"), pady=8, bd=0)
        self.action_btn.pack(fill="x", pady=(0, 10))

        log_header = tk.Frame(main_frame, bg="#f8f9fa")
        log_header.pack(fill="x")
        tk.Label(log_header, text="Execution Log:", bg="#f8f9fa", font=("Segoe UI", 9, "bold")).pack(side="left")
        
        btn_frame = tk.Frame(log_header, bg="#f8f9fa")
        btn_frame.pack(side="right")
        tk.Button(btn_frame, text="📋 Copy Log", command=self.copy_log_to_clipboard, font=("Segoe UI", 8), bg="#e3f2fd", fg="#1565c0", bd=0, padx=5).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Clear Log", command=self.clear_log, font=("Segoe UI", 8), bg="#f5f5f5", fg="#616161", bd=0, padx=5).pack(side="left")

        self.log_area = scrolledtext.ScrolledText(main_frame, height=12, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_area.pack(fill="both", expand=False)
        self.log_area.tag_configure("info", foreground="#9cdcfe")
        self.log_area.tag_configure("error", foreground="#f44747")
        self.log_area.tag_configure("success", foreground="#b5cea8")
        self.log_area.tag_configure("sync", foreground="#dcdcaa")

    def log(self, message, tag="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def toggle_sync(self):
        if not self.sync_active:
            self.sync_active = True
            self.sync_btn.config(text="🛑 Stop Sync (Active)", bg="#ea4335")
            self.log("Initializing Gemini Sync Engine...", "sync")
            threading.Thread(target=self.run_gemini_monitor, daemon=True).start()
        else:
            self.sync_active = False
            self.sync_btn.config(text="🌐 Start Sync", bg="#34a853")
            self.log("Gemini Sync Engine Stopped.", "sync")

    def run_gemini_monitor(self):
        try:
            local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
            pw_browser_path = os.path.join(local_appdata, "ms-playwright")
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = pw_browser_path
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.log("ERROR: 'playwright' module not found.", "error")
            self.sync_active = False
            return

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=False, timeout=60000, args=['--no-sandbox', '--disable-setuid-sandbox'])
                page = browser.new_page()
                page.goto("https://gemini.google.com/app", wait_until="domcontentloaded")
                self.log("Sync Active! Cleaning filters enabled.", "success")
                
                while self.sync_active:
                    try:
                        blocks = page.query_selector_all("pre")
                        if blocks:
                            for block in reversed(blocks):
                                raw_content = block.inner_text()
                                # --- 強化された抽出ロジック ---
                                # # filename: から # ---ここまで--- までを抜き出す正規表現
                                pattern = r"(#\s*filename:.*?#\s*---ここまで---)"
                                match = re.search(pattern, raw_content, re.DOTALL | re.IGNORECASE)
                                
                                if match:
                                    clean_content = match.group(1).strip()
                                    if clean_content != self.last_sync_content:
                                        self.last_sync_content = clean_content
                                        self.root.after(0, lambda c=clean_content: self.update_code_from_sync(c))
                                    break
                    except: pass
                    time.sleep(2)
                browser.close()
            except Exception as e:
                self.log(f"SYNC ERROR: {str(e)}", "error")
                self.sync_active = False
                self.root.after(0, lambda: self.sync_btn.config(text="🌐 Start Sync", bg="#34a853"))

    def update_code_from_sync(self, content):
        self.code_area.delete("1.0", tk.END)
        self.code_area.insert("1.0", content)
        self.auto_extract_filename()
        self.log("Sync Success: Clean code imported.", "success")
        self.root.bell()

    def copy_log_to_clipboard(self):
        log_content = self.log_area.get("1.0", tk.END).strip()
        if log_content:
            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)
            self.log("Log copied to clipboard.", "info")

    def clear_code(self):
        if messagebox.askyesno("Confirm", "Clear code?"):
            self.code_area.delete("1.0", tk.END)

    def clear_log(self):
        self.log_area.delete("1.0", tk.END)
        self.log("Log cleared.")

    def open_settings(self):
        sw = tk.Toplevel(self.root)
        sw.title("Settings")
        sw.geometry("500x280")
        tk.Label(sw, text="Base Directory:").pack(pady=(10,0))
        ent_dir = tk.Entry(sw, width=60); ent_dir.insert(0, self.config["base_dir"]); ent_dir.pack(pady=5)
        tk.Label(sw, text="GitHub URL:").pack(pady=(10,0))
        ent_url = tk.Entry(sw, width=60); ent_url.insert(0, self.config["github_url"]); ent_url.pack(pady=5)
        def apply():
            self.config["base_dir"] = ent_dir.get()
            self.config["github_url"] = ent_url.get()
            self.save_config()
            self.path_label.config(text=f"Base Dir: {self.config['base_dir']}")
            sw.destroy()
        tk.Button(sw, text="Apply Changes", command=apply, bg="#1a73e8", fg="white", pady=5).pack(pady=20)

    def auto_extract_filename(self, event=None):
        first_line = self.code_area.get("1.0", "1.end").strip()
        match = re.search(r'filename:\s*([\w\.\- ]+)', first_line, re.IGNORECASE)
        if match:
            name = match.group(1)
            if self.file_name_entry.get() != name:
                self.file_name_entry.delete(0, tk.END)
                self.file_name_entry.insert(0, name)

    def start_process(self):
        code_content = self.code_area.get("1.0", tk.END).strip()
        if not code_content:
            messagebox.showwarning("Warning", "Code is empty!")
            return
        self.log_area.delete("1.0", tk.END)
        self.action_btn.config(state="disabled", text="⚡ Processing...")
        threading.Thread(target=self.run_