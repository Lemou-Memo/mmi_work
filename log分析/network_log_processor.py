import os
import re
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib

matplotlib.use('TkAgg')  # 或者尝试 'Qt5Agg'

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
        process_file(file_path, network_data)
    
    # 打印数据长度以进行调试
    print("数据长度:")
    for key, value in network_data.items():
        print(f"{key}: {len(value)}")
    
    # 绘制图表
    plot_network_data(network_data)

def process_file(file_path, network_data):
    print(f"处理文件: {file_path}")
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

def extract_timestamp(line):
    match = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6})', line)
    if match:
        return datetime.strptime(match.group(1), '%m-%d %H:%M:%S.%f')
    return None

def plot_network_data(network_data):
    print("开始绘图...")
    print(f"时间戳数量: {len(network_data['timestamp'])}")
    cellular_signals = [s for s in network_data['cellular_signal'] if s is not None]
    wifi_signals = [s for s in network_data['wifi_signal'] if s is not None]
    network_types = [nt for nt in network_data['network_type'] if nt is not None]
    print(f"手机网络信号数量: {len(cellular_signals)}")
    print(f"WiFi信号数量: {len(wifi_signals)}")
    print(f"网络类型变化数量: {len(network_types)}")
    print(f"网络类型: {set(network_types)}")

    if not cellular_signals and not wifi_signals:
        print("警告：没有有效的信号数据可以绘图")
        return

    font_path = 'C:/Windows/Fonts/simhei.ttf'
    font_prop = font_manager.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(12, 6))

    # 绘制手机网络信号强度
    cellular_data = [(t, s) for t, s in zip(network_data['timestamp'], network_data['cellular_signal']) if s is not None]
    if cellular_data:
        timestamps, signals = zip(*cellular_data)
        ax.plot(timestamps, signals, label='手机网络信号强度', color='blue')
        print(f"手机网络信号范围: {min(signals)} 到 {max(signals)} dBm")
    else:
        print("没有有效的手机网络信号数据")

    # 绘制WiFi信号强度
    wifi_data = [(t, s) for t, s in zip(network_data['timestamp'], network_data['wifi_signal']) if s is not None]
    if wifi_data:
        timestamps, signals = zip(*wifi_data)
        ax.plot(timestamps, signals, label='WiFi信号强度', color='green')
        print(f"WiFi信号范围: {min(signals)} 到 {max(signals)} dBm")
    else:
        print("没有有效的WiFi信号数据")

    # 处理网络类型背景色
    # 背景绘制部分已删除

    ax.set_xlabel('时间', fontproperties=font_prop)
    ax.set_ylabel('信号强度 (dBm)', fontproperties=font_prop)
    ax.set_title('网络信号强度趋势图', fontproperties=font_prop)

    # 创建自定义图例
    from matplotlib.patches import Patch
    legend_elements = [
        plt.Line2D([0], [0], color='blue', label='手机网络信号强度'),
        plt.Line2D([0], [0], color='green', label='WiFi信号强度')
    ]
    ax.legend(handles=legend_elements, loc='best', prop=font_prop)

    fig.autofmt_xdate()
    plt.tight_layout()

    # 确保y轴显示负值
    all_signals = cellular_signals + wifi_signals
    if all_signals:
        ax.set_ylim(bottom=min(all_signals) - 10, top=max(all_signals) + 10)

    plt.show()

if __name__ == "__main__":
    log_path = input("请输入日志文件路径: ")
    process_network_logs(log_path)
