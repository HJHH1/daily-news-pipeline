import os, sys, yaml, datetime, subprocess
from pathlib import Path
from lib.deepseek_api import deepseek_chat
from lib.baidu_upload import upload_to_baidu
from lib.doc_generator import text_to_docx

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

ALLOWED_ROOTS = [
    config['paths']['project_dir'],
    config['paths']['news_content_dir']
]

def safe_path(p: str) -> Path:
    path = Path(p).resolve()
    for root in ALLOWED_ROOTS:
        root_path = Path(root).resolve()
        try:
            path.relative_to(root_path)
            return path
        except ValueError:
            continue
    raise PermissionError(f"禁止访问路径: {p}")

class PipelineError(Exception):
    pass

def step1_run_scraper():
    script = safe_path(os.path.join(config['paths']['project_dir'],
                                    config['paths']['scraper_script']))
    result = subprocess.run(['python3', str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        raise PipelineError(f"爬虫运行失败: {result.stderr}")

def step2_upload_parts():
    today = datetime.date.today()
    date_prefix = today.strftime('%Y-%m-%d')
    export_dir = safe_path(os.path.join(config['paths']['project_dir'],
                                        config['paths']['exports_dir']))
    for part in ['part1', 'part2', 'part3']:
        filename = f"{date_prefix}_{part}.txt"
        local_file = export_dir / filename
        if local_file.exists():
            upload_to_baidu(str(local_file), f"{config['paths']['baidu_remote_news_collection']}/{filename}", config)
        else:
            raise PipelineError(f"缺失文件: {local_file}")

def step3_create_daily_txt():
    today = datetime.date.today()
    filename = today.strftime('%Y年%m月%d日') + '.txt'
    news_dir = safe_path(config['paths']['news_content_dir'])
    file_path = news_dir / filename
    file_path.touch(exist_ok=True)
    return file_path

def step4_analyze_parts(daily_txt_path):
    today = datetime.date.today()
    date_prefix = today.strftime('%Y-%m-%d')
    export_dir = safe_path(os.path.join(config['paths']['project_dir'],
                                        config['paths']['exports_dir']))
    prompt = config['prompts']['analysis']
    for part in ['part1', 'part2', 'part3']:
        file = export_dir / f"{date_prefix}_{part}.txt"
        content = file.read_text(encoding='utf-8')
        full_msg = prompt + "\n\n" + content
        resp = deepseek_chat(config, full_msg)
        with open(daily_txt_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n===== {part} 分析结果 =====\n")
            f.write(resp)

def step5_upload_daily(daily_txt_path):
    upload_to_baidu(str(daily_txt_path), f"{config['paths']['baidu_remote_news_organized']}/{daily_txt_path.name}", config)

def step6_refine(daily_txt_path):
    content = daily_txt_path.read_text(encoding='utf-8')
    prompt = config['prompts']['refine']
    resp = deepseek_chat(config, prompt + "\n\n" + content)
    news_dir = safe_path(config['paths']['news_content_dir'])
    refine_path = news_dir / (daily_txt_path.stem + "新闻精炼.txt")
    refine_path.write_text(resp, encoding='utf-8')
    return refine_path

def step7_upload_refine(refine_path):
    upload_to_baidu(str(refine_path), f"{config['paths']['baidu_remote_news_organized']}/{refine_path.name}", config)

def step8_word(refine_path):
    today = datetime.date.today()
    news_dir = safe_path(config['paths']['news_content_dir'])
    word_path = news_dir / f"新闻精炼版{today.strftime('%Y年%m月%d日')}.docx"
    text_to_docx(refine_path.read_text(encoding='utf-8'), str(word_path))
    upload_to_baidu(str(word_path), f"{config['paths']['baidu_remote_news_organized']}/{word_path.name}", config)

try:
    step1_run_scraper()
    step2_upload_parts()
    daily = step3_create_daily_txt()
    step4_analyze_parts(daily)
    step5_upload_daily(daily)
    refine = step6_refine(daily)
    step7_upload_refine(refine)
    step8_word(refine)
    print("SUCCESS: 全流程完成")
except PipelineError as e:
    print(f"FAIL: {e}")
    sys.exit(1)
