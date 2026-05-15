# filename: ProgramingEnviroment_v3.3.3.py
# sub_process: False
# --- ここから ---
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
VERSION = "3.3.3"
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
        self.page = None
        self.browser_context = None
        
        self.load_config()
        self.setup_ui()
        
        self.log(f"Welcome to {APP_NAME} v{VERSION}")

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
        tk.Label(header, text=f"{APP_NAME}", font=("Segoe UI", 14, "bold"), bg="#f8f9fa", fg="#1a73e8").pack(side="left")
        
        self.sync_btn = tk.Button(header, text="🌐 Start Sync", command=self.toggle_sync, bg="#34a853", fg="white", bd=0, padx=10, font=("Segoe UI", 9, "bold"))
        self.sync_btn.pack(side="left", padx=10)
        
        self.scan_btn = tk.Button(header, text="🔍 Manual Scan", command=self.manual_scan, bg="#1a73e8", fg="white", bd=0, padx=10, font=("Segoe UI", 9))
        self.scan_btn.pack(side="left", padx=5)
        
        tk.Button(header, text="⚙ Settings", command=self.open_settings, bg="#dee2e6", bd=0, padx=10).pack(side="right")

        self.path_label = tk.Label(main_frame, text=f"Base Dir: {self.config['base_dir']}", bg="#f8f9fa", fg="#5f6368", font=("Segoe UI", 8))
        self.path_label.pack(anchor="w", pady=(2, 5))

        tk.Label(main_frame, text="Target File Name:", bg="#f8f9fa", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.file_name_entry = tk.Entry(main_frame, font=("Consolas", 11), bd=1, relief="solid")
        self.file_name_entry.pack(fill="x", pady=(0, 10))
        self.file_name_entry.insert(0, f"{APP_NAME}_v{VERSION}.py")

        self.code_area = scrolledtext.ScrolledText(main_frame, height=25, font=("Consolas", 10), bd=1, relief="solid")
        self.code_area.pack(fill="both", expand=True, pady=(0, 10))
        self.code_area.bind("<KeyRelease>", self.auto_extract_filename)

        self.action_btn = tk.Button(main_frame, text="🚀 Save, Push & Build EXE", command=self.start_process, 
                                   bg="#1a73e8", fg="white", font=("Segoe UI", 12, "bold"), pady=8, bd=0)
        self.action_btn.pack(fill="x", pady=(0, 10))

        self.log_area = scrolledtext.ScrolledText(main_frame, height=10, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
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
            self.sync_btn.config(text="🛑 Stop Sync", bg="#ea4335")
            self.log("Starting Gemini Sync (60s interval)...", "sync")
            threading.Thread(target=self.run_gemini_monitor, daemon=True).start()
        else:
            self.sync_active = False
            self.log("Stopping Sync Engine...", "sync")

    def manual_scan(self):
        if not self.page:
            messagebox.showinfo("Info", "Sync has not been started yet.")
            return
        self.log("Manual scanning for code blocks...", "sync")
        self.scan_for_code()

    def scan_for_code(self):
        if not self.page: return
        try:
            # ページが閉じられていないかチェック
            if self.page.is_closed(): return False
            blocks = self.page.query_selector_all("pre")
            if blocks:
                for block in reversed(blocks):
                    raw_content = block.inner_text()
                    pattern = r"(#\s*filename:.*?#\s*---ここまで---)"
                    match = re.search(pattern, raw_content, re.DOTALL | re.IGNORECASE)
                    if match:
                        clean_content = match.group(1).strip()
                        if clean_content != self.last_sync_content:
                            self.last_sync_content = clean_content
                            self.root.after(0, lambda c=clean_content: self.update_code_from_sync(c))
                        return True
            return False
        except Exception as e:
            self.log(f"Scan interrupted: {e}", "info")
            return False

    def run_gemini_monitor(self):
        try:
            from playwright.sync_api import sync_playwright
            project_name = self.get_project_name(self.file_name_entry.get())
            session_dir = os.path.abspath(os.path.join(self.config["base_dir"], project_name, ".sync_session"))
            
            with sync_playwright() as p:
                self.browser_context = p.chromium.launch_persistent_context(
                    user_data_dir=session_dir,
                    headless=False,
                    args=['--start-maximized', '--no-sandbox']
                )
                self.page = self.browser_context.pages[0] if self.browser_context.pages else self.browser_context.new_page()
                self.page.goto("https://gemini.google.com/app")
                self.log("Sync Session Ready.", "success")
                
                while self.sync_active:
                    self.scan_for_code()
                    # 60秒間、1秒ごとにフラグをチェック（即時停止に対応するため）
                    for _ in range(60):
                        if not self.sync_active: break
                        time.sleep(1)
                
                try:
                    if self.browser_context:
                        self.browser_context.close()
                except: pass
                
                self.page = None
                self.browser_context = None
                self.root.after(0, lambda: self.sync_btn.config(text="🌐 Start Sync", bg="#34a853"))
                self.log("Sync safely closed.", "sync")
        except Exception as e:
            self.log(f"SYNC ERROR: {str(e)}", "error")
            self.sync_active = False
            self.root.after(0, lambda: self.sync_btn.config(text="🌐 Start Sync", bg="#34a853"))

    def update_code_from_sync(self, content):
        self.code_area.delete("1.0", tk.END)
        self.code_area.insert("1.0", content)
        self.auto_extract_filename()
        self.log("Sync Success: Code updated.", "success")
        self.root.bell()

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
        if not code_content: return
        self.action_btn.config(state="disabled", text="⚡ Processing...")
        threading.Thread(target=self.run_pipeline, daemon=True).start()

    def get_project_name(self, file_name):
        clean_name = re.split(r'[_ \-]', file_name)[0]
        return clean_name if clean_name else APP_NAME

    def run_pipeline(self):
        file_name = self.file_name_entry.get().strip()
        if not file_name.lower().endswith(".py"): file_name += ".py"
        code_content = self.code_area.get("1.0", tk.END).strip()
        prog_name = self.get_project_name(file_name)
        target_dir = os.path.abspath(os.path.join(self.config["base_dir"], prog_name))
        full_path = os.path.join(target_dir, file_name)

        try:
            if not os.path.exists(target_dir): os.makedirs(target_dir)
            with open(full_path, "w", encoding="utf-8") as f: f.write(code_content)
            self.log(f"Saved: {file_name}", "success")
            # --- Git & Build 実行 (v3.3.1と同等) ---
            self.execute_git(target_dir, file_name)
            self.execute_build(target_dir, file_name)
            self.log("Pipeline finished.", "success")
            messagebox.showinfo("Success", "Process completed!")
        except Exception as e:
            self.log(f"Error: {str(e)}", "error")
        finally:
            self.action_btn.config(state="normal", text="🚀 Save, Push & Build EXE")

    def execute_git(self, target_dir, file_name):
        try:
            repo = git.Repo(target_dir) if os.path.exists(os.path.join(target_dir, ".git")) else git.Repo.init(target_dir)
            repo.index.add([file_name]); repo.index.commit(f"Auto-update: {file_name}")
            if 'origin' in [r.name for r in repo.remotes]:
                repo.remote(name='origin').push()
        except: pass

    def execute_build(self, target_dir, file_name):
        dist_path = os.path.abspath(os.path.join(target_dir, "dist"))
        cmd = ["py", f"-{TARGET_PYTHON}", "-m", "PyInstaller", "--onefile", "--noconsole", f"--distpath={dist_path}", file_name]
        subprocess.run(cmd, cwd=target_dir, shell=True)

    def open_settings(self):
        sw = tk.Toplevel(self.root)
        sw.title("Settings")
        ent_dir = tk.Entry(sw, width=50); ent_dir.insert(0, self.config["base_dir"]); ent_dir.pack(pady=10)
        def apply():
            self.config["base_dir"] = ent_dir.get()
            self.save_config()
            sw.destroy()
        tk.Button(sw, text="Apply", command=apply).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk(); app = ProgramingEnviromentApp(root); root.mainloop()
# ---ここまで---