import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QCheckBox,
    QWidget, QPushButton, QHBoxLayout, QSpinBox, QLabel, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from random import randint
from typing import Callable


def quick_sort_inplace(array: list, callback: Callable, reverse: bool = False, 
                       low: int = 0, high: int = None):
    """In-place Quick Sort для красивой визуализации."""
    if high is None:
        high = len(array) - 1

    if low < high:
        pivot_idx = partition(array, low, high, callback, reverse)
        quick_sort_inplace(array, callback, reverse, low, pivot_idx - 1)
        quick_sort_inplace(array, callback, reverse, pivot_idx + 1, high)


def partition(array: list, low: int, high: int, callback: Callable, reverse: bool) -> int:
    """Разбиение массива вокруг опорного элемента."""
    mid = (low + high) // 2
    pivot = array[mid]
    array[mid], array[high] = array[high], array[mid]
    if callback:
        callback(array, high, -1)

    i = low
    for j in range(low, high):
        if callback:
            callback(array, high, j)

        condition = array[j] > pivot if reverse else array[j] < pivot
        if condition:
            array[i], array[j] = array[j], array[i]
            if callback:
                callback(array, high, i)
            i += 1

    array[i], array[high] = array[high], array[i]
    if callback:
        callback(array, i, -1)
        
    return i


class SortThread(QThread):
    step_signal = pyqtSignal(list, int, int, float) 
    finished_signal = pyqtSignal(list)

    def __init__(self, array: list[int], delay: float, reverse: bool = False):
        super().__init__()
        self.array = array
        self.delay = delay
        self.is_paused = False
        self.reverse = reverse

    def run(self):
        def callback(current_array, pivot_idx, compare_idx):
            self.step_signal.emit(current_array[:], pivot_idx, compare_idx, self.delay)
            time.sleep(self.delay)
            while self.is_paused:
                time.sleep(0.1)

        quick_sort_inplace(self.array, callback, self.reverse)
        self.finished_signal.emit(self.array)


class SortVisualizerWidget(QWidget):
    """Виджет для отрисовки массива в виде столбчатой диаграммы."""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self.ax.set_title("Quick Sort Visualization")

    def update_plot(self, array, pivot_idx: int = -1, compare_idx: int = -1,
                    min_val: int = 0, max_val: int = 100):
        self.ax.clear()
        self.ax.set_xticks([])

        colors = ['skyblue'] * len(array)
        if 0 <= pivot_idx < len(array):
            colors[pivot_idx] = 'orange'
        if 0 <= compare_idx < len(array) and compare_idx != pivot_idx:
            colors[compare_idx] = 'red'

        self.ax.bar(range(len(array)), array, color=colors)

        if array:
            padding = max(10, (max_val - min_val) * 0.1)
            self.ax.set_ylim(min_val - padding, max_val + padding)
        
        self.canvas.draw()


class MainWindow(QMainWindow):
    MAX_ARRAY_SIZE = 10000
    DELAY = 1000

    def __init__(self):
        super().__init__()
        self.sort_thread = None
        self._create_ui()
        self.start_sorting()

    def _create_ui(self):
        self.setWindowTitle("Sorting arrat")
        main_layout = QVBoxLayout()
        self.matplotlib_widget = SortVisualizerWidget()
        main_layout.addWidget(self.matplotlib_widget)

        min_range_label = QLabel("Minimum possible value:")
        self.min_range = QSpinBox()
        self.min_range.setMaximum(10000)
        self.min_range.setMinimum(-10000)
        self.min_range.setValue(-100)
        min_layout = QHBoxLayout()
        min_layout.addWidget(min_range_label)
        min_layout.addWidget(self.min_range)
        main_layout.addLayout(min_layout)

        max_range_label = QLabel("Maximum possible value:")
        self.max_range = QSpinBox()
        self.max_range.setMaximum(10000)
        self.max_range.setMinimum(-10000)
        self.max_range.setValue(100)
        max_layout = QHBoxLayout()
        max_layout.addWidget(max_range_label)
        max_layout.addWidget(self.max_range)
        main_layout.addLayout(max_layout)

        array_size_label = QLabel("Array size:")
        self.array_size = QSpinBox(self)
        self.array_size.setMaximum(self.MAX_ARRAY_SIZE)
        self.array_size.setValue(20)
        self.array_size.setMinimum(1)
        array_size_layout = QHBoxLayout()
        array_size_layout.addWidget(array_size_label)
        array_size_layout.addWidget(self.array_size)
        main_layout.addLayout(array_size_layout)

        self.reverse = QCheckBox("Sorting in reverse order")
        main_layout.addWidget(self.reverse)

        self.start_button = QPushButton("start", self)
        self.start_button.clicked.connect(self.start_sorting)
        self.pause_button = QPushButton("pause", self)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.restart_button = QPushButton("restart", self)
        self.restart_button.clicked.connect(self.restart_sorting)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.restart_button)
        self.pause_button.setEnabled(False)
        main_layout.addLayout(buttons_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def start_sorting(self):
        if self.sort_thread is not None and self.sort_thread.isRunning():
            return

        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        delay = max(0.001, self.DELAY / self.MAX_ARRAY_SIZE) 
        original_array = [randint(self.min_val, self.max_val)
            for _ in range(self.size_val)]

        self.matplotlib_widget.update_plot(
            original_array, min_val=self.min_val, max_val=self.max_val
        )

        self.sort_thread = SortThread(
            original_array[:],
            delay, self.is_reverse
        )
        self.sort_thread.step_signal.connect(self.on_step)
        self.sort_thread.finished_signal.connect(self.on_finish)
        self.sort_thread.start()

    def on_step(self, current_array, pivot_idx, compare_idx, delay):
        self.matplotlib_widget.update_plot(
            current_array, 
            pivot_idx=pivot_idx,
            compare_idx=compare_idx,
            min_val=self.min_val,
            max_val=self.max_val
        )

    def on_finish(self, result):
        self.matplotlib_widget.update_plot(
            result, 
            min_val=self.min_val,
            max_val=self.max_val
        )
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)

    def toggle_pause(self):
        """Ставит поток на паузу или возобновляет."""
        if self.sort_thread:
            self.sort_thread.is_paused = not self.sort_thread.is_paused
            self.pause_button.setText(
                "resume" if self.sort_thread.is_paused else "pause")

    def restart_sorting(self):
        """Перезапускает сортировку с новым массивом."""
        if self.sort_thread and self.sort_thread.isRunning():
            self.sort_thread.terminate()
            self.sort_thread.wait()
        
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.start_sorting()

    @property
    def min_val(self):
        return self.min_range.value()

    @property
    def max_val(self):
        return self.max_range.value()

    @property
    def is_reverse(self):
        return self.reverse.isChecked()

    @property
    def size_val(self):
        return self.array_size.value()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())