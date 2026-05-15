# filename: ProgramingEnviroment_v2.4.1.py
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

# --- バージョン定義 ---
APP_NAME = "ProgramingEnviroment"
VERSION = "2.4.1"
TARGET_PYTHON = "3.13"

class ProgramingEnviromentApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - v{VERSION}")
        self.root.geometry("900x950")
        self.root.configure(bg="#f8f9fa")
        
        self.config_file = "config.json"
        self.load_config()
        self.setup_ui()

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
        tk.Label(header, text=f"{APP_NAME} v{VERSION}", font=("Segoe UI", 18, "bold"), bg="#f8f9fa", fg="#1a73e8").pack(side="left")
        tk.Button(header, text="⚙ Settings", command=self.open_settings, bg="#dee2e6", bd=0, padx=10).pack(side="right")

        self.path_label = tk.Label(main_frame, text=f"Base Dir: {self.config['base_dir']}", bg="#f8f9fa", fg="#5f6368")
        self.path_label.pack(anchor="w", pady=(0, 5))

        tk.Label(main_frame, text="File Name:", bg="#f8f9fa", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.file_name_entry = tk.Entry(main_frame, font=("Consolas", 11), bd=1, relief="solid")
        self.file_name_entry.pack(fill="x", pady=(0, 10))
        self.file_name_entry.insert(0, f"{APP_NAME}_v{VERSION}.py")

        code_header = tk.Frame(main_frame, bg="#f8f9fa")
        code_header.pack(fill="x")
        tk.Label(code_header, text="Source Code (Auto-scan dependencies enabled):", bg="#f8f9fa", font=("Segoe UI", 9, "bold")).pack(side="left")
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
        tk.Button(log_header, text="Clear Log", command=self.clear_log, font=("Segoe UI", 8), bg="#f5f5f5", fg="#616161", bd=0, padx=5).pack(side="right")

        self.log_area = scrolledtext.ScrolledText(main_frame, height=12, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_area.pack(fill="both", expand=False)
        self.log_area.tag_configure("info", foreground="#9cdcfe")
        self.log_area.tag_configure("error", foreground="#f44747")
        self.log_area.tag_configure("success", foreground="#b5cea8")

    def clear_code(self):
        if messagebox.askyesno("Confirm", "Clear all source code?"):
            self.code_area.delete("1.0", tk.END)

    def clear_log(self):
        self.log_area.delete("1.0", tk.END)
        self.log("Log cleared.")

    def log(self, message, tag="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_area.see(tk.END)
        self.root.update_idletasks()

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
        self.log_area.delete("1.0", tk.END)
        self.action_btn.config(state="disabled", text="⚡ Processing...")
        threading.Thread(target=self.run_pipeline, daemon=True).start()

    def check_and_install_dependencies(self, code):
        """ソースコードからインポート文を探し、なければインストールする"""
        self.log("Scanning dependencies...")
        imports = re.findall(r"^(?:import|from)\s+([a-zA-Z0-9_]+)", code, re.MULTILINE)
        unique_imports = set(imports)
        
        # --- 修正点: set(sys.builtin_module_names) に変換 ---
        exclude = set(sys.builtin_module_names) | {"tkinter", "os", "sys", "re", "json", "threading", "subprocess", "shutil", "datetime", "git", "importlib", "time", "tkinterdnd2"}
        
        for module in unique_imports:
            if module in exclude: continue
            
            # モジュールが存在するかチェック
            spec = importlib.util.find_spec(module)
            if spec is None:
                self.log(f"Missing module found: {module}", "error")
                if messagebox.askyesno("Dependency Check", f"Module '{module}' is missing. Install it via pip?"):
                    self.log(f"Installing {module}...")
                    process = subprocess.run(["py", f"-{TARGET_PYTHON}", "-m", "pip", "install", module], capture_output=True, text=True)
                    if process.returncode == 0:
                        self.log(f"Successfully installed {module}", "success")
                    else:
                        raise Exception(f"Failed to install {module}:\n{process.stderr}")
                else:
                    raise Exception(f"Aborted: Missing module '{module}' is required.")

    def get_project_name(self, file_name):
        clean_name = re.split(r'[_ \-]', file_name)[0]
        return clean_name if clean_name else APP_NAME

    def run_pipeline(self):
        raw_file_name = self.file_name_entry.get().strip()
        file_name = raw_file_name if raw_file_name.lower().endswith(".py") else raw_file_name + ".py"
        code_content = self.code_area.get("1.0", tk.END).strip()
        
        prog_name = self.get_project_name(file_name)
        target_dir = os.path.abspath(os.path.join(self.config["base_dir"], prog_name))
        full_path = os.path.join(target_dir, file_name)
        dist_path = os.path.join(target_dir, "dist")

        try:
            self.log(f"--- Pipeline v{VERSION} [Project: {prog_name}] ---")
            self.check_and_install_dependencies(code_content)

            if not os.path.exists(target_dir): os.makedirs(target_dir)
            self.organize_old_files(target_dir, file_name)

            self.log(f"Saving source: {file_name}")
            with open(full_path, "w", encoding="utf-8") as f: f.write(code_content)

            self.log("Git operations...")
            self.execute_git(target_dir, file_name)

            self.log("PyInstaller Build...")
            self.execute_build(target_dir, file_name)

            self.log("All processes completed successfully!", "success")
            messagebox.showinfo("Success", f"Build for {prog_name} completed!")
            if os.path.exists(dist_path):
                os.startfile(dist_path)

        except Exception as e:
            self.log(f"CRITICAL ERROR: {str(e)}", "error")
            messagebox.showerror("Pipeline Failed", str(e))
        finally:
            self.action_btn.config(state="normal", text="🚀 Save, Push & Build EXE")

    def organize_old_files(self, target_dir, current_file_name):
        old_dir = os.path.join(target_dir, "old")
        dist_dir = os.path.join(target_dir, "dist")
        current_base = os.path.splitext(current_file_name)[0]
        if not os.path.exists(old_dir): os.makedirs(old_dir)
        for f in os.listdir(target_dir):
            if f.endswith((".py", ".spec")) and f != current_file_name and f != f"{current_base}.spec":
                if f in ["old", "dist", "build"]: continue
                if os.path.isdir(os.path.join(target_dir, f)): continue
                if APP_NAME in f: continue
                self.log(f"Moving {f} to old/")
                try: shutil.move(os.path.join(target_dir, f), os.path.join(old_dir, f))
                except: pass
        if os.path.exists(dist_dir):
            for f in os.listdir(dist_dir):
                if f.endswith(".exe") and f != f"{current_base}.exe":
                    if