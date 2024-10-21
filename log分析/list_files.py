import os
import re
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib import font_manager
import subprocess
# 温度数据处理
def process_log_files(path):
    log_files = []
    
    # 遍历给定路径下的所有文件
    for root, dirs, files in os.walk(path):
        for file in files:
            if re.match(r'kernel_log_\d+__\d{4}_\d{4}_\d{6}\.localtime$', file):
                log_files.append(os.path.join(root, file))
            elif re.match(r'kernel_log_\d+__\d{4}_\d{4}_\d{6}$', file):
                # 如果找到非.localtime的kernel日志,尝试转换
                convert_kernel_log(os.path.join(root, file))
                localtime_file = os.path.join(root, file + '.localtime')
                if os.path.exists(localtime_file):
                    log_files.append(localtime_file)
            elif re.match(r'main_log_\d+__\d{4}_\d{4}_\d{6}', file):
                log_files.append(os.path.join(root, file))
    
    # 按文件名排序,确保按顺序处理
    log_files.sort()
    
    # 用于存储所有温度数据的字典
    all_temps = {
        'timestamp': [], 'tmp1': [], 'tmp2': [], 'tmp3': [], 
        'batt_temp_kernel': [], 'batt_temp_main': [], 'batt_temp_healthd': [],
        'wmt': [], 'batt_level_main': [], 'batt_level_kernel': []
    }
    
    # 处理每个日志文件
    processed_files = set()  # 用于跟踪已处理的文件
    for file_path in log_files:
        if file_path not in processed_files:
            process_file(file_path, all_temps)
            processed_files.add(file_path)
    
    # 打印数据长度以进行调试
    print("数据长度:")
    for key, value in all_temps.items():
        print(f"{key}: {len(value)}")
    
    # 绘制图表
    plot_temperatures(all_temps)

def convert_kernel_log(file_path):
    ktime_convert = os.path.join(os.path.dirname(__file__), 'ktime_convert.exe')
    if os.path.exists(ktime_convert):
        try:
            subprocess.run([ktime_convert, file_path], check=True)
            print(f"成功转换文件: {file_path}")
        except subprocess.CalledProcessError:
            print(f"转换文件失败: {file_path}")
    else:
        print("未找到 ktime_convert.exe 文件,无法转换 kernel 日志")

def process_file(file_path, all_temps):
    print(f"处理文件: {file_path}")
    wmt_count = 0
    processed_timestamps = set()
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            timestamp = extract_timestamp(line)
            if timestamp is None or timestamp in processed_timestamps:
                continue
            processed_timestamps.add(timestamp)

            # 匹配MTK_BH温度 (kernel_log)
            match = re.search(r'MTK_BH:.*tmp:(\d+) (\d+) (\d+)', line)
            if match:
                update_temps(all_temps, timestamp, tmp1=int(match.group(1)), tmp2=int(match.group(2)), tmp3=int(match.group(3)))
                continue

            # 匹配电池温度 (kernel_log)
            match = re.search(r'orignal batt_temp = (\d+)', line)
            if match:
                update_temps(all_temps, timestamp, batt_temp_kernel=int(match.group(1)) / 10)
                continue

            # 匹配无线通讯内部温度 (kernel_log)
            match = re.search(r'wmt_dev_tm_temp_query.*current_temp = (0x[0-9a-fA-F]+)', line)
            if match:
                wmt_temp = int(match.group(1), 16)
                update_temps(all_temps, timestamp, wmt=wmt_temp)
                wmt_count += 1
                print(f"找到无线通讯温度: {wmt_temp}°C, 时间戳: {timestamp}")
                continue

            # 匹配电池电量和温度 (main_log)
            match = re.search(r'BatteryLabService: current level == (\d+), temperature == (\d+)', line)
            if match:
                update_temps(all_temps, timestamp, batt_temp_main=int(match.group(2)) / 10, batt_level_main=int(match.group(1)))
                continue

            # 匹配kernel日志中的电池信息
            match = re.search(r'healthd: battery l=(\d+) v=\d+ t=([\d.]+)', line)
            if match:
                update_temps(all_temps, timestamp, batt_level_kernel=int(match.group(1)), batt_temp_healthd=float(match.group(2)))
                continue

    print(f"文件 {file_path} 中找到 {wmt_count} 个无线通讯温度数据点")

def update_temps(all_temps, timestamp, tmp1=None, tmp2=None, tmp3=None, 
                 batt_temp_kernel=None, batt_temp_main=None, batt_temp_healthd=None, 
                 wmt=None, batt_level_main=None, batt_level_kernel=None):
    all_temps['timestamp'].append(timestamp)
    all_temps['tmp1'].append(tmp1)
    all_temps['tmp2'].append(tmp2)
    all_temps['tmp3'].append(tmp3)
    all_temps['batt_temp_kernel'].append(batt_temp_kernel)
    all_temps['batt_temp_main'].append(batt_temp_main)
    all_temps['batt_temp_healthd'].append(batt_temp_healthd)
    if wmt is not None:
        print(f"更新无线通讯温度: {wmt}°C, 时间戳: {timestamp}")
    all_temps['wmt'].append(wmt)
    all_temps['batt_level_main'].append(batt_level_main)
    all_temps['batt_level_kernel'].append(batt_level_kernel)

def extract_timestamp(line):
    # 首先尝试匹配kernel日志的时间戳格式
    match = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6})', line)
    if match:
        return datetime.strptime(match.group(1), '%m-%d %H:%M:%S.%f')
    
    # 如果没有匹配到,尝试匹配healthd日志的时间戳格式
    match = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6})', line)
    if match:
        return datetime.strptime(match.group(1), '%m-%d %H:%M:%S.%f')
    
    return None

def plot_temperatures(temps):
    font_path = 'C:/Windows/Fonts/simhei.ttf'
    font_prop = font_manager.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    
    plt.figure(figsize=(12, 6))
    
    label_map = {
        'tmp1': 'MTK_BH 温度1',
        'tmp2': 'MTK_BH 温度2',
        'tmp3': 'MTK_BH 温度3',
        'batt_temp_kernel': '电池温度(kernel)',
        'batt_temp_main': '电池温度(main)',
        'batt_temp_healthd': '电池温度(healthd)',
        'wmt': '无线通讯温度',
        'batt_level_main': '电池电量(main)',
        'batt_level_kernel': '电池电量(kernel)'
    }
    
    color_map = {
        'tmp1': 'red',
        'tmp2': 'blue',
        'tmp3': 'green',
        'batt_temp_kernel': 'orange',
        'batt_temp_main': 'pink',
        'batt_temp_healthd': 'brown',
        'wmt': 'purple',
        'batt_level_main': 'black',
        'batt_level_kernel': 'gray'
    }
    
    for key in label_map.keys():
        valid_data = [(t, v) for t, v in zip(temps['timestamp'], temps[key]) if v is not None]
        print(f"{key}: {len(valid_data)} 个有效数据点")
        if valid_data:
            timestamps, values = zip(*valid_data)
            if 'batt_level' in key:
                plt.plot(timestamps, values, label=label_map[key], color=color_map[key], linestyle='--')
            else:
                plt.plot(timestamps, values, label=label_map[key], color=color_map[key])

    plt.xlabel('时间', fontproperties=font_prop)
    plt.ylabel('温度 (°C) / 电池电量 (%)', fontproperties=font_prop)
    plt.title('温度和电池电量趋势图', fontproperties=font_prop)
    plt.legend(loc='best', prop=font_prop)
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    log_path = input("请输入日志文件路径: ")
    process_log_files(log_path)