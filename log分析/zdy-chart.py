import re
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib as mpl
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
# 设置中文字体
mpl.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
def plot_log_data(log_file, pattern, ax=None, fig=None, root=None):
    data = []
    timestamps = []
    # 转义方括号和其他特殊字符
    escaped_pattern = re.escape(pattern).replace('XXX', r'(-?\d+)')
    regex = re.compile(escaped_pattern)
    # 匹配时间的正则表达式
    time_regex = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{6})')
    # 读取日志文件
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            time_match = time_regex.search(line)
            rssi_match = regex.search(line)
            if time_match and rssi_match:
                time_str = time_match.group(1)
                time = datetime.strptime(time_str, '%H:%M:%S.%f')
                timestamps.append(time)
                data.append(int(rssi_match.group(1)))
    # 打印数据点数量
    print(f"找到的数据点数量：{len(data)}")
    if len(data) == 0:
        print("没有找到匹配的数据点。请检查日志文件格式和匹配模式。")
        return None, None, None
    if ax is None or fig is None or root is None:
        # 创建新的图形窗口
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_title('变化图表')
        ax.set_xlabel('时间')
        ax.set_ylabel('变化值')
        ax.grid(True)
        # 设置x轴时间格式
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        fig.autofmt_xdate()
        # 创建Tkinter窗口
        root = tk.Tk()
        root.title(f"变化图表 - {log_file}")
        # 将matplotlib图形嵌入Tkinter窗口
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.draw()
        canvas.get_tk_widget().pack()
    # 在现有或新的图表上绘制数据
    ax.plot(timestamps, data, marker='o', label=pattern)
    ax.legend()
    # 更新图表
    fig.canvas.draw_idle()  # 使用 draw_idle() 替代 draw()
    # 非阻塞方式显示窗口
    root.update()
    return fig, ax, root
def main():
    log_file = input("请输入日志文件路径：").strip()
    fig = ax = root = None
    while True:
        pattern = input("请输入读取格式(使用XXX表示要提取的数值,输入'q'退出,输入'add:'添加数据): ").strip()
        if pattern.lower() == 'q':
            break
        if not pattern.startswith("add:"):
            # 如果不是添加模式，关闭现有窗口并重置图表对象
            if root:
                root.destroy()
            fig = ax = root = None
        else:
            # 如果是添加模式，移除"add:"前缀
            pattern = pattern[4:]
        try:
            fig, ax, root = plot_log_data(log_file, pattern, ax, fig, root)
        except FileNotFoundError:
            print(f"错误：找不到文件 '{log_file}'。")
        except Exception as e:
            print(f"发生错误：{e}")
        print("\n")  # 添加空行以提高可读性
    if root:
        root.mainloop()
if __name__ == "__main__":
    main()