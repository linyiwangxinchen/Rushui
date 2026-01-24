from PyInstaller.__main__ import run
import os

if __name__ == '__main__':
    opts = [
        'MainWindow.py',
        '--onefile',
        '--noconsole',
        '--name=Amphoreus',
        '--clean',  # 添加清理选项
    ]


    # opts = [
    #     'MainWindow.py',
    #     '--onedir',
    #     '--windowed',
    #     '--name=Amphoreus',
    #     '--clean',  # 添加清理选项
    # ]


    print(f"打包选项: {opts}")
    run(opts)