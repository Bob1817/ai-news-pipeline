import uuid
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

class TaskSignals(QObject):
    progress = pyqtSignal(int, str)
    complete = pyqtSignal(str, dict)
    error = pyqtSignal(str, str)
    status = pyqtSignal(str, str)

class TaskRunner(QRunnable):
    def __init__(self, task_id, task_type, params, callback):
        super().__init__()
        self.task_id = task_id
        self.task_type = task_type
        self.params = params
        self.callback = callback
        self.signals = TaskSignals()
        self.is_cancelled = False
    
    def cancel(self):
        self.is_cancelled = True
    
    @pyqtSlot()
    def run(self):
        try:
            result = self.callback(self.task_id, self.params, self.signals)
            self.signals.complete.emit(self.task_id, result)
        except Exception as e:
            self.signals.error.emit(self.task_id, str(e))

class TaskManager(QObject):
    progress_signal = pyqtSignal(str, int, str)
    complete_signal = pyqtSignal(str, str, dict)
    error_signal = pyqtSignal(str, str)
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def initialize(self):
        if self._initialized:
            return
        super().__init__()
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(3)
        self.active_tasks = {}
        self._initialized = True
    
    def submit_task(self, task_type, params, callback):
        task_id = str(uuid.uuid4())[:8]
        runner = TaskRunner(task_id, task_type, params, callback)
        
        def on_progress(progress, message):
            if hasattr(self, 'progress_signal'):
                self.progress_signal.emit(task_id, progress, message)
        
        def on_complete(task_id, result):
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            if hasattr(self, 'complete_signal'):
                self.complete_signal.emit(task_id, task_type, result)
        
        def on_error(task_id, error):
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            if hasattr(self, 'error_signal'):
                self.error_signal.emit(task_id, error)
        
        runner.signals.progress.connect(on_progress)
        runner.signals.complete.connect(on_complete)
        runner.signals.error.connect(on_error)
        
        self.active_tasks[task_id] = runner
        self.thread_pool.start(runner)
        
        return task_id
    
    def cancel_task(self, task_id):
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]
            return True
        return False
    
    def get_active_task_count(self):
        return len(self.active_tasks)