import os
import re
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib
from datetime import datetime

matplotlib.use('TkAgg')  # 或者尝试 'Qt5Agg'

# 定义字体属性
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = font_manager.FontProperties(fname=font_path)
def process_temp_logs(path):
    log_files = []
    
    # 遍历给定路径下的所有文件
    for root, dirs, files in os.walk(path):
        for file in files:
            if re.match(r'kernel_log_\d+__\d{4}_\d{4}_\d{6}\.localtime$', file):
                log_files.append(os.path.join(root, file))
            elif re.match(r'kernel_log_\d+__\d{4}_\d{4}_\d{6}$', file):
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
            process_temp_file(file_path, all_temps)
            processed_files.add(file_path)
    
    # 打印数据长度以进行调试
    print("温度数据长度:")
    for key, value in all_temps.items():
        print(f"{key}: {len(value)}")
    
    return all_temps

def convert_kernel_log(file_path):
    # 这是一个示例函数，如果你有具体的转换逻辑，请修改它
    pass

def process_temp_file(file_path, all_temps):
    print(f"处理温度文件: {file_path}")
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
    match = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6})', line)
    if match:
        return datetime.strptime(match.group(1), '%m-%d %H:%M:%S.%f')
    return None

def process_network_logs(path):
    log_files = []
    
    # 遍历给定路径下的所有文件
    for root, dirs, files in os.walk(path):
        for file in files:
            if re.match(r'(main|sys)_log_\d+__\d{4}_\d{4}_\d{6}', file):
                log_files.append(os.path.join(root, file))
    
    # 按文件名排序,确保按顺序处理
    log_files.sort()
    
    # 用于存储所有网络数据的字典
    network_data = {
        'timestamp': [],
        'cellular_signal': [],
        'wifi_signal': [],
        'network_type': []  # 存储网络类型
    }
    
    # 处理每个日志文件
    for file_path in log_files:
        process_network_file(file_path, network_data)
    
    # 打印数据长度以进行调试
    print("网络数据长度:")
    for key, value in network_data.items():
        print(f"{key}: {len(value)}")
    
    return network_data

def process_network_file(file_path, network_data):
    print(f"处理网络文件: {file_path}")
    cellular_count = 0
    wifi_count = 0
    network_type_count = 0
    current_network_type = None
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            timestamp = extract_timestamp(line)
            if timestamp is None:
                continue

            # 匹配手机网络信号强度
            match = re.search(r'TranSignalStrengthComponentImpl: \[LTE\] dbm: (-?\d+)', line)
            if match:
                signal = int(match.group(1))
                print(f"找到手机信号: {signal} dBm, 时间戳: {timestamp}")
                update_network_data(network_data, timestamp, cellular_signal=signal, network_type=current_network_type)
                cellular_count += 1
                continue

            # 匹配WiFi信号强度
            match = re.search(r'====>>rssi :(-?\d+)', line)
            if match:
                signal = int(match.group(1))
                print(f"找到WiFi信号: {signal} dBm, 时间戳: {timestamp}")
                update_network_data(network_data, timestamp, wifi_signal=signal, network_type=current_network_type)
                wifi_count += 1
                continue

            # 匹配网络类型变化
            match = re.search(r'NetworkStatusMonitor: onNetworkTypeChanged (\w+) => (\w+)', line)
            if match:
                old_type, new_type = match.group(1), match.group(2)
                if current_network_type != new_type:  # 网络类型变化才记录
                    print(f"网络类型变化: {old_type} => {new_type}, 时间戳: {timestamp}")
                    update_network_data(network_data, timestamp, network_type=new_type)
                current_network_type = new_type
                network_type_count += 1

    print(f"文件 {file_path} 中找到 {cellular_count} 个手机信号, {wifi_count} 个WiFi信号, 和 {network_type_count} 个网络类型变化")
    print(f"最后的网络类型: {current_network_type}")

def update_network_data(network_data, timestamp, cellular_signal=None, wifi_signal=None, network_type=None):
    network_data['timestamp'].append(timestamp)
    network_data['cellular_signal'].append(cellular_signal)
    network_data['wifi_signal'].append(wifi_signal)
    network_data['network_type'].append(network_type)
    if network_type is not None:
        print(f"更新网络类型: {network_type}, 时间戳: {timestamp}")

def plot_data(all_temps, network_data):
    print("开始绘图...")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12), sharex=True)
 # 添加全局图例，放置在图表外部
    handles = [
        plt.Line2D([0], [0], color='c', linestyle='--', alpha=0.2, lw=2, label='ANR Warning'),
        plt.Line2D([0], [0], color='r', linestyle='--', alpha=0.2, lw=2, label='App Not Responding')
    ]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, 0.97), ncol=2)
    # 绘制温度数据
    if all_temps['tmp1']:
        ax1.plot(all_temps['timestamp'], all_temps['tmp1'], label='温度1', color='red')
    if all_temps['tmp2']:
        ax1.plot(all_temps['timestamp'], all_temps['tmp2'], label='温度2', color='blue')
    if all_temps['tmp3']:
        ax1.plot(all_temps['timestamp'], all_temps['tmp3'], label='温度3', color='green')
    if all_temps['batt_temp_kernel']:
        ax1.plot(all_temps['timestamp'], all_temps['batt_temp_kernel'], label='电池温度 (Kernel)', color='purple')
    if all_temps['batt_temp_main']:
        ax1.plot(all_temps['timestamp'], all_temps['batt_temp_main'], label='电池温度 (Main)', color='orange')
    if all_temps['batt_temp_healthd']:
        ax1.plot(all_temps['timestamp'], all_temps['batt_temp_healthd'], label='电池温度 (Healthd)', color='brown')
    if all_temps['wmt']:
        ax1.plot(all_temps['timestamp'], all_temps['wmt'], label='无线通讯温度', color='cyan')
    if all_temps['batt_level_main']:
        ax1.plot(all_temps['timestamp'], all_temps['batt_level_main'], label='电池电量 (Main)', color='magenta')
    if all_temps['batt_level_kernel']:
        ax1.plot(all_temps['timestamp'], all_temps['batt_level_kernel'], label='电池电量 (Kernel)', color='gray')

    ax1.set_ylabel('温度 (°C) / 电量 (%)', fontproperties=font_prop)
    ax1.set_title('温度数据趋势图', fontproperties=font_prop)
    ax1.legend(loc='best', prop=font_prop)

    # 绘制网络数据
    cellular_signals = [s for s in network_data['cellular_signal'] if s is not None]
    wifi_signals = [s for s in network_data['wifi_signal'] if s is not None]

    if cellular_signals:
        cellular_data = [(t, s) for t, s in zip(network_data['timestamp'], network_data['cellular_signal']) if s is not None]
        timestamps, signals = zip(*cellular_data)
        ax2.plot(timestamps, signals, label='手机网络信号强度', color='blue')
    
    if wifi_signals:
        wifi_data = [(t, s) for t, s in zip(network_data['timestamp'], network_data['wifi_signal']) if s is not None]
        timestamps, signals = zip(*wifi_data)
        ax2.plot(timestamps, signals, label='WiFi信号强度', color='green')
    
    ax2.set_xlabel('时间', fontproperties=font_prop)
    ax2.set_ylabel('信号强度 (dBm)', fontproperties=font_prop)
    ax2.set_title('网络信号强度趋势图', fontproperties=font_prop)
    ax2.legend(loc='best', prop=font_prop)

    fig.autofmt_xdate()
    plt.tight_layout()

    # 确保y轴显示负值
    all_signals = cellular_signals + wifi_signals
    if all_signals:
        ax2.set_ylim(bottom=min(all_signals) - 10, top=max(all_signals) + 10)

    plt.show()

if __name__ == "__main__":
    log_path = input("请输入日志文件路径: ")
    all_temps = process_temp_logs(log_path)
    network_data = process_network_logs(log_path)
    plot_data(all_temps, network_data)
