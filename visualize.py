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

    for i, element in enumerate(lw_elements):
        offsets.append((element, OffsetTypes.LOW.value, offset + i))

    for i, element in enumerate(eq_elements):
        offsets.append((element, OffsetTypes.CENTER.value,
            offset + len(lw_elements) + i))

    for i, element in enumerate(hg_elements):
        offsets.append(
            (element, OffsetTypes.HIGH.value, offset +
             len(lw_elements) + len(eq_elements) + i))

    lw_answer = visualize_my_sort(lw_elements, reverse, offset)
    hg_answer = visualize_my_sort(
        hg_elements, reverse, offset + len(lw_elements) + len(eq_elements))

    answer = lw_answer[0] + eq_elements + hg_answer[0]
    current_highlight += lw_answer[1] + hg_answer[1]
    offsets += lw_answer[2] + hg_answer[2]
    print((answer, current_highlight, offsets))
    return (answer, current_highlight, offsets)


class SortThread(QThread):
    # 4-й аргумент - int (для пивота)
    step_signal = pyqtSignal(list, list, int, list, list) 
    finished_signal = pyqtSignal(list)

    def __init__(self, array: list, delay: float, reverse: bool = False):
        super().__init__()
        self.array = array
        self.delay = delay
        self.reverse = reverse
        self.is_paused = False

    def run(self):
        sorted_array, highlights, offsets = visualize_my_sort(self.array, self.reverse)
        
        global_state = self.array[:] 
        
        # Нижний массив изначально пустой (None), чтобы рисовать только добавленные элементы
        local_state = [None] * len(self.array)
        
        offset_idx = 0
        current_pivot_value = None 
        
        for idx, (h_idx, h_type) in enumerate(highlights):
            current_highlights_bottom = []
            current_highlights_top = []

            # --- Логика для верхнего графика ---
            if h_type == HighlightTypes.PIVOT:
                current_pivot_value = global_state[h_idx]
                current_highlights_top = [(h_idx, HighlightTypes.ELEMENT)]
            else:
                current_highlights_top = [(h_idx, HighlightTypes.ELEMENT)]

            # --- Логика для нижнего графика ---
            if h_type == HighlightTypes.ELEMENT and offset_idx < len(offsets):
                value, group_type, target_idx = offsets[offset_idx]
                
                # Просто ставим значение на заранее вычисленное место
                if 0 <= target_idx < len(local_state):
                    local_state[target_idx] = value
                    current_highlights_bottom = [(target_idx, group_type)]
                
                offset_idx += 1

            # Ищем, где сейчас находится текущий пивот на верхнем графике
            pivot_idx = -1
            if current_pivot_value is not None:
                try:
                    pivot_idx = global_state.index(current_pivot_value)
                except ValueError:
                    pass

            self.step_signal.emit(
                global_state[:], 
                local_state[:], 
                pivot_idx, 
                current_highlights_top, 
                current_highlights_bottom
            )
            
            time.sleep(self.delay)
            while self.is_paused:
                time.sleep(0.1)

            # --- Конец текущего куска ---
            if h_type == HighlightTypes.PIVOT or idx == len(highlights) - 1:
                # Переносим всё, что насобирали в нижнем графике, наверх
                for i in range(len(global_state)):
                    if local_state[i] is not None:
                        global_state[i] = local_state[i]
                
                # Очищаем нижний график для следующего подмассива
                local_state = [None] * len(self.array)

        self.finished_signal.emit(sorted_array)


class SortVisualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        self.ax_top = self.figure.add_subplot(211)
        self.ax_bottom = self.figure.add_subplot(212)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self.ax_top.set_title("Global State")
        self.ax_bottom.set_title("Local State (Current Processing)")

    def update_plot(self, top_array, bottom_array, pivot_idx,
                    top_highlights, bottom_highlights,
                    min_val: int = 0, max_val: int = 100):
        
        self.ax_top.clear()
        self.ax_bottom.clear()
        self.ax_top.set_xticks([])
        self.ax_bottom.set_xticks([])

        # --- Верхний график ---
        top_colors = ['skyblue'] * len(top_array)
        
        if isinstance(pivot_idx, int) and 0 <= pivot_idx < len(top_colors):
            top_colors[pivot_idx] = HighlightTypes.PIVOT.value
            
        for idx, h_type in top_highlights:
            if 0 <= idx < len(top_colors):
                if top_colors[idx] != HighlightTypes.PIVOT.value:
                    top_colors[idx] = h_type.value

        self.ax_top.bar(range(len(top_array)), top_array, color=top_colors)

        # --- Нижний график ---
        # Заменяем None на 0 для отрисовки
        display_bottom = [0 if x is None else x for x in bottom_array]
        
        # По умолчанию все столбики прозрачные/серые (пустые)
        bottom_colors = ['lightgray'] * len(display_bottom)
        
        for idx, h_type in bottom_highlights:
            if 0 <= idx < len(bottom_colors):
                if h_type == OffsetTypes.LOW.value:
                    bottom_colors[idx] = 'blue'
                elif h_type == OffsetTypes.CENTER.value:
                    bottom_colors[idx] = 'orange'
                elif h_type == OffsetTypes.HIGH.value:
                    bottom_colors[idx] = 'purple'
                else:
                    bottom_colors[idx] = 'green'

        self.ax_bottom.bar(range(len(display_bottom)), display_bottom, color=bottom_colors)

        # Настройка Y
        if top_array:
            padding = max(10, (max_val - min_val) * 0.1)
            self.ax_top.set_ylim(min_val - padding, max_val + padding)
            self.ax_bottom.set_ylim(min_val - padding, max_val + padding)
        
        self.canvas.draw()


# ==========================================
# 4. Главное окно
# ==========================================
class MainWindow(QMainWindow):
    MAX_ARRAY_SIZE = 10000
    DELAY = 50

    def __init__(self):
        super().__init__()
        self.sort_thread = None
        self._create_ui()
        self.start_sorting()

    def _create_ui(self):
        self.setWindowTitle("Sorting array")
        main_layout = QVBoxLayout()
        
        self.matplotlib_widget = SortVisualizerWidget()
        main_layout.addWidget(self.matplotlib_widget)

        # Настройки
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

        # Кнопки
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
        
        delay = max(0.005, self.DELAY / self.size_val)
        
        original_array = [randint(self.min_val, self.max_val)
            for _ in range(self.size_val)]

        # ИСПРАВЛЕНИЕ: вместо [] ставим -1
        self.matplotlib_widget.update_plot(
            original_array, 
            original_array,
            -1,  # pivot_idx (нет активного пивота)
            [],  # top_highlights
            [],  # bottom_highlights
            min_val=self.min_val, 
            max_val=self.max_val
        )

        self.sort_thread = SortThread(
            original_array[:],
            delay, self.is_reverse
        )
        self.sort_thread.step_signal.connect(self.on_step)
        self.sort_thread.finished_signal.connect(self.on_finish)
        self.sort_thread.start()

    def on_step(self, top_array, bottom_array, pivot_idx, top_hl, bottom_hl):
        self.matplotlib_widget.update_plot(
            top_array, bottom_array, pivot_idx,
            top_hl, bottom_hl,
            min_val=self.min_val,
            max_val=self.max_val
        )

    def on_finish(self, result):
        self.matplotlib_widget.update_plot(
            result, result, -1,  # -1 означает, что нет активного пивота
            [], [],
            min_val=self.min_val,
            max_val=self.max_val
        )
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)

    def toggle_pause(self):
        if self.sort_thread:
            self.sort_thread.is_paused = not self.sort_thread.is_paused
            self.pause_button.setText(
                "resume" if self.sort_thread.is_paused else "pause")

    def restart_sorting(self):
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
