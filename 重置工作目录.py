import os
import shutil
from git import Repo

def delete_untracked_files():
    repo = Repo(os.getcwd())

    untracked_files = repo.untracked_files
    if not untracked_files:
        print("没有需要删除的文件。")
        return

    for file in untracked_files:
        path = os.path.join(os.getcwd(), file)
        print(f"正在删除 {path}...")
        try:
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
        except Exception as e:
            print(f"删除文件 {path} 时出现错误: {str(e)}")
            continue

    print("清理完成。")

delete_untracked_files()