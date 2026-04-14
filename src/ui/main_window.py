import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QMenuBar, QMenu,
    QStatusBar, QVBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI新闻自动化系统")
        self.setMinimumSize(1024, 768)
        
        self.collect_tab = None
        self.article_tab = None
        self.publish_tab = None
        self.task_manager = None
        self.config_manager = None
        
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
    
    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        self.load_tabs()
    
    def load_tabs(self):
        from src.ui.collect_tab import CollectTab
        from src.ui.article_tab import ArticleTab
        from src.ui.publish_tab import PublishTab
        
        self.collect_tab = CollectTab()
        self.article_tab = ArticleTab()
        self.publish_tab = PublishTab()
        
        self.tab_widget.addTab(
            self.collect_tab, 
            QIcon.fromTheme("download"), 
            "采集"
        )
        self.tab_widget.addTab(
            self.article_tab, 
            QIcon.fromTheme("document-edit"), 
            "文章管理"
        )
        self.tab_widget.addTab(
            self.publish_tab, 
            QIcon.fromTheme("upload"), 
            "发布"
        )
    
    def setup_menu(self):
        self.menu_bar = QMenuBar()
        
        file_menu = QMenu("文件", self)
        file_menu.addAction("导出数据", self.export_data)
        file_menu.addAction("退出", self.close)
        
        settings_menu = QMenu("设置", self)
        settings_menu.addAction("系统设置", self.open_settings)
        
        help_menu = QMenu("帮助", self)
        help_menu.addAction("关于", self.show_about)
        
        self.menu_bar.addMenu(file_menu)
        self.menu_bar.addMenu(settings_menu)
        self.menu_bar.addMenu(help_menu)
        
        self.setMenuBar(self.menu_bar)
    
    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def set_task_manager(self, task_manager):
        self.task_manager = task_manager
        
        if hasattr(task_manager, 'progress_signal'):
            task_manager.progress_signal.connect(self.on_task_progress)
        if hasattr(task_manager, 'complete_signal'):
            task_manager.complete_signal.connect(self.on_task_complete)
        if hasattr(task_manager, 'error_signal'):
            task_manager.error_signal.connect(self.on_task_error)
    
    def set_config_manager(self, config_manager):
        self.config_manager = config_manager
        
        if self.collect_tab:
            self.collect_tab.set_config_manager(config_manager)
        if self.article_tab:
            self.article_tab.set_config_manager(config_manager)
        if self.publish_tab:
            self.publish_tab.set_config_manager(config_manager)
    
    def on_task_progress(self, task_id, progress, message):
        self.status_bar.showMessage(f"任务 {task_id}: {message} ({progress}%)")
    
    def on_task_complete(self, task_id, task_type, result):
        self.status_bar.showMessage(f"任务 {task_id} 完成")
        
        if task_type == 'pipeline' and result.get('success'):
            QMessageBox.information(
                self,
                "任务完成",
                f"新闻采集: {result.get('news_count', 0)}条\n"
                f"主题提炼: {result.get('theme_count', 0)}个\n"
                f"文章生成: {result.get('article_count', 0)}篇"
            )
    
    def on_task_error(self, task_id, error):
        self.status_bar.showMessage(f"任务 {task_id} 失败")
        QMessageBox.critical(self, "任务失败", f"错误信息: {error}")
    
    def export_data(self):
        from src.utils.exporter import export_all_data
        try:
            export_all_data()
            QMessageBox.information(self, "导出成功", "数据已导出")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))
    
    def open_settings(self):
        from src.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.config_manager, self)
        dialog.exec()
    
    def show_about(self):
        QMessageBox.about(
            self,
            "关于",
            "AI新闻自动化系统 v1.0.0\n\n"
            "基于PyQt6开发的新闻自动化工具\n"
            "支持新闻采集、分析、生成和发布"
        )
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()