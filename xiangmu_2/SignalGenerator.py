import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLineEdit, QLabel, QSlider, QCheckBox)
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import time
import math
from Automation.BDaq.InstantAoCtrl import InstantAoCtrl
from Automation.BDaq.BDaqApi import BioFailed


class SignalGenerator:
    def __init__(self, device_description="USB-4704,BID#0", profile_path="../../profile/DemoDevice.xml",
                 signal_array=None, signal_type='custom', offset=1.0, amplitude=1.0, period=100):
        self.instantAo = InstantAoCtrl(device_description)
        self.instantAo.loadProfile = profile_path
        self.offset = offset
        self.amplitude = amplitude
        self.period = period
        self.index = 0
        self.cycle_count = 0  # 已输出的周期数
        self.total_cycles = float('inf')  # 默认无限循环

        if signal_array is not None:
            self.signal_array = signal_array
        else:
            if signal_type == 'sine':
                self.signal_array = [offset + amplitude * math.sin(2 * math.pi * i / period) for i in range(period)]
            elif signal_type == 'ramp':
                self.signal_array = [offset + amplitude * (i / period) for i in range(period)]
            elif signal_type == 'constant':
                self.signal_array = [offset] * period
            elif signal_type == 'square':  # 方波信号
                self.signal_array = [offset + amplitude if i % (period // 2) == 0 else offset - amplitude for i in range(period)]
            else:
                raise ValueError(
                    "Invalid signal type. Choose from 'sine', 'ramp', 'constant', 'square' or provide a custom array.")

    def next_value(self):
        """获取并返回信号数组中的下一个值，同时更新索引和周期计数。"""
        value = self.signal_array[self.index]
        self.index = (self.index + 1) % len(self.signal_array)

        if self.index == 0:
            self.cycle_count += 1  # 每个完整周期结束后计数加1

        return value

    def reset_cycle_count(self):
        """重置已输出的周期计数和信号索引。"""
        self.cycle_count = 0
        self.index = 0


class SignalUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signal Generator UI")

        # 初始化信号生成器和输出控制
        self.signal_gen = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_output)
        self.output_active = False  # 用于标记是否正在输出

        # 默认输出频率（以赫兹为单位）
        self.output_frequency = 10  # 频率为10 Hz

        # 绘图相关
        self.x_data = list(range(100))
        self.y_data = [0] * 100

        # 初始化UI布局
        self.init_ui()

        # 标记是否选择了波形
        self.waveform_selected = False

    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)  # 使用self作为父布局，这样就不会返回None

        # 绘图布局
        self.init_plot(main_layout)

        # 参数输入
        param_layout = QHBoxLayout()
        self.offset_input = QLineEdit("1.0")
        self.amplitude_input = QLineEdit("1.0")
        self.period_input = QLineEdit("100")

        param_layout.addWidget(QLabel("Offset:"))
        param_layout.addWidget(self.offset_input)
        param_layout.addWidget(QLabel("Amplitude:"))
        param_layout.addWidget(self.amplitude_input)
        param_layout.addWidget(QLabel("Period:"))
        param_layout.addWidget(self.period_input)

        main_layout.addLayout(param_layout)

        # 滑条和输入框用于控制输出频率
        freq_layout = QHBoxLayout()
        self.freq_slider = QSlider(Qt.Horizontal)
        self.freq_slider.setRange(1, 100)
        self.freq_slider.setValue(self.output_frequency)
        self.freq_slider.setMinimumSize(500, 0)
        self.freq_slider.valueChanged.connect(self.update_frequency_from_slider)

        self.freq_input = QLineEdit(str(self.output_frequency))
        self.freq_input.setFixedWidth(75)
        self.freq_input.setFixedHeight(50)
        self.freq_input.editingFinished.connect(self.update_frequency_from_input)

        freq_layout.addWidget(QLabel("Output Frequency (Hz):"))
        freq_layout.addWidget(self.freq_slider)
        freq_layout.addWidget(self.freq_input)
        main_layout.addLayout(freq_layout)

        # 波形选择按钮
        button_layout = QVBoxLayout()  # 使用垂直布局，减少水平空间占用
        self.sine_button = QPushButton("Generate Sine Wave")
        self.sine_button.clicked.connect(self.generate_sine_wave)
        button_layout.addWidget(self.sine_button)

        self.ramp_button = QPushButton("Generate Ramp Wave")
        self.ramp_button.clicked.connect(self.generate_ramp_wave)
        button_layout.addWidget(self.ramp_button)

        self.constant_button = QPushButton("Generate Constant Signal")
        self.constant_button.clicked.connect(self.generate_constant_signal)
        button_layout.addWidget(self.constant_button)

        self.square_button = QPushButton("Generate Square Wave")  # 新增方波按钮
        self.square_button.clicked.connect(self.generate_square_wave)
        button_layout.addWidget(self.square_button)

        self.file_button = QPushButton("Load Signal from File")
        self.file_button.clicked.connect(self.load_signal_from_file)
        button_layout.addWidget(self.file_button)

        main_layout.addLayout(button_layout)

        # 周期控制复选框和输入栏
        cycle_control_layout = QGridLayout()  # 使用网格布局
        self.cycle_check = QCheckBox("Limit Output Cycles")
        self.cycle_check.stateChanged.connect(self.on_cycle_check)
        self.cycle_input = QLineEdit("1.0")
        self.cycle_input.setEnabled(False)  # 初始禁用
        cycle_control_layout.addWidget(self.cycle_check, 0, 0)
        cycle_control_layout.addWidget(QLabel("Cycle Count:"), 0, 1)
        cycle_control_layout.addWidget(self.cycle_input, 0, 2)
        main_layout.addLayout(cycle_control_layout)

        # 控制按钮
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.toggle_output)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setEnabled(False)  # 初始状态下禁用暂停按钮

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.pause_button)
        main_layout.addLayout(control_layout)

    def init_plot(self, main_layout):
        """初始化绘图"""
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(300)  # 设置画布的最小高度
        self.canvas.setMinimumWidth(500)  # 设置画布的最小宽度
        self.line, = self.ax.plot(self.x_data, self.y_data)
        self.ax.set_ylim(-2, 2)
        main_layout.addWidget(self.canvas)  # 将画布添加到主布局

    def update_frequency_from_slider(self):
        """滑条调整频率并更新输入框"""
        self.output_frequency = self.freq_slider.value()
        self.freq_input.setText(str(self.output_frequency))
        if self.output_active:
            self.timer.setInterval(1000 // self.output_frequency)  # 将频率转换为毫秒

    def update_frequency_from_input(self):
        """输入框调整频率并更新滑条"""
        try:
            value = int(self.freq_input.text())
            if 1 <= value <= 100:
                self.output_frequency = value
                self.freq_slider.setValue(value)
                if self.output_active:
                    self.timer.setInterval(1000 // self.output_frequency)  # 将频率转换为毫秒
            else:
                self.freq_input.setText(str(self.output_frequency))
        except ValueError:
            self.freq_input.setText(str(self.output_frequency))

    def reset_plot(self):
        """重置绘图数据"""
        self.y_data = [0] * 100  # 清空y轴数据
        self.line.set_ydata(self.y_data)
        self.canvas.draw()

    def update_plot(self, new_value):
        """实时更新绘图数据"""
        self.y_data = self.y_data[1:] + [new_value]
        self.line.set_ydata(self.y_data)
        self.canvas.draw()

    # 其余函数保持不变

    def toggle_output(self):
        """开始或结束信号输出"""
        if not self.output_active:
            if not self.waveform_selected:  # 检查是否选择了波形
                return
            # 开始输出
            if self.signal_gen:
                offset = float(self.offset_input.text())
                amplitude = float(self.amplitude_input.text())
                period = int(self.period_input.text())

                # 根据之前选择的波形类型，重新生成信号
                if isinstance(self.signal_gen, SignalGenerator):
                    if self.sine_button.styleSheet() == "background-color: lightblue":
                        self.signal_gen = SignalGenerator(signal_type='sine', offset=offset, amplitude=amplitude,
                                                          period=period)
                    elif self.ramp_button.styleSheet() == "background-color: lightblue":
                        self.signal_gen = SignalGenerator(signal_type='ramp', offset=offset, amplitude=amplitude,
                                                          period=period)
                    elif self.constant_button.styleSheet() == "background-color: lightblue":
                        self.signal_gen = SignalGenerator(signal_type='constant', offset=offset)
                    elif self.square_button.styleSheet() == "background-color: lightblue":
                            self.signal_gen = SignalGenerator(signal_type='square', offset=offset, amplitude=amplitude,
                                                              period=period)

                self.reset_plot()  # 重置绘图数据
                self.signal_gen.reset_cycle_count()  # 重置周期计数
                if self.cycle_check.isChecked():
                    self.signal_gen.total_cycles = float(self.cycle_input.text())  # 设置限制的周期数
                else:
                    self.signal_gen.total_cycles = float('inf')  # 无限循环

                self.timer.start(1000 // self.output_frequency)  # 使用滑条控制的频率
                self.output_active = True
                self.start_button.setText("Stop")
                self.pause_button.setEnabled(True)
        else:
            # 结束输出
            self.timer.stop()
            self.output_active = False
            self.start_button.setText("Start")
            self.pause_button.setText("Pause")
            self.pause_button.setEnabled(False)

    def toggle_pause(self):
        """暂停或恢复信号输出"""
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("Continue")
        else:
            self.timer.start(1000 // self.output_frequency)  # 恢复时也使用频率控制
            self.pause_button.setText("Pause")

    def on_cycle_check(self):
        """启用或禁用周期数输入框"""
        self.cycle_input.setEnabled(self.cycle_check.isChecked())

    def highlight_button(self, button):
        """高亮显示当前选中的波形按钮"""
        for b in [self.sine_button, self.ramp_button, self.constant_button, self.square_button, self.file_button]:
            b.setStyleSheet("")  # 清除其他按钮的样式
        button.setStyleSheet("background-color: lightblue")  # 设置当前按钮为高亮

    def generate_sine_wave(self):
        """生成正弦波信号并高亮按钮"""
        self.highlight_button(self.sine_button)
        offset = float(self.offset_input.text())
        amplitude = float(self.amplitude_input.text())
        period = int(self.period_input.text())
        self.signal_gen = SignalGenerator(signal_type='sine', offset=offset, amplitude=amplitude, period=period)
        self.waveform_selected = True

    def generate_ramp_wave(self):
        """生成斜坡信号并高亮按钮"""
        self.highlight_button(self.ramp_button)
        offset = float(self.offset_input.text())
        amplitude = float(self.amplitude_input.text())
        period = int(self.period_input.text())
        self.signal_gen = SignalGenerator(signal_type='ramp', offset=offset, amplitude=amplitude, period=period)
        self.waveform_selected = True

    def generate_constant_signal(self):
        """生成常数信号并高亮按钮"""
        self.highlight_button(self.constant_button)
        offset = float(self.offset_input.text())
        self.signal_gen = SignalGenerator(signal_type='constant', offset=offset)
        self.amplitude_input.setEnabled(False)
        self.period_input.setEnabled(False)
        self.waveform_selected = True

    def generate_square_wave(self):
        """生成方波信号并高亮按钮"""
        self.highlight_button(self.square_button)
        offset = float(self.offset_input.text())
        amplitude = float(self.amplitude_input.text())
        period = int(self.period_input.text())

        # 修正：生成一个完整的方波周期
        self.signal_gen = SignalGenerator(signal_type='square', offset=offset, amplitude=amplitude, period=period)

        # 修改方波生成逻辑
        self.signal_gen.signal_array = [
            offset + amplitude if i < period // 2 else offset - amplitude
            for i in range(period)
        ]

        self.waveform_selected = True

    def load_signal_from_file(self):
        """从文件加载信号数据并高亮按钮"""
        self.highlight_button(self.file_button)
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Signal File", "", "CSV Files (*.csv)")
        if file_path:
            data = pd.read_csv(file_path, header=None).to_numpy().flatten()
            self.signal_gen = SignalGenerator(signal_array=data)
            self.waveform_selected = True

    def update_output(self):
        """更新信号输出值并实时显示"""
        if self.signal_gen:
            if self.signal_gen.cycle_count + self.signal_gen.index /  self.signal_gen.period>= self.signal_gen.total_cycles:
                self.timer.stop()
                self.output_active = False
                self.start_button.setText("Start")
                self.pause_button.setText("Pause")
                self.pause_button.setEnabled(False)
                return

            # 获取下一个信号值
            new_value = self.signal_gen.next_value()
            # 向硬件输出信号
            write_data = [new_value]
            ret = self.signal_gen.instantAo.writeAny(0, 1, None, write_data)
            # 检查输出状态，输出失败时停止计时器
            if BioFailed(ret):
                print("Error: Failed to write data.")
                self.timer.stop()
            # 实时更新UI的绘图
            self.update_plot(new_value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignalUI()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
