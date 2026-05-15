# filename: ProgramingEnviroment_v2.0.2.py
import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
import sys
import git
import re
import json
import threading
import subprocess

# --- バージョン定義 ---
APP_NAME = "ProgramingEnviroment"
VERSION = "2.0.2"
TARGET_PYTHON = "3.13"

class ProgramingEnviromentApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - v{VERSION}")
        self.root.geometry("850x850")
        self.root.configure(bg="#f8f9fa")
        
        self.config_file = "config.json"
        self.load_config()
        self.setup_ui()

    def load_config(self):
        # デフォルトを「E:\gemini」に固定。なければ現在のフォルダのProjectsへ。
        default_base = r"E:\gemini" if os.path.exists("E:") else os.path.join(os.getcwd(), "Projects")
        
        default_config = {
            "base_dir": default_base,
            "github_url": "https://github.com/ktakamuki-git/Programing_Enviroment.git"
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = {**default_config, **json.load(f)}
            except:
                self.config = default_config
        else:
            self.config = default_config

    def save_config(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#f8f9fa")
        main_frame.pack(fill="both", expand=True, padx=25, pady=15)

        header = tk.Frame(main_frame, bg="#f8f9fa")
        header.pack(fill="x")
        tk.Label(header, text=f"{APP_NAME}", font=("Segoe UI", 20, "bold"), bg="#f8f9fa", fg="#1a73e8").pack(side="left")
        tk.Button(header, text="⚙ Settings", command=self.open_settings, bg="#dee2e6", bd=0, padx=10).pack(side="right")

        self.path_label = tk.Label(main_frame, text=f"Target: {self.config['base_dir']}", bg="#f8f9fa", fg="#5f6368")
        self.path_label.pack(anchor="w", pady=(0, 10))

        tk.Label(main_frame, text="File Name:", bg="#f8f9fa").pack(anchor="w")
        self.file_name_entry = tk.Entry(main_frame, font=("Consolas", 11), bd=1, relief="solid")
        self.file_name_entry.pack(fill="x", pady=(0, 10))
        self.file_name_entry.insert(0, f"{APP_NAME}_v{VERSION}.py")

        tk.Label(main_frame, text="Source Code:", bg="#f8f9fa").pack(anchor="w")
        self.code_area = scrolledtext.ScrolledText(main_frame, height=25, font=("Consolas", 10), bd=1, relief="solid")
        self.code_area.pack(fill="both", expand=True, pady=(0, 15))
        self.code_area.bind("<KeyRelease>", self.auto_extract_filename)

        self.action_btn = tk.Button(main_frame, text="🚀 Save, Push & Build (E: Drive Focus)", command=self.start_process, 
                                   bg="#1a73e8", fg="white", font=("Segoe UI", 12, "bold"), pady=10, bd=0)
        self.action_btn.pack(fill="x")

        self.status_label = tk.Label(main_frame, text="Ready", bg="#f8f9fa", fg="#5f6368")
        self.status_label.pack(pady=5)

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
            self.path_label.config(text=f"Target: {self.config['base_dir']}")
            sw.destroy()
        tk.Button(sw, text="Apply Changes", command=apply, bg="#1a73e8", fg="white", pady=5).pack(pady=20)

    def auto_extract_filename(self, event=None):
        first_line = self.code_area.get("1.0", "1.end").strip()
        match = re.search(r'filename:\s*([\w\.\-]+)', first_line, re.IGNORECASE)
        if match:
            name = match.group(1)
            if self.file_name_entry.get() != name:
                self.file_name_entry.delete(0, tk.END)
                self.file_name_entry.insert(0, name)

    def start_process(self):
        self.action_btn.config(state="disabled", text="⚡ Processing...")
        threading.Thread(target=self.run_pipeline, daemon=True).start()

    def run_pipeline(self):
        file_name = self.file_name_entry.get().strip()
        code_content = self.code_area.get("1.0", tk.END).strip()
        prog_name = file_name.split("_")[0] if "_" in file_name else APP_NAME
        target_dir = os.path.abspath(os.path.join(self.config["base_dir"], prog_name))
        full_path = os.path.join(target_dir, file_name)
        try:
            self.status_label.config(text="Saving...")
            if not os.path.exists(target_dir): os.makedirs(target_dir)
            with open(full_path, "w", encoding="utf-8") as f: f.write(code_content)
            self.status_label.config(text="Git Pushing...")
            self.execute_git(target_dir, file_name)
            self.status_label.config(text="Building EXE (E: Drive)...")
            self.execute_build(target_dir, file_name)
            self.status_label.config(text="Success!")
            messagebox.showinfo("Success", f"v{VERSION} Build Completed on E:!\n\nFolder: {target_dir}")
        except Exception as e:
            self.status_label.config(text="Failed.")
            messagebox.showerror("Error", str(e))
        finally:
            self.action_btn.config(state="normal", text="🚀 Save, Push & Build (E: Drive Focus)")

    def execute_git(self, target_dir, file_name):
        try:
            repo = git.Repo(target_dir) if os.path.exists(os.path.join(target_dir, ".git")) else git.Repo.init(target_dir)
            repo.index.add([file_name]); repo.index.commit(f"Update: {file_name} (v{VERSION})")
            if 'origin' not in [r.name for r in repo.remotes]: repo.create_remote('origin', url=self.config["github_url"])
            origin = repo.remote(name='origin')
            try: branch = repo.active_branch.name
            except: branch = "main"
            origin.push(branch)
        except Exception as e: raise Exception(f"Git failed: {e}")

    def execute_build(self, target_dir, file_name):
        dist_path = os.path.abspath(os.path.join(target_dir, "dist"))
        build_path = os.path.abspath(os.path.join(target_dir, "build"))
        output_name = os.path.splitext(file_name)[0]
        process = subprocess.run(["py", "-3.13", "-m", "PyInstaller", "--onefile", "--noconsole", f"--name={output_name}", f"--distpath={dist_path}", f"--workpath={build_path}", file_name], cwd=target_dir, shell=True, capture_output=True, text=True)
        if process.returncode != 0: raise Exception(f"Build Error: {process.stderr}")
        if not os.path.exists(os.path.join(dist_path, f"{output_name}.exe")): raise Exception("EXE not found.")

if __name__ == "__main__":
    root = tk.Tk(); app = ProgramingEnviromentApp(root); root.mainloop()

# ---ここまで---