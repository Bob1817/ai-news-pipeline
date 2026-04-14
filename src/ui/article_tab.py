from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QTextEdit,
    QLabel, QPushButton, QGroupBox, QMessageBox,
    QDialog, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
from pathlib import Path
import json

class ArticleTab(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = None
        self.selected_article = None
        self.setup_ui()
        self.load_articles()
    
    def setup_ui(self):
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        article_group = QGroupBox("文章列表")
        left_layout.addWidget(article_group)
        
        article_layout = QVBoxLayout(article_group)
        
        self.article_table = QTableWidget()
        self.article_table.setColumnCount(4)
        self.article_table.setHorizontalHeaderLabels(["标题", "状态", "字数", "操作"])
        self.article_table.horizontalHeader().setStretchLastSection(True)
        self.article_table.itemSelectionChanged.connect(self.on_article_select)
        article_layout.addWidget(self.article_table)
        
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_articles)
        button_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("导出选中")
        self.export_btn.clicked.connect(self.export_article)
        button_layout.addWidget(self.export_btn)
        
        self.delete_btn = QPushButton("删除选中")
        self.delete_btn.clicked.connect(self.delete_article)
        button_layout.addWidget(self.delete_btn)
        
        left_layout.addLayout(button_layout)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        detail_group = QGroupBox("文章详情")
        right_layout.addWidget(detail_group)
        
        detail_layout = QVBoxLayout(detail_group)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        detail_layout.addWidget(self.title_label)
        
        keywords_layout = QHBoxLayout()
        keywords_label = QLabel("关键词: ")
        self.keywords_display = QLabel()
        keywords_layout.addWidget(keywords_label)
        keywords_layout.addWidget(self.keywords_display)
        detail_layout.addLayout(keywords_layout)
        
        summary_layout = QHBoxLayout()
        summary_label = QLabel("摘要: ")
        self.summary_display = QLabel()
        self.summary_display.setWordWrap(True)
        summary_layout.addWidget(summary_label)
        summary_layout.addWidget(self.summary_display)
        detail_layout.addLayout(summary_layout)
        
        image_layout = QHBoxLayout()
        image_label = QLabel("配图: ")
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 150)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(image_label)
        image_layout.addWidget(self.image_label)
        detail_layout.addLayout(image_layout)
        
        content_label = QLabel("内容:")
        detail_layout.addWidget(content_label)
        
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        detail_layout.addWidget(self.content_text)
        
        edit_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self.edit_article)
        edit_layout.addWidget(self.edit_btn)
        
        self.preview_btn = QPushButton("预览")
        self.preview_btn.clicked.connect(self.preview_article)
        edit_layout.addWidget(self.preview_btn)
        
        detail_layout.addLayout(edit_layout)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([300, 700])
        
        self.layout.addWidget(self.splitter)
    
    def set_config_manager(self, config_manager):
        self.config_manager = config_manager
    
    def load_articles(self):
        from src.utils.db import get_session, GeneratedArticle
        
        session = get_session()
        articles = session.query(GeneratedArticle).order_by(GeneratedArticle.created_at.desc()).all()
        
        self.article_table.setRowCount(len(articles))
        
        for row, article in enumerate(articles):
            title_item = QTableWidgetItem(article.title[:50] + "..." if len(article.title) > 50 else article.title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.article_table.setItem(row, 0, title_item)
            
            status_item = QTableWidgetItem(article.status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if article.status == 'published':
                status_item.setForeground(Qt.GlobalColor.green)
            self.article_table.setItem(row, 1, status_item)
            
            word_count = len(article.content)
            word_item = QTableWidgetItem(str(word_count))
            word_item.setFlags(word_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.article_table.setItem(row, 2, word_item)
            
            publish_btn = QPushButton("发布")
            publish_btn.clicked.connect(lambda _, a=article: self.publish_article(a))
            self.article_table.setCellWidget(row, 3, publish_btn)
        
        self.article_table.resizeColumnsToContents()
    
    def on_article_select(self):
        selected = self.article_table.selectedItems()
        if selected:
            row = selected[0].row()
            title = self.article_table.item(row, 0).text()
            
            from src.utils.db import get_session, GeneratedArticle
            
            session = get_session()
            article = session.query(GeneratedArticle).filter(GeneratedArticle.title.like(f"%{title[:20]}%")).first()
            
            if article:
                self.selected_article = article
                self.display_article(article)
    
    def display_article(self, article):
        self.title_label.setText(article.title)
        
        try:
            keywords = json.loads(article.keywords)
            self.keywords_display.setText(", ".join(keywords[:5]))
        except:
            self.keywords_display.setText("")
        
        self.summary_display.setText(article.summary[:100] + "..." if len(article.summary) > 100 else article.summary)
        
        if article.image_path and Path(article.image_path).exists():
            pixmap = QPixmap(article.image_path)
            pixmap = pixmap.scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.clear()
            self.image_label.setText("无配图")
        
        self.content_text.setPlainText(article.content)
    
    def edit_article(self):
        if not self.selected_article:
            QMessageBox.warning(self, "提示", "请先选择一篇文章")
            return
        
        dialog = QDialog()
        dialog.setWindowTitle("编辑文章")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        title_edit = QLineEdit(self.selected_article.title)
        layout.addWidget(QLabel("标题:"))
        layout.addWidget(title_edit)
        
        content_edit = QTextEdit(self.selected_article.content)
        layout.addWidget(QLabel("内容:"))
        layout.addWidget(content_edit)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        def save():
            from src.utils.db import get_session
            
            session = get_session()
            article = session.query(type(self.selected_article)).get(self.selected_article.id)
            article.title = title_edit.text()
            article.content = content_edit.toPlainText()
            session.commit()
            
            QMessageBox.information(self, "成功", "文章已保存")
            dialog.close()
            self.load_articles()
        
        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.close)
        
        dialog.exec()
    
    def preview_article(self):
        if not self.selected_article:
            QMessageBox.warning(self, "提示", "请先选择一篇文章")
            return
        
        dialog = QDialog()
        dialog.setWindowTitle("文章预览")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        title_label = QLabel(f"<h1>{self.selected_article.title}</h1>")
        layout.addWidget(title_label)
        
        keywords_label = QLabel(f"<b>关键词:</b> {self.selected_article.keywords}")
        layout.addWidget(keywords_label)
        
        content_text = QTextEdit()
        content_text.setPlainText(self.selected_article.content)
        content_text.setReadOnly(True)
        layout.addWidget(content_text)
        
        dialog.exec()
    
    def export_article(self):
        selected = self.article_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择文章")
            return
        
        from src.utils.exporter import export_articles
        
        row = selected[0].row()
        title = self.article_table.item(row, 0).text()
        
        from src.utils.db import get_session, GeneratedArticle
        
        session = get_session()
        article = session.query(GeneratedArticle).filter(GeneratedArticle.title.like(f"%{title[:20]}%")).first()
        
        if article:
            export_articles([article])
            QMessageBox.information(self, "成功", "文章已导出")
    
    def delete_article(self):
        selected = self.article_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择文章")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除选中的文章吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            row = selected[0].row()
            title = self.article_table.item(row, 0).text()
            
            from src.utils.db import get_session, GeneratedArticle
            
            session = get_session()
            article = session.query(GeneratedArticle).filter(GeneratedArticle.title.like(f"%{title[:20]}%")).first()
            
            if article:
                session.delete(article)
                session.commit()
                QMessageBox.information(self, "成功", "文章已删除")
                self.load_articles()
    
    def publish_article(self, article):
        from src.distributor.distributor import Distributor
        
        distributor = Distributor()
        article_data = {
            'title': article.title,
            'content': article.content,
            'keywords': article.keywords,
            'image_path': article.image_path
        }
        
        import asyncio
        result = asyncio.run(distributor.distribute(article_data, ['website']))
        
        if result[0].get('success'):
            article.status = 'published'
            from src.utils.db import get_session
            session = get_session()
            session.commit()
            QMessageBox.information(self, "成功", "文章发布成功")
            self.load_articles()
        else:
            QMessageBox.error(self, "失败", result[0].get('error', '发布失败'))