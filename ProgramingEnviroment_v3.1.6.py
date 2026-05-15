# filename: ProgramingEnviroment_v3.1.6.py
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
VERSION = "3.1.6"
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
        tk.Button(btn_frame, text="📋 Copy Log", command=self.copy_log_