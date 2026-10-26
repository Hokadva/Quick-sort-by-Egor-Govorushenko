import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QCheckBox,
    QWidget, QPushButton, QHBoxLayout, QSpinBox, QLabel, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from enum import Enum
from random import randint
from typing import Callable
from my_sort import NUM_OF_MEDIAN_CANDIDATES


class OffsetTypes(Enum):
    LOW = "low"
    CENTER = "center"
    HIGH = "high"


class HighlightTypes(Enum):
    PIVOT = "red"
    CANDIDATE = "maroon"
    ELEMENT = "green"


def visualize_my_sort(array: list, reverse: bool, offset: int = 0) -> tuple[list, list, list]:
    current_highlight = []
    offsets = []
    
    if not array:
        return ([], [], [])
    
    arr_len = len(array)
    if arr_len == 1:
        return (array, [], [])

    if (arr_len < 10000 or
        arr_len <= NUM_OF_MEDIAN_CANDIDATES or NUM_OF_MEDIAN_CANDIDATES == 1):
        pivot = array[arr_len // 2]
        pivot_idx = arr_len // 2
        pivot = array[pivot_idx]
        current_highlight.append((pivot_idx + offset, HighlightTypes.PIVOT))
    else:
        candidates = [array[arr_len * (nm + 1) // NUM_OF_MEDIAN_CANDIDATES - 1]
                      for nm in range(NUM_OF_MEDIAN_CANDIDATES)]
        current_highlight += [
            (idx + offset, HighlightTypes.CANDIDATE)
            for idx in range(len(candidates))]
        
        for pivot in candidates:
            counter = 0
            for el in candidates:
                counter += int((el < pivot) ^ reverse)
                if counter > NUM_OF_MEDIAN_CANDIDATES // 2:
                    break
            if counter == NUM_OF_MEDIAN_CANDIDATES // 2:
                break
        pivot_idx = array.index(pivot) 
        current_highlight.append((pivot_idx + offset, HighlightTypes.PIVOT))

    lw_elements = []
    eq_elements = []
    hg_elements = []

    for idx, element in enumerate(array):
        current_highlight.append((idx + offset, HighlightTypes.ELEMENT))

        if element == pivot:
            eq_elements.append(element)
        elif (element < pivot) ^ reverse:
            lw_elements.append(element)
        else:
            hg_elements.append(element)

    for element in array:
        if element in lw_elements:
            offsets.append((element, OffsetTypes.LOW, offset))
        elif element in eq_elements:
            offsets.append(
                (element, OffsetTypes.CENTER, offset + len(lw_elements)))
        else:
            offsets.append(
                (element, OffsetTypes.HIGH, offset + len(lw_elements) +
                 len(eq_elements))
            )

    lw_answer = visualize_my_sort(lw_elements, reverse, offset)
    hg_answer = visualize_my_sort(
        hg_elements, reverse, offset + len(lw_elements) + len(eq_elements))

    answer = lw_answer[0] + eq_elements + hg_answer[0]
    current_highlight += lw_answer[1] + hg_answer[1]
    offsets += lw_answer[2] + hg_answer[2]
    return (answer, current_highlight, offsets)


class SortThread(QThread):
    step_signal = pyqtSignal(tuple, tuple, tuple, list, list)
    finished_signal = pyqtSignal()

    def __init__(self, array: list, delay: float):
        super().__init__()
        self.array = array
        self.new_array = array
        self.sorted_array, self.highlights, self.offsets = visualize_my_sort(self.array)
        self.delay = delay
        self.is_paused = False

    def run(self):
        idof = 0
        for idx, el in enumerate(self.highlights):
            current_highlight = self.highlights[idx]
            if (current_highlight[1] == HighlightTypes.CANDIDATE or
                current_highlight[1] == HighlightTypes.PIVOT):
                current_pivot = current_highlight
                current_highlight = ()
                current_offset = ()
                current_state_up = self.new_array
                current_state_down = self.new_array
                if current_highlight[1] == HighlightTypes.PIVOT:
                    for idh in range(idx, len(self.highlights)): #idh - idx - число
                        #элементов которые необходимо ликвидировать
                        if (self.highlights[idh] == HighlightTypes.CANDIDATE
                            or self.highlights[idh] == HighlightTypes.PIVOT):
                            break

                    for _ in range(idh - idx):
                        current_state_down.pop(self.offsets[idof + 1][2])

            else:
                current_offset = self.offsets[idof]
                idof += 1
                current_state_up = self.new_array
                current_state_down.append(current_offset[idof][0])
                if idx + 1 < len(self.highlights) and (
                    self.highlights[idx + 1][1] == HighlightTypes.CANDIDATE or
                    self.highlights[idx + 1][1] == HighlightTypes.PIVOT):
                    self.new_array = current_state_down

            self.step_signal.emit(current_highlight, current_pivot,
                                  current_offset, current_state_up,
                                  current_state_down)
            time.sleep(self.delay)

        self.finished_signal.emit()


class SortVisualizerWidget(QWidget):
    """Базовый виджет с двумя графиками."""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        self.ax_top = self.figure.add_subplot(211)
        self.ax_bottom = self.figure.add_subplot(212)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def update_plot(
            self, top_array, bottom_array):
        """Рисует верхний и нижний графики с переданными цветами."""
        self.ax_top.clear()
        self.ax_bottom.clear()
        self.ax_top.set_xticks([])
        self.ax_bottom.set_xticks([])

        self.ax_top.bar(range(len(top_array)), top_array)

        display_bottom = [0 if x is None else x for x in bottom_array]
        self.ax_bottom.bar(range(len(display_bottom)), display_bottom)

        self.canvas.draw()


class MainWindow(QMainWindow):
    MAX_ARRAY_SIZE = 10000
    BASE_DELAY = 4

    def __init__(self):
        super().__init__()
        self.sort_thread = None
        self._create_ui()
        self.restart_sorting()

    def _create_ui(self):
        self.setWindowTitle("Sorting array")
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

        speed_label = QLabel("Speed:")
        self.speed_edit = QSpinBox(self)
        self.speed_edit.setMaximum(50)
        self.speed_edit.setValue(25)
        self.speed_edit.setMinimum(1)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_edit)
        main_layout.addLayout(speed_layout)

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
        self.sort_thread = SortThread(
            self.original_array, delay=self.BASE_DELAY // self.speed)
        self.sort_thread.step_signal.connect(self.on_step)
        self.sort_thread.finished_signal.connect(self.on_finished)

        self.sort_thread.start()
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)

    def on_step(self, current_highlight, current_pivot, current_offset,
                current_state_up, current_state_down):
        self.matplotlib_widget.update_plot(current_highlight, current_pivot,
                                           current_offset, current_state_up,
                                           current_state_up)

    def on_finished(self):
        print("Сортировка завершена!")

    def toggle_pause(self):
        if self.sort_thread:
            self.sort_thread.is_paused = not self.sort_thread.is_paused
            self.pause_button.setText(
                "Resume" if self.sort_thread.is_paused else "Pause")

    def stop_sorting(self):
        self.sort_thread.is_stopped = True
        self.sort_thread.is_paused = False

        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)

    def restart_sorting(self):
        self.original_array = [
            randint(self.min_val, self.max_val) for _ in range(self.size_val)]
        self.matplotlib_widget.update_plot(self.original_array, [])
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)

    @property
    def speed(self):
        return self.speed_edit.value()

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
