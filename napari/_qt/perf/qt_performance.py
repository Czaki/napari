"""QtPerformance widget to show performance information."""

import time
from collections import deque
from statistics import mean
from typing import ClassVar

from qtpy.QtCore import Qt, QTimer
from qtpy.QtGui import QTextCursor
from qtpy.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from napari.utils import perf
from napari.utils.translations import trans

MEAN_DRAW_TIME = 2.0  # seconds


class TimeBasedCircularBuffer:
    def __init__(self, duration_seconds):
        self.buffer = deque()
        self.duration_seconds = duration_seconds

    def add_event(self, event):
        current_time = time.time()
        # Append event with current timestamp
        self.buffer.append((event, current_time))
        self._remove_old_events()

    def _remove_old_events(self):
        current_time = time.time()
        # Remove events older than duration_seconds
        while (
            self.buffer
            and current_time - self.buffer[0][1] > self.duration_seconds
        ):
            self.buffer.popleft()

    def get_recent_events(self):
        # Optionally, remove old events first
        self._remove_old_events()
        # Return a list of recent events without timestamps
        return [event for event, _ in self.buffer]

    def aggregate(self, aggregation_func):
        # Apply the aggregation function to the recent events
        recent_events = self.get_recent_events()
        return aggregation_func(recent_events)


class TextLog(QTextEdit):
    """Text window we can write "log" messages to.

    TODO: need to limit length, erase oldest messages?
    """

    def append(self, name: str, time_ms: float) -> None:
        """Add one line of text for this timer.

        Parameters
        ----------
        name : str
            Timer name.
        time_ms : float
            Duration of the timer in milliseconds.
        """
        self.moveCursor(QTextCursor.MoveOperation.End)
        self.setTextColor(Qt.GlobalColor.red)
        self.insertPlainText(
            trans._('{time_ms:5.0f}ms {name}\n', time_ms=time_ms, name=name)
        )


class QtPerformance(QWidget):
    """Dockable widget to show performance info.

    Notes
    -----

    1) The progress bar doesn't show "progress", we use it as a bar graph to
       show the average duration of recent "UpdateRequest" events. This
       is actually not the total draw time, but it's generally the biggest
       part of each frame.

    2) We log any event whose duration is longer than the threshold.

    3) We show uptime so you can tell if this window is being updated at all.

    Attributes
    ----------
    start_time : float
        Time is seconds when widget was created.
    bar : QProgressBar
        The progress bar we use as your draw time indicator.
    thresh_ms : float
        Log events whose duration is longer then this.
    timer_label : QLabel
        We write the current "uptime" into this label.
    timer : QTimer
        To update our window every UPDATE_MS.
    """

    # We log events slower than some threshold (in milliseconds).
    THRESH_DEFAULT = 100
    THRESH_OPTIONS: ClassVar[list[str]] = [
        '1',
        '5',
        '10',
        '15',
        '20',
        '30',
        '40',
        '50',
        '100',
        '200',
    ]

    # Update at 250ms / 4Hz for now. The more we update more alive our
    # display will look, but the more we will slow things down.
    UPDATE_MS = 250

    def __init__(self) -> None:
        """Create our windgets."""
        super().__init__()
        layout = QVBoxLayout()
        # We log slow events to this window.
        self.log = TextLog()

        # For our "uptime" timer.
        self.start_time = time.time()
        self._average_queue = TimeBasedCircularBuffer(MEAN_DRAW_TIME)

        # Label for our progress bar.
        # Label for our progress bar.
        bar_label = QLabel(
            trans._(
                'Mean draw time for last {mean_draw_time} seconds:',
                mean_draw_time=MEAN_DRAW_TIME,
            )
        )
        layout.addWidget(bar_label)

        # Progress bar is not used for "progress", it's just a bar graph to show
        # the "draw time", the duration of the "UpdateRequest" event.
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(50)
        bar.setFormat('%vms')
        layout.addWidget(bar)
        self.bar = bar

        # We let the user set the "slow event" threshold.
        self.thresh_ms = self.THRESH_DEFAULT
        self.thresh_combo = QComboBox()
        self.thresh_combo.addItems(self.THRESH_OPTIONS)
        self.thresh_combo.currentTextChanged.connect(self._change_thresh)
        self.thresh_combo.setCurrentText(str(self.thresh_ms))

        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel(trans._('Show Events Slower Than:')))
        combo_layout.addWidget(self.thresh_combo)
        combo_layout.addWidget(QLabel(trans._('milliseconds')))
        combo_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        layout.addLayout(combo_layout)

        layout.addWidget(self.log)

        # Uptime label. To indicate if the widget is getting updated.
        label = QLabel('')
        layout.addWidget(label)
        self.timer_label = label

        self.setLayout(layout)

        # Update us with a timer.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.setInterval(self.UPDATE_MS)
        self.timer.start()

    def _change_thresh(self, text):
        """Threshold combo box change."""
        self.thresh_ms = float(text)
        self.log.clear()  # start fresh with this new threshold

    def _get_timer_info(self):
        """Get the information from the timers that we want to display."""
        average = None
        average_li = []
        long_events = []

        # We don't update any GUI/widgets while iterating over the timers.
        # Updating widgets can create immediate Qt Events which would modify the
        # timers out from under us!
        for name, timer in perf.timers.timers.items():
            # The Qt Event "UpdateRequest" is the main "draw" event, so
            # that's what we use for our progress bar.
            if name.startswith('UpdateRequest'):
                average = timer.average
                average_li.append(timer.average)

            # Log any "long" events to the text window.
            if timer.max >= self.thresh_ms:
                long_events.append((name, timer.max))
        if average_li:
            average = max(average_li)
        return average, long_events

    def update(self):
        """Update our label and progress bar and log any new slow events."""
        # Update our timer label.
        elapsed = time.time() - self.start_time
        self.timer_label.setText(
            trans._('Uptime: {elapsed:.2f}', elapsed=elapsed)
        )

        average, long_events = self._get_timer_info()

        # Now safe to update the GUI: progress bar first.
        if average is not None:
            self._average_queue.add_event(average)
            time_avg = int(self._average_queue.aggregate(mean))
            if time_avg > 1000:
                self.bar.setMaximum(10000)
            if time_avg > 100:
                self.bar.setMaximum(1000)
            else:
                self.bar.setMaximum(100)

            self.bar.setValue(time_avg)

        # And log any new slow events.
        for name, time_ms in long_events:
            self.log.append(name, time_ms)

        # Clear all the timers since we've displayed them. They will immediately
        # start accumulating numbers for the next update.
        perf.timers.clear()
