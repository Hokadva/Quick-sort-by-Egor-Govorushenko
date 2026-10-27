"""
App that visualize my realisation of quick sort
"""
#pylint: disable=[E0401, E0611, R0914, R0912, C0103, R0917, R0913]
#pylint: disable=[R0915, R0902, W0201]
import sys
import threading
from enum import Enum
from random import randint

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSpinBox,
    QVBoxLayout, QWidget)
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from my_sort import MIN_ARRAY_SIZE, NUM_OF_MEDIAN_CANDIDATES


class OffsetTypes(Enum):
    """
    Enum class for offsets
    """
    LOW = "low"
    CENTER = "center"
    HIGH = "high"


class Colors(Enum):
    """
    Enum class for colors
    """
    SKY_BLUE = "skyblue"
    LIGHT_GRAY = "lightgray"
    BLUE = "blue"
    ORANGE = "orange"
    PURPLE = "purple"



class HighlightTypes(Enum):
    """
    Enum class for highlights
    """
    PIVOT = "red"
    CANDIDATE = "maroon"
    ELEMENT = "green"


def visualize_my_sort(
        array: list, reverse: bool, offset: int = 0) -> tuple[list, list, list]:
    """
    Function that return sorted array, highlights changed elements and
    offsets elements
    """
    current_highlight = []
    offsets = []

    if not array:
        return ([], [], [])

    arr_len = len(array)
    if arr_len == 1:
        return (array, [], [])

    if (arr_len < MIN_ARRAY_SIZE or
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
                pivot_idx = array.index(pivot)
                break

        current_highlight.append((pivot_idx + offset, HighlightTypes.PIVOT))

    lw_elements = []
    eq_elements = []
    hg_elements = []
    right_limits = []

    for idx, element in enumerate(array):
        current_highlight.append((idx + offset, HighlightTypes.ELEMENT))

        if element == pivot:
            eq_elements.append(element)
            right_limits.append(offset + len(lw_elements) + len(eq_elements))
        elif (element < pivot) ^ reverse:
            lw_elements.append(element)
            right_limits.append(offset + len(lw_elements))
        else:
            hg_elements.append(element)
            right_limits.append(
                offset + len(lw_elements) + len(hg_elements) + len(eq_elements))

    for idx, element in enumerate(array):
        if element in lw_elements:
            offsets.append((element, OffsetTypes.LOW, offset,
                            right_limits[idx]))
        elif element in eq_elements:
            offsets.append(
                (element, OffsetTypes.CENTER,
                 offset + len(lw_elements) - 1, right_limits[idx]))
        else:
            offsets.append(
                (element, OffsetTypes.HIGH,
                 offset + len(lw_elements) + len(eq_elements) - 2,
                 right_limits[idx]))

    lw_answer = visualize_my_sort(lw_elements, reverse, offset)
    hg_answer = visualize_my_sort(
        hg_elements, reverse, offset + len(lw_elements) + len(eq_elements))

    answer = lw_answer[0] + eq_elements + hg_answer[0]
    current_highlight += lw_answer[1] + hg_answer[1]
    offsets += lw_answer[2] + hg_answer[2]
    return (answer, current_highlight, offsets)


class SortThread(QThread):
    """
    Thread class
    """
    step_signal = pyqtSignal(tuple, tuple, tuple, list, list)
    finished_signal = pyqtSignal()

    def __init__(self, array: list, delay: float, reverse: bool):
        """
        Init class
        """
        super().__init__()
        self.array = array
        self.new_array = array[:]
        self.sorted_array, self.highlights, self.offsets = visualize_my_sort(
            self.array, reverse=reverse)
        self.delay = delay
        self.stride = max(1, len(array) // 100)

        self._resume = threading.Event()
        self._resume.set()
        self._frame_done = threading.Event()
        self._frame_done.set()

    @property
    def is_paused(self) -> bool:
        """
        Get pause property
        """
        return not self._resume.is_set()

    def pause(self):
        """
        Pause sorting
        """
        self._resume.clear()

    def resume(self):
        """
        Resume sorting
        """
        self._resume.set()

    def stop(self):
        """
        Stop sorting
        """
        self.requestInterruption()
        self._resume.set()
        self._frame_done.set()

    def frame_done(self):
        """
        Frane done
        """
        self._frame_done.set()

    def _wait(self, event: threading.Event) -> bool:
        """
        Waiting for an event; False if a stop was requested
        """
        while not event.wait(0.05):
            if self.isInterruptionRequested():
                return False
        return not self.isInterruptionRequested()

    def run(self):
        """
        Run thread
        """
        idof = 0
        element_counter = 0
        current_pivot = ()
        current_state_up = self.new_array[:]
        current_state_down = self.new_array[:]
        last_idx = len(self.highlights) - 1

        for idx, current_highlight in enumerate(self.highlights):
            if not self._wait(self._resume):
                return

            is_key_step = current_highlight[1] != HighlightTypes.ELEMENT

            if is_key_step:
                current_pivot = current_highlight
                current_offset = ()
                current_state_up = self.new_array[:]
                current_state_down = self.new_array[:]
                if current_highlight[1] == HighlightTypes.PIVOT:
                    for idh in range(idx + 1, len(self.highlights)):
                        if self.highlights[idh][1] != HighlightTypes.ELEMENT:
                            break
                    else:
                        idh = len(self.highlights)

                    seg_start = self.highlights[idx + 1][0]
                    for _ in range(idh - idx - 1):
                        current_state_down.pop(seg_start)
            else:
                current_offset = self.offsets[idof]
                idof += 1
                current_state_down.insert(
                    current_offset[3] - 1, current_offset[0])
                if idx + 1 < len(self.highlights) and (
                        self.highlights[idx + 1][1] != HighlightTypes.ELEMENT):
                    self.new_array = current_state_down[:]
                element_counter += 1

            if not (is_key_step or idx == last_idx
                    or element_counter % self.stride == 0):
                continue

            if not self._wait(self._frame_done):
                return
            self._frame_done.clear()
            self.step_signal.emit(current_highlight, current_pivot,
                                  current_offset, current_state_up[:],
                                  current_state_down[:])
            self.msleep(int(self.delay * 1000))

        self.finished_signal.emit()


class SortVisualizerWidget(QWidget):
    """
    Widget with two graphs
    """
    def __init__(self, parent=None):
        """
        Init class
        """
        super().__init__(parent)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax_top = self.figure.add_subplot(211)
        self.ax_bottom = self.figure.add_subplot(212)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def update_size(self, min_val: int, max_val: int, arr_len: int):
        """
        Update size function
        """
        self._arr_len = arr_len
        self._min_val = min_val
        self._max_val = max_val

        for ax, title in ((self.ax_top, "Global State"),
                          (self.ax_bottom, "Local State (Current Processing)")):
            ax.clear()
            ax.set_title(title)
            ax.set_xticks([])
            ax.set_xlim(-1, arr_len)
            ax.set_ylim(min_val, max_val)

        self.top_bars = self.ax_top.bar(
            range(arr_len), [0] * arr_len, linewidth=0)
        self.bottom_bars = self.ax_bottom.bar(
            range(arr_len), [0] * arr_len, linewidth=0)
        self._top_cache = [None] * arr_len
        self._bottom_cache = [None] * arr_len

    @staticmethod
    def _apply(bars, heights, colors, cache):
        """
        It only changes the columns that have changed
        """
        for i, rect in enumerate(bars):
            h = heights[i] if i < len(heights) else 0
            c = colors[i] if i < len(colors) else Colors.LIGHT_GRAY.value
            if cache[i] != (h, c):
                rect.set_height(h)
                rect.set_facecolor(c)
                cache[i] = (h, c)

    def update_plot(self, current_highlight: tuple, current_pivot: tuple,
                    current_offset: tuple, top_array: list, bottom_array: list):
        """
        Updating graphics
        """
        top_colors = [Colors.SKY_BLUE.value] * len(top_array)
        if current_highlight:
            h_idx, h_type = current_highlight
            if 0 <= h_idx < len(top_colors):
                top_colors[h_idx] = h_type.value
        if current_pivot:
            p_idx, p_type = current_pivot
            if 0 <= p_idx < len(top_colors):
                top_colors[p_idx] = p_type.value

        display_bottom = [0 if x is None else x for x in bottom_array]
        bottom_colors = [Colors.LIGHT_GRAY.value] * len(display_bottom)
        if current_offset:
            value, group_type, _, __ = current_offset
            color = {OffsetTypes.LOW: Colors.BLUE.value,
                     OffsetTypes.CENTER: Colors.ORANGE.value,
                     OffsetTypes.HIGH: Colors.PURPLE.value}[group_type]
            for i, x in enumerate(display_bottom):
                if x == value and bottom_colors[i] == Colors.LIGHT_GRAY.value:
                    bottom_colors[i] = color
                    break

        self._apply(self.top_bars, top_array, top_colors, self._top_cache)
        self._apply(self.bottom_bars, display_bottom, bottom_colors,
                    self._bottom_cache)
        self.canvas.draw()


class MainWindow(QMainWindow):
    """
    Main window of program
    """
    MAX_ARRAY_SIZE = 1000
    MIN_RANGE = -10000
    MAX_RANGE = 10000
    MAX_SPEED = 200
    MIN_SPEED = 1
    BASE_DELAY = 4

    def __init__(self):
        """
        Init class
        """
        super().__init__()
        self.sort_thread = None

        self.setWindowTitle("Sorting array")
        self._main_layout = QVBoxLayout()

        self.matplotlib_widget = SortVisualizerWidget()
        self._main_layout.addWidget(self.matplotlib_widget)

        min_range_label = QLabel("Minimum possible value:")
        self.min_range = QSpinBox()
        self.min_range.setMaximum(self.MAX_RANGE)
        self.min_range.setMinimum(self.MIN_RANGE)
        self.min_range.setValue(-100)
        min_layout = QHBoxLayout()
        min_layout.addWidget(min_range_label)
        min_layout.addWidget(self.min_range)
        self._main_layout.addLayout(min_layout)

        max_range_label = QLabel("Maximum possible value:")
        self.max_range = QSpinBox()
        self.max_range.setMaximum(self.MAX_RANGE)
        self.max_range.setMinimum(self.MIN_RANGE)
        self.max_range.setValue(100)
        max_layout = QHBoxLayout()
        max_layout.addWidget(max_range_label)
        max_layout.addWidget(self.max_range)
        self._main_layout.addLayout(max_layout)

        array_size_label = QLabel("Array size:")
        self.array_size = QSpinBox(self)
        self.array_size.setMaximum(self.MAX_ARRAY_SIZE)
        self.array_size.setValue(20)
        self.array_size.setMinimum(1)
        array_size_layout = QHBoxLayout()
        array_size_layout.addWidget(array_size_label)
        array_size_layout.addWidget(self.array_size)
        self._main_layout.addLayout(array_size_layout)

        speed_label = QLabel("Speed:")
        self.speed_edit = QSpinBox(self)
        self.speed_edit.setMaximum(self.MAX_SPEED)
        self.speed_edit.setValue(25)
        self.speed_edit.setMinimum(self.MIN_SPEED)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_edit)
        self._main_layout.addLayout(speed_layout)

        self.reverse = QCheckBox("Sorting in reverse order")
        self._main_layout.addWidget(self.reverse)

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
        self._main_layout.addLayout(buttons_layout)

        central_widget = QWidget()
        central_widget.setLayout(self._main_layout)
        self.setCentralWidget(central_widget)

        self.restart_sorting()

    def start_sorting(self):
        """
        Start sorting
        """
        self._stop_thread()
        self.sort_thread = SortThread(
            self.original_array, delay=self.BASE_DELAY / self.speed,
            reverse=self.is_reverse)
        self.sort_thread.step_signal.connect(self.on_step)
        self.sort_thread.finished_signal.connect(self.on_finished)
        self.sort_thread.start()

        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.pause_button.setText("Pause")

    def on_step(self, current_highlight: tuple, current_pivot: tuple,
                current_offset: tuple, current_state_up: list[int],
                current_state_down: list[int]):
        """
        Step function
        """
        self.matplotlib_widget.update_plot(
            current_highlight, current_pivot, current_offset,
            current_state_up, current_state_down)
        if self.sort_thread:
            self.sort_thread.frame_done()

    def on_finished(self):
        """
        Finish process of visualizate sorting
        """
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("Pause")

    def toggle_pause(self):
        """
        Toggle pause(continue) state
        """
        t = self.sort_thread
        if not t or not t.isRunning():
            return
        if t.is_paused:
            t.resume()
            self.pause_button.setText("Pause")
        else:
            t.pause()
            self.pause_button.setText("Resume")

    def _stop_thread(self):
        """
        Stop thread
        """
        t = self.sort_thread
        if t is None:
            return
        for sig in (t.step_signal, t.finished_signal):
            try:
                sig.disconnect()
            except TypeError:
                pass
        t.stop()
        t.wait()
        self.sort_thread = None

    def stop_sorting(self):
        """
        Stop array sorting
        """
        self.sort_thread.is_stopped = True
        self.sort_thread.is_paused = False

        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)

    def restart_sorting(self):
        """
        Restarting sort (generate new array)
        """
        self._stop_thread()
        self.original_array = [
            randint(self.min_val, self.max_val) for _ in range(self.size_val)]
        self.matplotlib_widget.update_size(
            self.min_val, self.max_val, self.size_val)
        self.matplotlib_widget.update_plot(
            (), (), (), self.original_array, [])
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("Pause")

    def closeEvent(self, event):
        """
        Close event from MainWindow
        """
        self._stop_thread()
        super().closeEvent(event)

    @property
    def speed(self):
        """
        Return speed from QSpinBox
        """
        return self.speed_edit.value()

    @property
    def min_val(self):
        """
        Return min range from QSpinBox
        """
        return self.min_range.value()

    @property
    def max_val(self):
        """
        Return max range from QSpinBox
        """
        return self.max_range.value()

    @property
    def is_reverse(self):
        """
        Return is reverse order from Checkbox
        """
        return self.reverse.isChecked()

    @property
    def size_val(self):
        """
        Return array size from QSpinBox
        """
        return self.array_size.value()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
