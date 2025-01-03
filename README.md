#### 概述
本项目是一个基于PyQt5的图形用户界面（GUI）应用程序，提供了多个功能标签页，用于展示传感器数据、信号生成以及数字输入/输出（DI/DO）控制。

#### 启动程序
- 双击运行`main.py`文件或在命令行中执行`python main.py`来启动应用程序。

#### 主界面
程序启动后，将显示主窗口，标题为“Main Application”，窗口大小为1200x800像素，位于屏幕的(100,100)位置。

#### 功能标签页
主窗口包含一个`QTabWidget`，用于切换不同的功能标签页。标签页包括：

1. **Sensor Plot（传感器绘图）**
   - 显示8个传感器数据的实时绘图。
   - 每个传感器数据由一个`SensorPlot`实例表示，共8个实例。

2. **Signal Generator（信号生成器）**
   - 提供信号生成功能，允许用户自定义信号并输出。
   - 由`SignalUI`组件实现。

3. **DI（数字输入）**
   - 用于配置和显示数字输入的状态。
   - 由`DI_Tab`组件实现。

4. **DO（数字输出）**
   - 用于配置和控制数字输出。
   - 由`DO_Tab`组件实现。

#### 操作说明

- **切换标签页**
  - 点击顶部的标签页标题，可以切换到不同的功能区域。

- **Sensor Plot标签页**
  - 该标签页包含8个传感器数据的实时绘图，每个绘图区域可以独立显示传感器数据的变化。

- **Signal Generator标签页**
  - 在此标签页中，用户可以配置信号参数，并通过界面上的控件生成信号。

- **DI标签页**
  - 用户可以在此标签页中查看和配置数字输入的状态。

- **DO标签页**
  - 用户可以在此标签页中配置和控制数字输出的状态。

#### 线程操作
- **工作线程**
  - 程序中包含一个`WorkerThread`类，用于执行耗时的初始化操作，如设备初始化，以避免阻塞主线程。

#### 信号处理
- **信号与槽**
  - 当切换标签页时，程序会根据当前激活的标签页执行不同的线程操作，如停止或恢复线程。

#### 退出程序
- 点击窗口右上角的关闭按钮或在命令行中使用`Ctrl+C`可以退出程序。
