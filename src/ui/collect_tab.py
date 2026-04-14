from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QLineEdit, QSpinBox, QPushButton,
    QProgressBar, QTableWidget, QTableWidgetItem,
    QLabel, QGroupBox
)
from PyQt6.QtCore import Qt

class CollectTab(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = None
        self.task_manager = None
        self.setup_ui()
    
    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        config_group = QGroupBox("采集配置")
        self.layout.addWidget(config_group)
        
        config_layout = QFormLayout(config_group)
        
        self.industry_combo = QComboBox()
        self.industry_combo.addItems(["科技", "财经", "医疗健康", "教育", "体育", "娱乐", "社会", "国际", "人力资源服务"])
        config_layout.addRow("行业:", self.industry_combo)
        
        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("输入主题关键词（可选）")
        config_layout.addRow("主题关键词:", self.topic_edit)
        
        count_layout = QHBoxLayout()
        self.count_spin = QSpinBox()
        self.count_spin.setRange(5, 50)
        self.count_spin.setValue(10)
        count_layout.addWidget(self.count_spin)
        count_layout.addWidget(QLabel("条"))
        config_layout.addRow("采集数量:", count_layout)
        
        theme_layout = QHBoxLayout()
        self.theme_count_spin = QSpinBox()
        self.theme_count_spin.setRange(1, 10)
        self.theme_count_spin.setValue(3)
        theme_layout.addWidget(self.theme_count_spin)
        theme_layout.addWidget(QLabel("个"))
        config_layout.addRow("提炼主题数:", theme_layout)
        
        time_range_layout = QHBoxLayout()
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["6小时", "12小时", "24小时", "48小时"])
        time_range_layout.addWidget(self.time_range_combo)
        config_layout.addRow("时间范围:", time_range_layout)
        
        action_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始采集")
        self.start_btn.clicked.connect(self.on_start_collect)
        action_layout.addWidget(self.start_btn)
        
        self.run_all_btn = QPushButton("执行完整流程")
        self.run_all_btn.clicked.connect(self.on_run_all)
        action_layout.addWidget(self.run_all_btn)
        
        self.layout.addLayout(action_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)
        
        result_group = QGroupBox("采集结果")
        self.layout.addWidget(result_group)
        
        self.news_table = QTableWidget()
        self.news_table.setColumnCount(4)
        self.news_table.setHorizontalHeaderLabels(["标题", "来源", "发布时间", "操作"])
        self.news_table.horizontalHeader().setStretchLastSection(True)
        result_group_layout = QVBoxLayout(result_group)
        result_group_layout.addWidget(self.news_table)
    
    def set_config_manager(self, config_manager):
        self.config_manager = config_manager
        if config_manager:
            industries = config_manager.get_industry_names()
            if industries:
                self.industry_combo.clear()
                self.industry_combo.addItems(industries)
    
    def set_task_manager(self, task_manager):
        self.task_manager = task_manager
    
    def on_start_collect(self):
        if not self.task_manager:
            return
        
        params = {
            'industry': self.industry_combo.currentText(),
            'topic': self.topic_edit.text(),
            'count': self.count_spin.value(),
            'theme_count': self.theme_count_spin.value()
        }
        
        from src.business.pipeline_runner import run_collection_sync
        
        def on_progress(task_id, progress, message):
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)
        
        def on_complete(task_id, task_type, result):
            self.progress_bar.setVisible(False)
            news_list = result.get('news', [])
            self.populate_news_table(news_list)
        
        def on_error(task_id, error):
            self.progress_bar.setVisible(False)
        
        self.task_manager.progress_signal.connect(on_progress)
        self.task_manager.complete_signal.connect(on_complete)
        self.task_manager.error_signal.connect(on_error)
        
        self.task_manager.submit_task('collection', params, run_collection_sync)
    
    def on_run_all(self):
        if not self.task_manager:
            return
        
        params = {
            'industry': self.industry_combo.currentText(),
            'topic': self.topic_edit.text(),
            'count': self.count_spin.value(),
            'theme_count': self.theme_count_spin.value(),
            'platforms': [],
            'auto_publish': False
        }
        
        from src.business.pipeline_runner import run_pipeline_sync
        
        def on_progress(task_id, progress, message):
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)
        
        def on_complete(task_id, task_type, result):
            self.progress_bar.setVisible(False)
        
        def on_error(task_id, error):
            self.progress_bar.setVisible(False)
        
        self.task_manager.progress_signal.connect(on_progress)
        self.task_manager.complete_signal.connect(on_complete)
        self.task_manager.error_signal.connect(on_error)
        
        self.task_manager.submit_task('pipeline', params, run_pipeline_sync)
    
    def populate_news_table(self, news_list):
        self.news_table.setRowCount(len(news_list))
        
        for row, news in enumerate(news_list):
            title_item = QTableWidgetItem(news.get('title', ''))
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.news_table.setItem(row, 0, title_item)
            
            source_item = QTableWidgetItem(news.get('source', ''))
            source_item.setFlags(source_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.news_table.setItem(row, 1, source_item)
            
            time_item = QTableWidgetItem(str(news.get('publish_time', '')))
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.news_table.setItem(row, 2, time_item)
            
            view_btn = QPushButton("查看")
            view_btn.clicked.connect(lambda _, n=news: self.view_news(n))
            self.news_table.setCellWidget(row, 3, view_btn)
        
        self.news_table.resizeColumnsToContents()
    
    def view_news(self, news):
        from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout
        
        dialog = QDialog()
        dialog.setWindowTitle(news.get('title', '新闻详情'))
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        title_label = QLabel(f"<b>{news.get('title', '')}</b>")
        title_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(title_label)
        
        info_label = QLabel(f"来源: {news.get('source', '')} | 时间: {news.get('publish_time', '')}")
        layout.addWidget(info_label)
        
        url_label = QLabel(f"<a href='{news.get('url', '')}'>{news.get('url', '')}</a>")
        url_label.setOpenExternalLinks(True)
        layout.addWidget(url_label)
        
        summary_text = QTextEdit()
        summary_text.setPlainText(news.get('summary', ''))
        summary_text.setReadOnly(True)
        layout.addWidget(summary_text)
        
        dialog.exec()