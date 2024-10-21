import os
import glob
import subprocess
import re
from datetime import datetime
import sys

def convert_kernel_log_to_localtime(log_file):
    localtime_file = f"{log_file}.localtime"
    print("当前工作目录:", os.getcwd())
    
    # 获取 ktime_convert.exe 的路径
    ktime_convert_path = get_executable_path()  # 新增获取路径的函数

    try:
        subprocess.run([ktime_convert_path, log_file], check=True)  # 使用获取的路径
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running ktime_convert.exe: {e}")
        return None
    
    if not os.path.exists(localtime_file):
        print(f"Error: The .localtime file '{localtime_file}' was not created.")
        return None

    return localtime_file

def get_executable_path():
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        return os.path.join(sys._MEIPASS, 'ktime_convert.exe')
    else:
        # 如果是源代码
        return 'ktime_convert.exe'

def load_log_annotations(file_path):
    annotations = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # 忽略以 '#' 开头的注释（表示禁用的匹配）
            if line.strip().startswith('#'):
                continue
            # 使用正则表达式提取键值对
            match = re.match(r'"(.*?)":\s*"(.*?)"', line.strip())
            if match:
                key = match.group(1)
                value = match.group(2)
                annotations[key] = value  # 去掉多余的空格
    return annotations

def extract_timestamp(line):
    try:
        match = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
        if match:
            timestamp_str = match.group(1)
            current_year = datetime.now().year
            timestamp_str_with_year = f"{current_year}-{timestamp_str}"
            timestamp = datetime.strptime(timestamp_str_with_year, '%Y-%m-%d %H:%M:%S.%f')
            return timestamp
        else:
            return None
    except (ValueError, IndexError) as e:
        print(f"无法解析时间戳，跳过该行: {line.strip()}，错误信息: {e}")
        return None

def remove_original_timestamp(line):
    # 使用正则去除日志中原始的时间戳部分，只应用于简约日志
    line = re.sub(r'\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+', '', line, 1).strip()
    return line

def merge_logs(folder_path):
    log_files = glob.glob(os.path.join(folder_path, 'main_log_*')) + \
                glob.glob(os.path.join(folder_path, 'sys_log_*')) + \
                glob.glob(os.path.join(folder_path, 'events_log_*')) + \
                glob.glob(os.path.join(folder_path, 'radio_log_*')) + \
                glob.glob(os.path.join(folder_path, 'kernel_log_*'))

    print(f"找到的日志文件: {log_files}")
    
    merged_logs = []
    simplified_logs = []

    log_annotations = load_log_annotations('log过滤器.txt')

    for log_file in log_files:
        if 'kernel_log_' in log_file and not log_file.endswith('.localtime'):
            localtime_file = convert_kernel_log_to_localtime(log_file)
            if localtime_file:
                log_file = localtime_file

        with open(log_file, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                timestamp = extract_timestamp(line)
                if timestamp:
                    # 保留 merged_logs 中的完整日志行，不修改原始时间戳
                    merged_logs.append((timestamp, line.strip()))

                    # 简约日志中去掉原始时间戳，并加上中文注释
                    line_without_timestamp = remove_original_timestamp(line)
                    annotation = ''
                    for key, value in log_annotations.items():
                        if key in line:  
                            annotation = value
                            print(f"匹配到关键字: {key} -> {value}")
                            break

                    if annotation:
                        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
                        simplified_logs.append(f"{timestamp_str} [{annotation}] {line_without_timestamp}")
                else:
                    print(f"无效时间戳，跳过该行: {line.strip()}")

    # 按时间戳排序
    merged_logs.sort(key=lambda x: x[0])

    # 输出完整的 merged_logs 文件
    output_file_path = os.path.join(folder_path, '完整log集合.log')
    os.makedirs(folder_path, exist_ok=True)

    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        for _, log in merged_logs:
            output_file.write(log + '\n')

    print(f"合并后的日志文件已创建: {output_file_path}")

    # 输出简约日志，只保留一个格式化的时间戳并加上注释
    simplified_logs.sort()

    simplified_log_file_path = os.path.join(folder_path, '简约log.log')
    with open(simplified_log_file_path, 'w', encoding='utf-8') as simplified_file:
        for log in simplified_logs:
            simplified_file.write(log + '\n')

    print(f"简约日志文件已创建: {simplified_log_file_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = input("请输入APlog文件夹路径: ").strip()
    merge_logs(log_file)
