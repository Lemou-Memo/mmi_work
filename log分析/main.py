import matplotlib.pyplot as plt
import matplotlib
import matplotlib.dates as mdates
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime, timedelta
from collections import defaultdict
import plotly.graph_objs as go
import plotly.offline as pyo
import re
import subprocess
import os
import sys

# 设置支持中文的字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 黑体
matplotlib.rcParams['axes.unicode_minus'] = False

def convert_kernel_log_to_localtime(log_file):
    # 生成 .localtime 后缀的文件名
    localtime_file = f"{log_file}.localtime"
    
    # 调用 ktime_convert.exe 工具
    try:
        subprocess.run(['ktime_convert.exe', log_file], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running ktime_convert.exe: {e}")
        return None
    
    # 检查 .localtime 文件是否生成
    if not os.path.exists(localtime_file):
        print(f"Error: The .localtime file '{localtime_file}' was not created.")
        return None

    return localtime_file



def plot_kernel_log(log_file):
    # 定义正则表达式模式
    time_pattern = re.compile(r'\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    cpu_usage_pattern = re.compile(r'Cpus Usage\s+\[(\d+)\]\s*,?\s*\[(\d+)\]\s*,?\s*\[(\d+)\]\s*,?\s*\[(\d+)\]\s*,?\s*\[(\d+)\]\s*,?\s*\[(\d+)\]\s*,?\s*\[(\d+)\]\s*,?\s*\[(\d+)\]')
    touch_pattern = re.compile(r'touch_report info: touch (down|up)\[res:8\] :Finger 0: x = ([0-9]+), y = ([0-9]+)')
    perf_start_pattern = re.compile(r'\[.*\]\[.*\] \[K\]\[Perf\] TRAN Perf Statistic start \((\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)')
    fps_pattern = re.compile(r'\[DISP\]\[fps\]: drm_invoke_fps_chg_callbacks,new_fps =(\d+)')

    # 初始化数据
    cpu_data = []
    touch_data = []
    fps_data = []
    perf_start_time = None

    try:
        # 读取并解析日志文件
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as file:
            timestamps = []
            for line in file:
                # 找到时间戳
                time_match = time_pattern.search(line)
                if time_match:
                    time_str = f"2024-{time_match.group()}"  # 假设年份是 2024 年
                    current_timestamp = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    timestamps.append(current_timestamp)

                # 找到 CPU 使用率数据
                cpu_usage_match = cpu_usage_pattern.search(line)
                if cpu_usage_match and timestamps:
                    timestamp = timestamps[-1]  # 使用最新的时间戳
                    usage_data = [int(cpu_usage_match.group(i)) for i in range(1, 9)]
                    cpu_data.append((timestamp, usage_data))

                # 找到触摸事件数据
                touch_match = touch_pattern.search(line)
                if touch_match and timestamps:
                    timestamp = timestamps[-1]  # 使用最新的时间戳
                    event_type = touch_match.group(1)
                    x = int(touch_match.group(2))
                    y = int(touch_match.group(3))
                    touch_data.append((timestamp, event_type, x, y))

                # 找到帧率变化数据
                fps_match = fps_pattern.search(line)
                if fps_match and timestamps:
                    timestamp = timestamps[-1]  # 使用最新的时间戳
                    fps = int(fps_match.group(1))
                    fps_data.append((timestamp, fps))

                # 找到校准时间
                perf_start_match = perf_start_pattern.search(line)
                if perf_start_match:
                    perf_start_date_str = f"2024-{perf_start_match.group(1)}"
                    perf_start_time = datetime.strptime(perf_start_date_str, "%Y-%m-%d %H:%M:%S")

        if not cpu_data:
            print("No CPU data found.")
            return
        if not touch_data:
            print("No touch data found.")
            return
        if not fps_data:
            print("No FPS data found.")
            return
        if not perf_start_time:
            print("No calibration time found.")
            return

        # 对数据进行排序
        cpu_data.sort(key=lambda x: x[0])
        touch_data.sort(key=lambda x: x[0])
        fps_data.sort(key=lambda x: x[0])

        # 解包数据
        time_stamps_cpu, core_usage = zip(*cpu_data)
        time_stamps_fps, fps_values = zip(*fps_data)

        # 确保时间戳一致
        min_time = min(min(time_stamps_cpu), min(time_stamps_fps))
        max_time = max(max(time_stamps_cpu), max(time_stamps_fps))

        # 计算每分钟的触摸事件数
        touch_counts_per_minute = defaultdict(int)
        for ts, _, _, _ in touch_data:
            minute_key = ts.replace(second=0, microsecond=0)
            touch_counts_per_minute[minute_key] += 1

        # 创建图表
        fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, ncols=1, figsize=(14, 14), sharex=True)
        print("左上角可以操作图表，右上角可以看坐标信息")

        # 绘制 CPU 使用率图表
        for i in range(8):
            core_data = [usage[i] for usage in core_usage]
            ax1.plot(time_stamps_cpu, core_data, label=f'核心 {i+1}')
        ax1.set_title('Kernel Log CPU 使用率随时间变化')
        ax1.set_ylabel('CPU 使用率 (%)')
        ax1.set_ylim(0, 100)  # 设置 y 轴范围为 0 到 100
        ax1.legend()
        ax1.grid(True)

        # 绘制 FPS 变化图表
        ax2.plot(time_stamps_fps, fps_values, color='b', label='帧率 (fps)', marker='o', linestyle='-')
        ax2.set_title('帧率随时间变化')
        ax2.set_ylabel('帧率 (fps)')
        ax2.legend()
        ax2.grid(True)

        # 绘制每分钟的触摸事件统计柱状图
        sorted_minutes = sorted(touch_counts_per_minute.keys())
        sorted_counts = [touch_counts_per_minute[minute] for minute in sorted_minutes]
        bars = ax3.bar(sorted_minutes, sorted_counts, width=0.0005, color='b', label='Touch Down Events')
        # 在柱子上方显示事件数
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width() / 2, height, f'{int(height)}', ha='center', va='bottom', fontsize=10)

        ax3.set_xlabel('时间')
        ax3.set_ylabel('触摸事件数量')
        ax3.set_title('每分钟触摸事件数量统计')
        ax3.grid(True)

        # 设置 x 轴格式和范围
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax3.xaxis.set_major_locator(mdates.SecondLocator(interval=30))
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error occurred while processing the log file: {e}")


def plot_main_log(log_file):
    # 定义正则表达式模式
    time_pattern = re.compile(r'\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    signal_strength_pattern = re.compile(r'\[LTE\] dbm: (-\d+)')
    battery_pattern = re.compile(r'current level == (\d+), temperature == (\d+)')
    backlight_pattern = re.compile(r'write (\d+) to /sys/class/leds/lcd-backlight/brightness')
    anr_warning_pattern = re.compile(r'\[ANR Warning\]')
    application_not_responding_pattern = re.compile(r'application is not responding')
    # 添加WiFi信号强度模式
    wifi_strength_pattern = re.compile(r'TranWifiSmartAssistantController: ====>>rssi :(-\d+)')
    # 初始化数据
    wifi_strength_data = []
    signal_strength_data = []
    battery_data = []
    backlight_data = []
    anr_warning_times = []
    app_not_responding_times = []

    try:
        # 读取并解析日志文件
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as file:
            timestamps = []
            for line in file:
                # 找到时间戳
                time_match = time_pattern.search(line)
                if time_match:
                    time_str = f"2024-{time_match.group()}"  # 假设年份是 2024 年
                    current_timestamp = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    timestamps.append(current_timestamp)

                # 找到信号强度数据
                signal_strength_match = signal_strength_pattern.search(line)
                if signal_strength_match and timestamps:
                    timestamp = timestamps[-1]  # 使用最新的时间戳
                    signal_strength = int(signal_strength_match.group(1))
                    signal_strength_data.append((timestamp, signal_strength))

                # 找到电池数据
                battery_match = battery_pattern.search(line)
                if battery_match and timestamps:
                    timestamp = timestamps[-1]  # 使用最新的时间戳
                    level = int(battery_match.group(1))
                    temperature = int(battery_match.group(2)) / 10  # 修正温度数据
                    if level != -1 and temperature != -1:
                        battery_data.append((timestamp, level, temperature))

                # 找到背光亮度数据
                backlight_match = backlight_pattern.search(line)
                if backlight_match and timestamps:
                    timestamp = timestamps[-1]  # 使用最新的时间戳
                    brightness = int(backlight_match.group(1))
                    backlight_data.append((timestamp, brightness))

                # 找到 ANR Warning
                if anr_warning_pattern.search(line) and timestamps:
                    timestamp = timestamps[-1]
                    anr_warning_times.append(timestamp)

                # 找到 application is not responding
                if application_not_responding_pattern.search(line) and timestamps:
                    timestamp = timestamps[-1]
                    app_not_responding_times.append(timestamp)

                # 找到WiFi信号强度数据
                wifi_strength_match = wifi_strength_pattern.search(line)
                if wifi_strength_match and timestamps:
                    timestamp = timestamps[-1]  # 使用最新的时间戳
                    wifi_strength = int(wifi_strength_match.group(1))
                    wifi_strength_data.append((timestamp, wifi_strength))

        if not signal_strength_data and not battery_data and not backlight_data:
            print("No data found.")
            return

        # 对信号强度数据按照时间戳进行排序
        if signal_strength_data:
            signal_strength_data.sort(key=lambda x: x[0])
            time_stamps_signal, signal_strength = zip(*signal_strength_data)
        else:
            time_stamps_signal, signal_strength = [], []

        # 对电池数据按照时间戳进行排序
        if battery_data:
            battery_data.sort(key=lambda x: x[0])
            time_stamps_battery, battery_levels, temperatures = zip(*battery_data)
        else:
            time_stamps_battery, battery_levels, temperatures = [], [], []

        # 对背光数据按照时间戳进行排序
        if backlight_data:
            backlight_data.sort(key=lambda x: x[0])
            time_stamps_backlight, backlight_levels = zip(*backlight_data)
        else:
            time_stamps_backlight, backlight_levels = [], []

        # 计算时间跨度
        if time_stamps_signal:
            time_span = (time_stamps_signal[-1] - time_stamps_signal[0]).total_seconds()
            interval = max(1, int(time_span / 20))  # 确保 interval 不小于 1 秒
        else:
            interval = 60  # 默认值

        # 对WiFi信号强度数据按照时间戳进行排序
        if wifi_strength_data:
            wifi_strength_data.sort(key=lambda x: x[0])
            time_stamps_wifi, wifi_strength = zip(*wifi_strength_data)
        else:
            time_stamps_wifi, wifi_strength = [], []


        # 创建一个窗口包含三个子图
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 18), sharex=True)
        print("左上角可以操作图表，右上角可以看坐标信息")

        # 绘制信号强度图表
        if signal_strength or wifi_strength:
            if signal_strength:
                ax1.plot(time_stamps_signal, signal_strength, 'b-', label='LTE信号强度 (dBm)')
            if wifi_strength:
                ax1.plot(time_stamps_wifi, wifi_strength, 'g-', label='WiFi信号强度 (dBm)')
            ax1.set_title('信号强度随时间变化')
            ax1.set_ylabel('信号强度 (dBm)')
            ax1.axhspan(-50, 0, color='green', alpha=0.3, label='强信号区域')
            ax1.axhspan(-70, -50, color='yellow', alpha=0.3, label='中等信号区域')
            ax1.axhspan(-90, -70, color='orange', alpha=0.3, label='弱信号区域')
            ax1.axhspan(min(signal_strength + wifi_strength), -90, color='red', alpha=0.3, label='非常弱信号区域')


            # 绘制 ANR Warning 标记
            for error_time in anr_warning_times:
                ax1.axvline(x=error_time, color='c', linestyle='--', alpha=0.2)

            # 绘制 application is not responding 标记
            for error_time in app_not_responding_times:
                ax1.axvline(x=error_time, color='r', linestyle='--', alpha=0.2)

            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
            ax1.xaxis.set_major_locator(mdates.SecondLocator(interval=interval))
            ax1.grid(True)
            ax1.set_ylim(bottom=min(signal_strength), top=max(0, max(signal_strength)))
            ax1.legend(loc='upper right')
        # 绘制电池电量和温度图表
        if battery_levels and temperatures:
            ax2.plot(time_stamps_battery, battery_levels, 'g-', label='电池电量 (%)')
            ax2.set_ylabel('电池电量 (%)', color='g')
            ax4 = ax2.twinx()  # 创建右侧 y 轴
            ax4.plot(time_stamps_battery, temperatures, 'r-', label='温度 (°C)')
            ax4.set_ylabel('温度 (°C)', color='r')
            ax2.set_title('电池电量和温度随时间变化')

            # 绘制 ANR Warning 标记
            for error_time in anr_warning_times:
                ax2.axvline(x=error_time, color='c', linestyle='--', alpha=0.2)

            # 绘制 application is not responding 标记
            for error_time in app_not_responding_times:
                ax2.axvline(x=error_time, color='r', linestyle='--', alpha=0.2)

            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
            ax2.xaxis.set_major_locator(mdates.SecondLocator(interval=interval))
            ax2.grid(True)

            ax2.set_ylim(bottom=0, top=100)
            ax2.tick_params(axis='y', labelcolor='g')

            ax4.set_ylim(bottom=min(temperatures, default=0), top=max(temperatures, default=50))
            ax4.tick_params(axis='y', labelcolor='r')

            ax2.legend(loc='upper left')
            ax4.legend(loc='upper right')

        # 绘制背光亮度图表
        if backlight_levels:
            ax3.plot(time_stamps_backlight, backlight_levels, 'm-', label='背光亮度')
            ax3.set_title('背光亮度随时间变化')
            ax3.set_ylabel('背光亮度')

            # 绘制 ANR Warning 标记
            for error_time in anr_warning_times:
                ax3.axvline(x=error_time, color='c', linestyle='--', alpha=0.2)

            # 绘制 application is not responding 标记
            for error_time in app_not_responding_times:
                ax3.axvline(x=error_time, color='r', linestyle='--', alpha=0.2)

            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
            ax3.xaxis.set_major_locator(mdates.SecondLocator(interval=interval))
            ax3.grid(True)

            ax3.legend(loc='upper right')

        # 添加全局图例，放置在图表外部
        handles = [
            plt.Line2D([0], [0], color='c', linestyle='--', alpha=0.2, lw=2, label='ANR Warning'),
            plt.Line2D([0], [0], color='r', linestyle='--', alpha=0.2, lw=2, label='App Not Responding')
        ]
        fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, 0.97), ncol=2)

        # 自动调整子图间距以避免重叠，并确保四周边距适当
        plt.tight_layout(pad=3.0)
        # 调整布局，确保四边文字显示不全
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        plt.show()

    except FileNotFoundError:
        print(f"Error: The file '{log_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = input("Enter the path to the log file: ").strip()

    # 检查文件是否已经是 .localtime 文件
    if log_file.endswith('.localtime'):
        # 如果是 .localtime 文件，直接绘制
        if 'kernel_log' in log_file:
            plot_kernel_log(log_file)
        elif 'main_log' in log_file:
            plot_main_log(log_file)
        else:
            print("Unknown log type. Please provide a valid log file.")
    else:
        # 如果不是 .localtime 文件，调用转换工具
        if 'kernel_log' in log_file:
            localtime_file = convert_kernel_log_to_localtime(log_file)
            if localtime_file:
                plot_kernel_log(localtime_file)
            else:
                print("Failed to convert kernel log file to .localtime format.")
        elif 'main_log' in log_file:
            plot_main_log(log_file)
        else:
            print("Unknown log type. Please provide a valid log file.")



if __name__ == "__main__":

    print("运行中ing")
    main()
    # 保持窗口显示
    input("Press Enter to exit...")