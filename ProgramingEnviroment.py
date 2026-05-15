# filename: ProgramingEnviroment.py
import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
import git
import re
from datetime import datetime

class GitManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Code Version Manager - Pro v1.2")
        self.root.geometry("700x650")
        self.root.configure(bg="#f0f0f0")

        self.repo_path = os.getcwd()
        self.repo = None
        
        # 🚀 起動時に自動でGit状態をチェック
        self.auto_init_repo()
        
        self.setup_ui()

    def auto_init_repo(self):
        """現在のフォルダがGit管理下か確認し、自動で読み込む"""
        try:
            if os.path.exists(os.path.join(self.repo_path, ".git")):
                self.repo = git.Repo(self.repo_path)
            else:
                # .gitがなければ自動で作る（必要なら）
                self.repo = git.Repo.init(self.repo_path)
        except Exception as e:
            print(f"Init Error: {e}")

    def setup_ui(self):
        tk.Label(self.root, text="Git Version Manager", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)

        # ファイル名入力
        file_frame = tk.Frame(self.root, bg="#f0f0f0")
        file_frame.pack(fill="x", padx=20)
        tk.Label(file_frame, text="FileName:", bg="#f0f0f0").pack(side="left")
        self.file_name_entry = tk.Entry(file_frame)
        self.file_name_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.file_name_entry.insert(0, "main.py")

        # コードエリア
        tk.Label(self.root, text="Paste code here (1st line: # filename: example.py):", bg="#f0f0f0").pack(anchor="w", padx=20, pady=(10, 0))
        self.code_area = scrolledtext.ScrolledText(self.root, height=15, font=("Consolas", 10))
        self.code_area.pack(fill="both", expand=True, padx=20, pady=5)
        self.code_area.bind("<KeyRelease>", self.auto_extract_filename)

        # コミットメッセージ
        commit_frame = tk.Frame(self.root, bg="#f0f0f0")
        commit_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(commit_frame, text="Commit Message:", bg="#f0f0f0").pack(side="left")
        self.commit_entry = tk.Entry(commit_frame)
        self.commit_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.commit_entry.insert(0, f"Update {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # 操作ボタン
        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(pady=20)

        self.save_btn = tk.Button(btn_frame, text="Save & Commit & Push", command=self.process_git, 
                                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=20, pady=10)
        self.save_btn.pack(side="left", padx=10)

    def auto_extract_filename(self, event=None):
        first_line = self.code_area.get("1.0", "1.end").strip()
        match = re.search(r'(?:#|//|--)\s*filename:\s*([\w\.-]+)', first_line, re.IGNORECASE)
        if match:
            extracted_name = match.group(1)
            if self.file_name_entry.get() != extracted_name:
                self.file_name_entry.delete(0, tk.END)
                self.file_name_entry.insert(0, extracted_name)

    def process_git(self):
        file_name = self.file_name_entry.get().strip()
        code_content = self.code_area.get("1.0", tk.END).strip()
        commit_msg = self.commit_entry.get().strip()

        if not file_name or not code_content:
            messagebox.showwarning("Warning", "Please enter filename and code.")
            return

        try:
            # ファイル保存
            with open(os.path.join(self.repo_path, file_name), "w", encoding="utf-8") as f:
                f.write(code_content)

            # Git操作
            if not self.repo:
                self.repo = git.Repo(self.repo_path)

            self.repo.index.add([file_name])
            self.repo.index.commit(commit_msg)
            
            # Push試行
            try:
                # originがない場合はGitHubのURLを再セット
                if 'origin' not in [r.name for r in self.repo.remotes]:
                    self.repo.create_remote('origin', url='https://github.com/ktakamuki-git/Programing_Enviroment.git')
                
                origin = self.repo.remote(name='origin')
                origin.push('main') # 明示的にmainブランチをPush
                messagebox.showinfo("Success", f"'{file_name}' をGitHubにPushしました！")
            except Exception as e:
                messagebox.showinfo("Local Success", f"保存・コミットは完了しましたが、Pushに失敗しました。\n詳細: {e}")

        except Exception as e:
            messagebox.showerror("Error", f"エラーが発生しました: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitManagerApp(root)
    root.mainloop()