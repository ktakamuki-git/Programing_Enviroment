# filename: ProgramingEnviroment_v2.1.0.py
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
from datetime import datetime

# --- バージョン定義 ---
APP_NAME = "ProgramingEnviroment"
VERSION = "2.1.0"
TARGET_PYTHON = "3.13"

class ProgramingEnviromentApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - v{VERSION}")
        self.root.geometry("900x950") # ログウィンドウ分、少し縦に拡張
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

        # ヘッダー
        header = tk.Frame(main_frame, bg="#f8f9fa")
        header.pack(fill="x")
        tk.Label(header, text=f"{APP_NAME} v{VERSION}", font=("Segoe UI", 18, "bold"), bg="#f8f9fa", fg="#1a73e8").pack(side="left")
        tk.Button(header, text="⚙ Settings", command=self.open_settings, bg="#dee2e6", bd=0, padx=10).pack(side="right")

        self.path_label = tk.Label(main_frame, text=f"Target: {self.config['base_dir']}", bg="#f8f9fa", fg="#5f6368")
        self.path_label.pack(anchor="w", pady=(0, 5))

        # ファイル名入力
        tk.Label(main_frame, text="File Name:", bg="#f8f9fa", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.file_name_entry = tk.Entry(main_frame, font=("Consolas", 11), bd=1, relief="solid")
        self.file_name_entry.pack(fill="x", pady=(0, 10))
        self.file_name_entry.insert(0, f"{APP_NAME}_v{VERSION}.py")

        # ソースコード入力
        tk.Label(main_frame, text="Source Code:", bg="#f8f9fa", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.code_area = scrolledtext.ScrolledText(main_frame, height=20, font=("Consolas", 10), bd=1, relief="solid")
        self.code_area.pack(fill="both", expand=True, pady=(0, 10))
        self.code_area.bind("<KeyRelease>", self.auto_extract_filename)

        # 実行ボタン
        self.action_btn = tk.Button(main_frame, text="🚀 Save, Push & Build EXE", command=self.start_process, 
                                   bg="#1a73e8", fg="white", font=("Segoe UI", 12, "bold"), pady=8, bd=0)
        self.action_btn.pack(fill="x", pady=(0, 10))

        # ログウィンドウ（新機能）
        tk.Label(main_frame, text="Execution Log:", bg="#f8f9fa", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.log_area = scrolledtext.ScrolledText(main_frame, height=12, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_area.pack(fill="both", expand=False)
        self.log_area.tag_config("info", fg="#9cdcfe")
        self.log_area.tag_config("error", fg="#f44747")
        self.log_area.tag_config("success", fg="#b5cea8")

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
        self.log_area.delete("1.0", tk.END)
        self.action_btn.config(state="disabled", text="⚡ Processing...")
        threading.Thread(target=self.run_pipeline, daemon=True).start()

    def run_pipeline(self):
        file_name = self.file_name_entry.get().strip()
        code_content = self.code_area.get("1.0", tk.END).strip()
        prog_name = file_name.split("_")[0] if "_" in file_name else APP_NAME
        target_dir = os.path.abspath(os.path.join(self.config["base_dir"], prog_name))
        full_path = os.path.join(target_dir, file_name)

        try:
            self.log("--- Starting Pipeline v2.1.0 ---")
            
            # 1. フォルダ準備と古いファイルの整理（新機能）
            if not os.path.exists(target_dir): os.makedirs(target_dir)
            self.organize_old_files(target_dir, file_name)

            # 2. 保存
            self.log(f"Saving source: {file_name}")
            with open(full_path, "w", encoding="utf-8") as f: f.write(code_content)

            # 3. Git Push
            self.log("Initializing Git operations...")
            self.execute_git(target_dir, file_name)

            # 4. ビルド（リアルタイム表示）
            self.log("Launching PyInstaller (Target Python 3.13)...")
            self.execute_build(target_dir, file_name)

            self.log("All processes completed successfully!", "success")
            messagebox.showinfo("Success", f"Build v{VERSION} Ready!\nCheck 'old' folder for previous versions.")

        except Exception as e:
            self.log(f"CRITICAL ERROR: {str(e)}", "error")
            messagebox.showerror("Pipeline Failed", str(e))
        finally:
            self.action_btn.config(state="normal", text="🚀 Save, Push & Build EXE")

    def organize_old_files(self, target_dir, current_file_name):
        """現在のバージョン以外のファイルを old フォルダへ移動"""
        old_dir = os.path.join(target_dir, "old")
        dist_dir = os.path.join(target_dir, "dist")
        current_base = os.path.splitext(current_file_name)[0]

        self.log("Organizing old versions...")
        if not os.path.exists(old_dir): os.makedirs(old_dir)

        # プロジェクト直下の古い .py などを移動
        for f in os.listdir(target_dir):
            if f.endswith((".py", ".spec")) and f != current_file_name and f != f"{current_base}.spec":
                if f == "old" or f == "dist" or f == "build": continue
                self.log(f"Moving {f} to old/")
                shutil.move(os.path.join(target_dir, f), os.path.join(old_dir, f))

        # dist 内の古い .exe を移動
        if os.path.exists(dist_dir):
            for f in os.listdir(dist_dir):
                if f.endswith(".exe") and f != f"{current_base}.exe":
                    self.log(f"Moving old EXE: {f} to old/")
                    shutil.move(os.path.join(dist_dir, f), os.path.join(old_dir, f))

    def execute_git(self, target_dir, file_name):
        try:
            repo = git.Repo(target_dir) if os.path.exists(os.path.join(target_dir, ".git")) else git.Repo.init(target_dir)
            repo.index.add([file_name])
            repo.index.commit(f"Auto-update: {file_name} (v{VERSION})")
            if 'origin' not in [r.name for r in repo.remotes]:
                repo.create_remote('origin', url=self.config["github_url"])
            origin = repo.remote(name='origin')
            branch = "main"
            try: branch = repo.active_branch.name
            except: pass
            origin.push(branch)
            self.log(f"Git push successful to branch: {branch}", "success")
        except Exception as e:
            self.log(f"Git warning: {e}", "error")

    def execute_build(self, target_dir, file_name):
        dist_path = os.path.abspath(os.path.join(target_dir, "dist"))
        build_path = os.path.abspath(os.path.join(target_dir, "build"))
        output_name = os.path.splitext(file_name)[0]

        cmd = [
            "py", "-3.13", "-m", "PyInstaller",
            "--onefile", "--noconsole",
            f"--name={output_name}",
            f"--distpath={dist_path}",
            f"--workpath={build_path}",
            file_name
        ]

        # リアルタイムでログを取得するために Popen を使用
        process = subprocess.Popen(
            cmd, cwd=target_dir, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                self.log(line.strip())

        if process.returncode != 0:
            raise Exception("PyInstaller process returned non-zero exit code.")
        
        if os.path.exists(os.path.join(dist_path, f"{output_name}.exe")):
            self.log(f"EXE generated: {output_name}.exe", "success")
        else:
            raise Exception("EXE file not found after build.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProgramingEnviromentApp(root)
    root.mainloop()

# ---ここまで---