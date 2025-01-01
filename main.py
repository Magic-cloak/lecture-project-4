import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout ,QScrollArea
from PyQt5.QtCore import QThread, pyqtSignal
from xiangmu_1.SensorPlot import SensorPlot
from xiangmu_2.SignalGenerator import SignalUI
from xiangmu_3.DI_DO import DI_Tab , DO_Tab

class WorkerThread(QThread):
    # 用于通知主线程更新UI的信号
    update_signal = pyqtSignal(object)

    def __init__(self, device_description, profile_path):
        super().__init__()
        self.device_description = device_description
        self.profile_path = profile_path

    def run(self):
        # 这里运行耗时的初始化操作，确保不会阻塞主线程
        # 例如，初始化USB-4704设备
        pass

class SensorTab(QWidget):
    def __init__(self, parent=None):
        super(SensorTab, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.sensor_plot = SensorPlot(self)  # 假设SensorPlot的构造函数接受一个QWidget作为父窗口
        self.layout.addWidget(self.sensor_plot)

class SignalGeneratorTab(QWidget):
    def __init__(self, parent=None):
        super(SignalGeneratorTab, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.signal_ui = SignalUI(self)  # 假设SignalUI的构造函数接受一个QWidget作为父窗口
        self.layout.addWidget(self.signal_ui)

class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Application")
        self.setGeometry(100, 100, 1200, 800)

        # 创建 QTabWidget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # 创建4个标签页
        self.do_tab = DO_Tab()
        self.di_tab = DI_Tab()
        self.ai_tab = self.create_sensor_tab()
        self.ao_tab = SignalUI()

        self.create_tab("Sensor Plot", self.ai_tab)
        self.create_tab("Signal Generator", self.ao_tab)
        self.create_tab("DI", self.di_tab)
        self.create_tab("DO", self.do_tab)

        self.tab_widget.currentChanged.connect(self.on_tab_change)

    def create_sensor_tab(self):
        # 创建一个 QWidget 作为 Sensor Plot 的容器
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)

        # 在 Sensor Plot 标签页中添加8个 SensorPlot 实例
        for i in range(8):
            sensor_plot = SensorPlot(tab1, i)  # 假设 parent 是 tab1，index 是循环变量 i
            tab1_layout.addWidget(sensor_plot)

        return tab1

    def create_tab(self, title, widget):
        # 为每个标签页创建一个 QScrollArea，并设置滚动条
        scroll_area = QScrollArea()
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)  # 使得滚动区域可以根据内部部件的大小自动调整

        # 将 QScrollArea 添加到 QTabWidget 的标签页中
        self.tab_widget.addTab(scroll_area, title)

    def on_update_signal(self, data):
        # 处理来自工作线程的信号
        pass

    def on_tab_change(self, index):

        if index in [0, 1, 3]:  # DO Tab
            self.di_tab.stop_thread()
        elif index == 2:  # DI Tab
            self.di_tab.resume_thread()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = MainApplication()
    main_app.show()
    sys.exit(app.exec_())