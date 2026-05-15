# filename: ProgramingEnviroment_v3.3.9.py
# sub_process: False
# --- ここから ---
import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
import git
import re
import json
import threading
import subprocess
import shutil
from datetime import datetime
import time

# --- バージョン定義 ---
APP_NAME = "ProgramingEnviroment"
VERSION = "3.3.9"
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
        self.cleanup_old_exes()

    def load_config(self):
        default_base = r"E:\gemini" if os.path.exists("E:") else os.path.join(os.getcwd(), "Projects")
        default_config = {"base_dir": default_base}
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
        tk.Label(header, text=APP_NAME, font=("Segoe UI", 14, "bold"), bg="#f8f9fa", fg="#1a73e8").pack(side="left")
        
        self.sync_btn = tk.Button(header, text="🌐 Start Sync", command=self.toggle_sync, bg="#34a853", fg="white", bd=0, padx=10, font=("Segoe UI", 9, "bold"))
        self.sync_btn.pack(side="left", padx=10)
        
        tk.Button(header, text="⚙ Settings", command=self.open_settings, bg="#dee2e6", bd=0, padx=10).pack(side="right")

        self.path_label = tk.Label(main_frame, text=f"Base Dir: {self.config['base_dir']}", bg="#f8f9fa", fg="#5f6368", font=("Segoe UI", 8))
        self.path_label.pack(anchor="w", pady=(2, 5))

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

    def log(self, message, tag="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def toggle_sync(self):
        if not self.sync_active:
            self.sync_active = True
            self.sync_btn.config(text="🛑 Stop Sync", bg="#ea4335")
            threading.Thread(target=self.run_gemini_monitor, daemon=True).start()
        else:
            self.sync_active = False

    def run_gemini_monitor(self):
        try:
            from playwright.sync_api import sync_playwright
            pname = self.get_project_name(self.file_name_entry.get())
            session_dir = os.path.abspath(os.path.join(self.config["base_dir"], pname, ".sync_session"))
            with sync_playwright() as p:
                self.browser_context = p.chromium.launch_persistent_context(
                    user_data_dir=session_dir, headless=False, channel="chrome", args=['--no-sandbox']
                )
                self.page = self.browser_context.pages[0]
                self.page.goto("https://gemini.google.com/app")
                while self.sync_active:
                    blocks = self.page.query_selector_all("pre")
                    if blocks:
                        raw = blocks[-1].inner_text()
                        pattern = r"(#\s*filename:.*?#\s*---ここまで---)"
                        match = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
                        if match and match.group(1).strip() != self.last_sync_content:
                            self.last_sync_content = match.group(1).strip()
                            self.root.after(0, lambda c=self.last_sync_content: self.update_code(c))
                    time.sleep(2)
                self.browser_context.close()
        except Exception as e: self.log(f"Sync Error: {e}", "error")
        finally: self.root.after(0, lambda: self.sync_btn.config(text="🌐 Start Sync", bg="#34a853"))

    def update_code(self, content):
        self.code_area.delete("1.0", tk.END); self.code_area.insert("1.0", content)
        self.auto_extract_filename(); self.root.bell()

    def auto_extract_filename(self, event=None):
        first_line = self.code_area.get("1.0", "1.end")
        match = re.search(r'filename:\s*([\w\.\- ]+)', first_line, re.IGNORECASE)
        if match:
            self.file_name_entry.delete(0, tk.END); self.file_name_entry.insert(0, match.group(1).strip())

    def get_project_name(self, file_name):
        return re.split(r'[ \-]', file_name)[0] or APP_NAME

    def start_process(self):
        self.action_btn.config(state="disabled", text="⌛ Processing...")
        threading.Thread(target=self.run_pipeline, daemon=True).start()

    def run_pipeline(self):
        file_name = self.file_name_entry.get().strip()
        code = self.code_area.get("1.0", tk.END).strip()
        lines = code.splitlines()
        is_sub = len(lines) > 1 and "sub_process: True" in lines[1]
        self.log(f"Mode Detected: {'SUB-PROCESS' if is_sub else 'MAIN-PROCESS'}")
        pname = self.get_project_name(file_name)
        target_dir = os.path.abspath(os.path.join(self.config["base_dir"], pname))
        if is_sub: target_dir = os.path.join(target_dir, "processors")
        
        try:
            os.makedirs(target_dir, exist_ok=True)
            full_path = os.path.join(target_dir, file_name)
            with open(full_path, "w", encoding="utf-8") as f: f.write(code)
            self.log(f"File Saved: {file_name}", "success")
            repo_dir = os.path.dirname(target_dir) if is_sub else target_dir
            self.execute_git(repo_dir, full_path)
            
            if not is_sub:
                self.log(f"Initiating PyInstaller build for {file_name}...")
                self.execute_build(target_dir, file_name)
                self.cleanup_old_exes(target_dir, file_name)
                self.log("Build sequence completed successfully.", "success")
            else:
                self.log("Sub-process saved. Skipping EXE build.", "info")
            messagebox.showinfo("Success", "Pipeline Finished!")
        except Exception as e: self.log(f"Pipeline Failed: {e}", "error")
        finally: self.action_btn.config(state="normal", text="🚀 Save, Push & Build EXE")

    def execute_git(self, repo_dir, full_path):
        try:
            repo = git.Repo(repo_dir) if os.path.exists(os.path.join(repo_dir, ".git")) else git.Repo.init(repo_dir)
            repo.index.add([os.path.relpath(full_path, repo_dir)])
            repo.index.commit(f"Auto-update: {os.path.basename(full_path)}")
            if 'origin' in [r.name for r in repo.remotes]: repo.remote().push()
            self.log("Git push successful.")
        except: pass

    def execute_build(self, target_dir, file_name):
        dist = os.path.join(target_dir, "dist")
        subprocess.run(["py", f"-{TARGET_PYTHON}", "-m", "PyInstaller", "--onefile", "--noconsole", f"--distpath={dist}", file_name], 
                       cwd=target_dir, shell=True, check=True)

    def cleanup_old_exes(self, target_dir=None, current_file=None):
        base_dir = os.path.join(target_dir, "dist") if target_dir else os.getcwd()
        if not os.path.exists(base_dir): return
        ver_dir = os.path.join(base_dir, "Versions")
        os.makedirs(ver_dir, exist_ok=True)
        current_exe = current_file.replace(".py", ".exe") if current_file else f"{APP_NAME}_v{VERSION}.exe"
        for f in os.listdir(base_dir):
            if f.endswith(".exe") and f != current_exe and f != "Versions":
                try: 
                    shutil.move(os.path.join(base_dir, f), os.path.join(ver_dir, f))
                except Exception as e:
                    self.log(f"Cleanup skip: {f}", "info")

    def open_settings(self):
        sw = tk.Toplevel(self.root); sw.title("Settings")
        ent = tk.Entry(sw, width=50); ent.insert(0, self.config["base_dir"]); ent.pack(pady=10)
        tk.Button(sw, text="Apply", command=lambda: [self.config.update({"base_dir": ent.get()}), self.save_config(), sw.destroy()]).pack()

if __name__ == "__main__":
    root = tk.Tk(); app = ProgramingEnviromentApp(root); root.mainloop()
# ---ここまで---