from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QCheckBox,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import json

class PublishTab(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = None
        self.setup_ui()
        self.load_articles()
    
    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        platform_group = QGroupBox("发布平台")
        self.layout.addWidget(platform_group)
        
        platform_layout = QHBoxLayout(platform_group)
        
        self.website_check = QCheckBox("自有官网")
        self.website_check.setChecked(True)
        platform_layout.addWidget(self.website_check)
        
        self.wechat_check = QCheckBox("微信公众号")
        platform_layout.addWidget(self.wechat_check)
        
        article_group = QGroupBox("待发布文章")
        self.layout.addWidget(article_group)
        
        article_layout = QVBoxLayout(article_group)
        
        self.article_table = QTableWidget()
        self.article_table.setColumnCount(5)
        self.article_table.setHorizontalHeaderLabels(["选择", "标题", "关键词", "配图", "状态"])
        self.article_table.horizontalHeader().setStretchLastSection(True)
        article_layout.addWidget(self.article_table)
        
        action_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.load_articles)
        action_layout.addWidget(self.refresh_btn)
        
        self.publish_btn = QPushButton("批量发布选中")
        self.publish_btn.clicked.connect(self.batch_publish)
        action_layout.addWidget(self.publish_btn)
        
        self.layout.addLayout(action_layout)
        
        history_group = QGroupBox("发布历史")
        self.layout.addWidget(history_group)
        
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["文章标题", "平台", "状态", "发布时间"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        history_layout.addWidget(self.history_table)
        
        self.load_history()
    
    def set_config_manager(self, config_manager):
        self.config_manager = config_manager
        if config_manager:
            self.website_check.setEnabled(config_manager.get_platform_enabled('website'))
            self.wechat_check.setEnabled(config_manager.get_platform_enabled('wechat'))
    
    def load_articles(self):
        from src.utils.db import get_session, GeneratedArticle
        
        session = get_session()
        articles = session.query(GeneratedArticle).filter(
            GeneratedArticle.status == 'draft'
        ).order_by(GeneratedArticle.created_at.desc()).all()
        
        self.article_table.setRowCount(len(articles))
        
        for row, article in enumerate(articles):
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.article_table.setCellWidget(row, 0, checkbox)
            
            title_item = QTableWidgetItem(article.title[:50] + "..." if len(article.title) > 50 else article.title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.article_table.setItem(row, 1, title_item)
            
            try:
                keywords = json.loads(article.keywords)
                keywords_text = ", ".join(keywords[:3])
            except:
                keywords_text = ""
            keywords_item = QTableWidgetItem(keywords_text)
            keywords_item.setFlags(keywords_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.article_table.setItem(row, 2, keywords_item)
            
            has_image = article.image_path and article.image_path != ''
            image_item = QTableWidgetItem("有" if has_image else "无")
            image_item.setFlags(image_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            image_item.setForeground(Qt.GlobalColor.green if has_image else Qt.GlobalColor.gray)
            self.article_table.setItem(row, 3, image_item)
            
            status_item = QTableWidgetItem("待发布")
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            status_item.setForeground(QColor(255, 165, 0))
            self.article_table.setItem(row, 4, status_item)
        
        self.article_table.resizeColumnsToContents()
    
    def load_history(self):
        from src.utils.db import get_session, PublishRecord, GeneratedArticle
        
        session = get_session()
        records = session.query(PublishRecord).order_by(PublishRecord.published_at.desc()).limit(20).all()
        
        self.history_table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            article = session.query(GeneratedArticle).get(record.article_id)
            title = article.title[:30] + "..." if article and len(article.title) > 30 else (article.title if article else "未知")
            
            title_item = QTableWidgetItem(title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 0, title_item)
            
            platform_item = QTableWidgetItem(record.platform)
            platform_item.setFlags(platform_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 1, platform_item)
            
            status_item = QTableWidgetItem(record.status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if record.status == 'success':
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.red)
            self.history_table.setItem(row, 2, status_item)
            
            time_item = QTableWidgetItem(str(record.published_at))
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 3, time_item)
        
        self.history_table.resizeColumnsToContents()
    
    def batch_publish(self):
        selected_platforms = []
        if self.website_check.isChecked():
            selected_platforms.append('website')
        if self.wechat_check.isChecked():
            selected_platforms.append('wechat')
        
        if not selected_platforms:
            QMessageBox.warning(self, "提示", "请选择至少一个发布平台")
            return
        
        selected_articles = []
        for row in range(self.article_table.rowCount()):
            checkbox = self.article_table.cellWidget(row, 0)
            if checkbox.isChecked():
                title = self.article_table.item(row, 1).text()
                from src.utils.db import get_session, GeneratedArticle
                session = get_session()
                article = session.query(GeneratedArticle).filter(
                    GeneratedArticle.title.like(f"%{title[:20]}%")
                ).first()
                if article:
                    selected_articles.append(article)
        
        if not selected_articles:
            QMessageBox.warning(self, "提示", "请选择至少一篇文章")
            return
        
        reply = QMessageBox.question(
            self,
            "确认发布",
            f"确定要发布 {len(selected_articles)} 篇文章到 {', '.join(selected_platforms)} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from src.distributor.distributor import Distributor
            
            distributor = Distributor()
            articles_data = []
            
            for article in selected_articles:
                articles_data.append({
                    'title': article.title,
                    'content': article.content,
                    'keywords': article.keywords,
                    'image_path': article.image_path
                })
            
            import asyncio
            result = asyncio.run(distributor.batch_distribute(articles_data, selected_platforms))
            
            success_count = result.get('success', 0)
            total_count = result.get('total_articles', 0) * result.get('total_platforms', 1)
            
            if success_count == total_count:
                for article in selected_articles:
                    article.status = 'published'
                
                from src.utils.db import get_session
                session = get_session()
                session.commit()
                
                QMessageBox.information(self, "成功", f"全部 {success_count} 篇文章发布成功")
            else:
                QMessageBox.warning(self, "部分成功", f"发布 {success_count}/{total_count} 篇文章成功")
            
            self.load_articles()
            self.load_history()