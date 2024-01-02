import logging
import sys
from queue import Queue, Empty
from threading import Thread
from tkinter import Tk, messagebox
from typing import Callable, Optional, Any

from naevpm.core.abstract_thread_communication import AbstractCommunication

logger = logging.getLogger(__name__)


class ThreadCommunication(AbstractCommunication):
    _root: Tk
    _queue: Queue

    # assuming variable read / writes are atomic in Python
    closed = False

    def __init__(self, root: Tk, queue: Queue):
        self._root = root
        self._queue = queue

    def message(self, msg: str, delay: bool = False):
        if not self.closed:
            # queue is thread safe
            self._queue.put(msg)
            if not delay:
                # Assuming the event system of tkinter is thread safe
                self._root.event_generate('<<ThreadedTask.RequestGuiUpdate>>')

    # def request_gui_update(self):
    #     if not self.closed:
    #         # Assuming the event system of tkinter is thread safe
    #         self._root.event_generate('<<ThreadedTask.RequestGuiUpdate>>')


class ThreadedTask:
    thread: Thread
    communication: ThreadCommunication
    label: str
    completion_callback: Callable[[Optional[Any], Optional[Exception]], None]
    return_value: Optional[Any]
    exception: Exception


class TkThreading:
    _root: Tk
    _queue: Queue
    _threaded_tasks: list[ThreadedTask]
    _update_gui_fn: Optional[Callable[[str], None]]
    _detect_completed_task_schedule: Optional[str] = None

    def __init__(self, root: Tk):
        super().__init__()
        self._root = root
        self._queue = Queue()
        self._threaded_tasks = []
        self._update_gui_fn = None

        root.bind('<<ThreadedTask.RequestGuiUpdate>>', self._process_queue)

    def set_update_gui_fn(self, update_gui_fn: Callable[[str], None]):
        self._update_gui_fn = update_gui_fn

    # noinspection PyUnusedLocal
    def _process_queue(self, ev=None) -> None:
        """
        @param ev: Is only set when function is called by the tkinter event system
        """
        try:
            msg = self._queue.get_nowait()

            logger.info(msg)

            # Update GUI
            if self._update_gui_fn is not None:
                self._update_gui_fn(msg)

            # In case the task added multiple queue events to process without requesting immediate GUI update,
            # schedule this function in the next loop otherwise the additional
            # queue items are never processed
            if self._queue.qsize() > 0:
                # Process another queue event in the next loop
                self._root.after(100, self._process_queue)
        except Empty:
            pass

    def _detect_completed_tasks(self):
        completed_threaded_tasks = []
        for threaded_task in self._threaded_tasks:
            if not threaded_task.thread.is_alive():
                completed_threaded_tasks.append(threaded_task)
        for completed_threaded_task in completed_threaded_tasks:
            self._threaded_tasks.remove(completed_threaded_task)
        if len(self._threaded_tasks) > 0:
            self._detect_completed_task_schedule = self._root.after(100, self._detect_completed_tasks)
        else:
            self._detect_completed_task_schedule = None
        # loop a second time over completed tasks to run the callbacks that can throw exceptions.
        # Even if a callback throws an error, continue calling the callbacks.
        for completed_threaded_task in completed_threaded_tasks:
            if completed_threaded_task is not None:
                # noinspection PyBroadException
                try:
                    completed_threaded_task.completion_callback(
                        completed_threaded_task.return_value,
                        completed_threaded_task.exception)
                except Exception:
                    self._root.report_callback_exception(*sys.exc_info())

    def run_threaded_task(self, label: str, threaded_task_fn: Callable[[ThreadCommunication], Any],
                          completion_callback: Optional[Callable[[Optional[Any], Optional[Exception]], None]] = None):
        if self._detect_completed_task_schedule is None:
            self._detect_completed_task_schedule = self._root.after(100, self._detect_completed_tasks)

        comm = ThreadCommunication(self._root, self._queue)

        t = ThreadedTask()

        def top_level_exception_handler(c: ThreadCommunication):
            try:
                t.return_value = threaded_task_fn(c)
            except Exception as e:
                t.exception = e

        thread = Thread(target=top_level_exception_handler, args=[comm])

        t.label = label
        t.communication = comm
        t.thread = thread
        t.completion_callback = completion_callback
        t.exception = None
        t.return_value = None
        self._threaded_tasks.append(t)

        thread.start()

    def close(self) -> bool:
        """
        Capture the delete window event and call this function first to check if the window should really be destroyed:
            self.protocol("WM_DELETE_WINDOW", close_fn)

        @return: True if GUI can continue to close, False if it should not close
        """
        for threaded_background_task in self._threaded_tasks:
            if threaded_background_task.thread.is_alive():
                yes = messagebox.askyesno("Running background task",
                                          f"Background task '{threaded_background_task.label}' is still running. "
                                          f"Ignore?")
                if not yes:
                    return False
                threaded_background_task.communication.closed = True
        return True
