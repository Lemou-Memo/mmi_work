import os
import re
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib
from datetime import datetime
import matplotlib.ticker as ticker
import sys
import subprocess
matplotlib.use('TkAgg')  # 或者尝试 'Qt5Agg'
matplotlib.rcParams['font.family'] = 'SimHei'  # 选择支持中文的字体，例如 SimHei

# 定义字体属性
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = font_manager.FontProperties(fname=font_path)

# 强制使用默认字体的负号符号
matplotlib.rcParams['axes.unicode_minus'] = False

def process_temp_logs(path):
    log_files = []

    # 遍历给定路径下的所有文件
    for root, dirs, files in os.walk(path):
        for file in files:
            if re.match(r'kernel_log_\d+__\d{4}_\d{4}_\d{6}\.localtime$', file):
                log_files.append(os.path.join(root, file))
            elif re.match(r'kernel_log_\d+__\d{4}_\d{4}_\d{6}$', file):
                localtime_file = convert_kernel_log(os.path.join(root, file))  # 调用转换函数
                if localtime_file and os.path.exists(localtime_file):
                    log_files.append(localtime_file)
            elif re.match(r'main_log_\d+__\d{4}_\d{4}_\d{6}', file):
                log_files.append(os.path.join(root, file))

    # 按文件名排序,确保按顺序处理
    log_files.sort()

    # 用于存储所有数据的字典
    all_temps = {
        'timestamp': [], 'tmp1': [], 'tmp2': [], 'tmp3': [], 
        'batt_temp_kernel': [], 'batt_temp_main': [], 'batt_temp_healthd': [],
        'wmt': [], 'batt_level_main': [], 'batt_level_kernel': [], 
        'cpu_usage': [[] for _ in range(8)]  # 为8个CPU核心准备8个列表
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
    ktime_convert = os.path.join(os.path.dirname(__file__), 'ktime_convert.exe')
    if os.path.exists(ktime_convert):
        try:
            subprocess.run([ktime_convert, file_path], check=True)
            print(f"成功转换文件: {file_path}")
            return file_path + '.localtime'
        except subprocess.CalledProcessError:
            print(f"转换文件失败: {file_path}")
    else:
        print("未找到 ktime_convert.exe 文件,无法转换 kernel 日志")
    return None

def process_temp_file(file_path, all_temps):
    print(f"处理文件: {file_path}")
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
                print(f"找到无线通讯温度: {wmt_temp}°C, 时间戳: {timestamp.strftime('%m-%d %H:%M:%S.%f')}")
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

            # 匹配CPU使用率
            match = re.search(r'Cpus Usage \[(\d+)\], \[(\d+)\], \[(\d+)\], \[(\d+)\], \[(\d+)\] \[(\d+)\], \[(\d+)\], \[(\d+)\]', line)
            if match:
                cpu_usages = [int(match.group(i)) for i in range(1, 9)]
                for i, usage in enumerate(cpu_usages):
                    all_temps['cpu_usage'][i].append((timestamp, usage))
                continue

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
    anr_warning_times = []  # 添加此行
    app_not_responding_times = []  # 添加此行

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
        network_data, anr_warning_times_temp, app_not_responding_times_temp = process_network_file(file_path, network_data)
        anr_warning_times.extend(anr_warning_times_temp)  # 合并时间戳
        app_not_responding_times.extend(app_not_responding_times_temp)  # 合并时间戳

    # 打印数据长度以进行调试
    print("网络数据长度:")
    for key, value in network_data.items():
        print(f"{key}: {len(value)}")

    return network_data, anr_warning_times, app_not_responding_times  # 修改此行

def process_network_file(file_path, network_data):
    print(f"处理文件: {file_path}")
    cellular_count = 0
    wifi_count = 0
    network_type_count = 0
    current_network_type = None
    anr_warning_times = []  # 添加此行
    app_not_responding_times = []  # 添加此行
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            timestamp = extract_timestamp(line)
            if timestamp is None:
                continue

            # 匹配手机网络信号强度
            match = re.search(r'TranSignalStrengthComponentImpl: \[LTE\] dbm: (-?\d+)', line)
            if match:
                signal = int(match.group(1))
                #print(f"找到手机信号: {signal} dBm, 时间戳: {timestamp.strftime('%m-%d %H:%M:%S.%f')}")
                update_network_data(network_data, timestamp, cellular_signal=signal, network_type=current_network_type)
                cellular_count += 1
                continue

            # 匹配WiFi信号强度
            match = re.search(r'====>>rssi :(-?\d+)', line)
            if match:
                signal = int(match.group(1))
                #(f"找到WiFi信号: {signal} dBm, 时间戳: {timestamp.strftime('%m-%d %H:%M:%S.%f')}")
                update_network_data(network_data, timestamp, wifi_signal=signal, network_type=current_network_type)
                wifi_count += 1
                continue

            # 匹配网络类型变化
            match = re.search(r'NetworkStatusMonitor: onNetworkTypeChanged (\w+) => (\w+)', line)
            if match:
                old_type, new_type = match.group(1), match.group(2)
                if current_network_type != new_type:  # 网络类型变化才记录
                    update_network_data(network_data, timestamp, network_type=new_type)
                print(f"网络类型变化: {old_type} => {new_type}, 时间戳: {timestamp.strftime('%m-%d %H:%M:%S.%f')}")  # 输出变化信息
                current_network_type = new_type
                network_type_count += 1

            # 匹配 ANR 警告
            if re.search(r'\[ANR Warning\]', line):
                anr_warning_times.append(timestamp)

            # 匹配应用程序未响应
            if re.search(r'application is not responding', line):
                app_not_responding_times.append(timestamp)

    print(f"文件 {file_path} 中找到 {cellular_count} 个手机信号, {wifi_count} 个WiFi信号, 和 {network_type_count} 个网络类型变化")
    print(f"最后的网络类型: {current_network_type}")

    return network_data, anr_warning_times, app_not_responding_times  # 修改此行

def update_network_data(network_data, timestamp, cellular_signal=None, wifi_signal=None, network_type=None):
    network_data['timestamp'].append(timestamp)
    network_data['cellular_signal'].append(cellular_signal)
    network_data['wifi_signal'].append(wifi_signal)
    network_data['network_type'].append(network_type)
    if network_type is not None:
        print(f"更新网络类型: {network_type}, 时间戳: {timestamp.strftime('%m-%d %H:%M:%S.%f')}")

def plot_data(all_temps, network_data, anr_warning_times, app_not_responding_times):
    print("开始绘图...")

    # 打印数据长度以进行调试
    print("数据长度检查:")
    print(f"时间戳: {len(all_temps['timestamp'])}")
    print(f"wmt信号模块温度: {len(all_temps['wmt'])}")
    print(f"手机信号强度: {len(network_data['cellular_signal'])}")
    print(f"WiFi信号强度: {len(network_data['wifi_signal'])}")

    font_path = 'C:/Windows/Fonts/simhei.ttf'
    font_prop = font_manager.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 18), sharex=True)

    # 添加全局图例，放置在图表外部
    handles = [
        plt.Line2D([0], [0], color='c', linestyle='--', alpha=0.2, lw=2, label='ANR Warning'),
        plt.Line2D([0], [0], color='r', linestyle='--', alpha=0.2, lw=2, label='App Not Responding')
    ]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, 1), ncol=2)
    # 绘制温度数据
    label_map = {
        'tmp1': '芯片组电池温度1',
        'tmp2': '芯片组电池温度2',
        'tmp3': '芯片组电池温度3',
        'batt_temp_kernel': '电池温度 (Kernel)',
        'batt_temp_main': '电池温度 (Main)',
        'batt_temp_healthd': '电池温度 (Healthd)',
        'wmt': 'WMT 温度',
        'batt_level_main': '电量 (Main)',
        'batt_level_kernel': '电量 (Kernel)'
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
        valid_data = [(t, v) for t, v in zip(all_temps['timestamp'], all_temps[key]) if v is not None]
        print(f"{key}: {len(valid_data)} 个有效数据点")
        if valid_data:
            timestamps, values = zip(*valid_data)
            if 'batt_level' in key:
                ax1.plot(timestamps, values, label=label_map[key], color=color_map[key], linestyle='--')
            else:
                ax1.plot(timestamps, values, label=label_map[key], color=color_map[key])

    ax1.set_ylabel('温度 (°C) / 电池电量 (%)', fontproperties=font_prop)
    ax1.set_title('温度和电池电量趋势图', fontproperties=font_prop)
    ax1.legend(loc='best', prop=font_prop)

    # 绘制网络信号强度数据
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
    
    ax2.set_ylabel('信号强度 (dBm)', fontproperties=font_prop)
    ax2.set_title('网络信号强度趋势图', fontproperties=font_prop)
    ax2.legend(loc='best', prop=font_prop)

    # 绘制CPU使用率数据
    for i in range(8):
        if all_temps['cpu_usage'][i]:
            timestamps, usages = zip(*all_temps['cpu_usage'][i])
            ax3.plot(timestamps, usages, label=f'CPU {i+1} 使用率')

    # 添加 ANR 警告和应用程序未响应的标记
    for error_time in anr_warning_times:
        ax3.axvline(x=error_time, color='c', linestyle='--', alpha=0.2)
    for error_time in app_not_responding_times:
        ax3.axvline(x=error_time, color='r', linestyle='--', alpha=0.2)

    ax3.set_ylabel('CPU 使用率 (%)', fontproperties=font_prop)
    ax3.set_title('CPU 使用率趋势图', fontproperties=font_prop)
    ax3.legend(loc='best', prop=font_prop)
    ax3.set_ylim(0, 100)  # CPU使用率的范围通常是0%到100%

    # 调整子图的边距
    # 自动调整子图间距以避免重叠，并确保四周边距适当
    #plt.tight_layout(pad=10.0)
    # 调整布局，确保四边文字显示不全
    plt.subplots_adjust(left=0.051, right=0.975, top=0.933, bottom=0.067)

    plt.xticks(rotation=10)  # 旋转10度
    

    plt.xlabel('时间', fontproperties=font_prop)
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        temp_path = sys.argv[1]
    else:
        temp_path = input("请输入日志文件路径:").strip()
    all_temps = process_temp_logs(temp_path)
    network_data, anr_warning_times, app_not_responding_times = process_network_logs(temp_path)
    plot_data(all_temps, network_data, anr_warning_times, app_not_responding_times)
