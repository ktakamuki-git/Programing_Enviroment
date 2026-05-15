# filename: ProgramingEnviroment_v1.5.py
import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
import git
import re
from datetime import datetime

class GitManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Code Version Manager - Auto Organizer v1.5")
        self.root.geometry("700x650")
        self.root.configure(bg="#f0f0f0")

        # 🚀 ベースとなる保存先ディレクトリを固定
        self.base_dir = r"D:\gemini"
        
        # もし D:\gemini 自体がなければ作成
        if not os.path.exists(self.base_dir):
            try:
                os.makedirs(self.base_dir)
            except:
                # Dドライブがないなどの場合は実行場所にする
                self.base_dir = os.getcwd()

        self.repo = None
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text="Git Version Manager (Auto Folder)", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)

        file_frame = tk.Frame(self.root, bg="#f0f0f0")
        file_frame.pack(fill="x", padx=20)
        tk.Label(file_frame, text="FileName:", bg="#f0f0f0").pack(side="left")
        self.file_name_entry = tk.Entry(file_frame)
        self.file_name_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.file_name_entry.insert(0, "main_v1.0.py")

        tk.Label(self.root, text="Paste code here:", bg="#f0f0f0").pack(anchor="w", padx=20, pady=(10, 0))
        self.code_area = scrolledtext.ScrolledText(self.root, height=15, font=("Consolas", 10))
        self.code_area.pack(fill="both", expand=True, padx=20, pady=5)
        self.code_area.bind("<KeyRelease>", self.auto_analyze_code)

        commit_frame = tk.Frame(self.root, bg="#f0f0f0")
        commit_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(commit_frame, text="Commit Message:", bg="#f0f0f0").pack(side="left")
        self.commit_entry = tk.Entry(commit_frame)
        self.commit_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.commit_entry.insert(0, f"Update {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(pady=20)

        self.save_btn = tk.Button(btn_frame, text="Save & Commit & Push", command=self.process_git, 
                                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=20, pady=10)
        self.save_btn.pack(side="left", padx=10)

    def auto_analyze_code(self, event=None):
        first_line = self.code_area.get("1.0", "1.end").strip()
        match = re.search(r'(?:#|//|--)\s*filename:\s*([\w\.-]+)_v(\d+\.\d+)\.py', first_line, re.IGNORECASE)
        if match:
            base_name, current_ver = match.group(1), float(match.group(2))
            suggested_name = f"{base_name}_v{round(current_ver + 0.1, 1)}.py"
            if suggested_name not in self.file_name_entry.get():
                self.file_name_entry.delete(0, tk.END)
                self.file_name_entry.insert(0, suggested_name)

    def process_git(self):
        file_name = self.file_name_entry.get().strip()
        code_content = self.code_area.get("1.0", tk.END).strip()
        commit_msg = self.commit_entry.get().strip()

        if not file_name or not code_content: return

        # 🚀 フォルダ名の決定 (例: Hello_World_v1.1.py -> Hello_World)
        folder_name = "DefaultProject"
        folder_match = re.search(r'(.+)_v\d+\.\d+\.py', file_name)
        if folder_match:
            folder_name = folder_match.group(1)
        
        target_dir = os.path.join(self.base_dir, folder_name)

        try:
            # フォルダがなければ作成
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            # ファイル保存
            full_path = os.path.join(target_dir, file_name)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code_content)

            # Git操作 (そのフォルダをGit管理する)
            repo = None
            try:
                if os.path.exists(os.path.join(target_dir, ".git")):
                    repo = git.Repo(target_dir)
                else:
                    repo = git.Repo.init(target_dir)
                
                repo.index.add([file_name])
                repo.index.commit(commit_msg)
                
                # リポジトリURLはフォルダ名に基づいて動的に変える（必要なら）
                # ここでは前回のあなたのリポジトリをデフォルトに設定
                if 'origin' not in [r.name for r in repo.remotes]:
                    repo.create_remote('origin', url='https://github.com/ktakamuki-git/Programing_Enviroment.git')
                
                origin = repo.remote(name='origin')
                current_branch = repo.active_branch.name
                origin.push(current_branch)
                
                messagebox.showinfo("Success", f"'{folder_name}' フォルダに保存し、GitHubへ送信しました！")
            except Exception as git_e:
                messagebox.showinfo("Local Success", f"D:\\gemini\\{folder_name} に保存しました。\nGit Error: {git_e}")

        except Exception as e:
            messagebox.showerror("Error", f"エラー: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitManagerApp(root)
    root.mainloop()