from PyInstaller.__main__ import run
import os

if __name__ == '__main__':
    opts = [
        'MainWindow.py',
        '--onefile',
        '--windowed',
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

    # 确保 about 文件夹路径正确
    about_source = './about'
    about_target = 'about'

    # 检查源文件夹是否存在
    if os.path.exists(about_source) and os.path.isdir(about_source):
        print(f"✓ 找到 about 文件夹: {about_source}")
        print(f"文件夹内容: {os.listdir(about_source)}")

        # 使用正确的路径分隔符
        add_data_arg = f'--add-data={about_source}{os.pathsep}{about_target}'
        opts.append(add_data_arg)
        print(f"添加数据参数: {add_data_arg}")
    else:
        print(f"✗ 未找到 about 文件夹: {about_source}")

    print(f"打包选项: {opts}")
    run(opts)