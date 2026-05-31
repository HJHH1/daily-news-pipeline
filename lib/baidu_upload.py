import subprocess

def upload_to_baidu(local_file: str, remote_path: str, config):
    check = subprocess.run(['bypy', 'info'], capture_output=True, text=True)
    if check.returncode != 0:
        raise Exception("百度网盘未登录，请先在终端执行 bypy info 进行授权")
    cmd = f'bypy upload "{local_file}" "{remote_path}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"上传失败: {result.stderr}")
