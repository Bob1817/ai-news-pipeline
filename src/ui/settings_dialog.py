from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QLineEdit, QSpinBox, QCheckBox,
    QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("系统设置")
        self.resize(500, 400)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        llm_group = QGroupBox("LLM配置")
        self.layout.addWidget(llm_group)
        
        llm_layout = QFormLayout(llm_group)
        
        self.llm_provider_combo = QComboBox()
        self.llm_provider_combo.addItems(["ollama", "openai"])
        llm_layout.addRow("提供商:", self.llm_provider_combo)
        
        self.model_edit = QLineEdit()
        llm_layout.addRow("模型名称:", self.model_edit)
        
        self.api_url_edit = QLineEdit()
        llm_layout.addRow("API地址:", self.api_url_edit)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        llm_layout.addRow("API密钥:", self.api_key_edit)
        
        article_group = QGroupBox("文章设置")
        self.layout.addWidget(article_group)
        
        article_layout = QFormLayout(article_group)
        
        min_words_layout = QHBoxLayout()
        self.min_words_spin = QSpinBox()
        self.min_words_spin.setRange(500, 2000)
        self.min_words_spin.setValue(800)
        min_words_layout.addWidget(self.min_words_spin)
        min_words_layout.addWidget(QPushButton("字"))
        article_layout.addRow("最小字数:", min_words_layout)
        
        max_words_layout = QHBoxLayout()
        self.max_words_spin = QSpinBox()
        self.max_words_spin.setRange(500, 3000)
        self.max_words_spin.setValue(1500)
        max_words_layout.addWidget(self.max_words_spin)
        max_words_layout.addWidget(QPushButton("字"))
        article_layout.addRow("最大字数:", max_words_layout)
        
        self.auto_image_check = QCheckBox("自动生成配图")
        article_layout.addRow("", self.auto_image_check)
        
        publish_group = QGroupBox("发布设置")
        self.layout.addWidget(publish_group)
        
        publish_layout = QFormLayout(publish_group)
        
        self.require_review_check = QCheckBox("发布前需要审核")
        publish_layout.addRow("", self.require_review_check)
        
        interval_layout = QHBoxLayout()
        self.publish_interval_spin = QSpinBox()
        self.publish_interval_spin.setRange(5, 60)
        self.publish_interval_spin.setValue(10)
        interval_layout.addWidget(self.publish_interval_spin)
        interval_layout.addWidget(QPushButton("秒"))
        publish_layout.addRow("发布间隔:", interval_layout)
        
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_btn)
        
        self.layout.addLayout(button_layout)
    
    def load_settings(self):
        if not self.config_manager:
            return
        
        provider = self.config_manager.get_setting('llm.provider', 'ollama')
        self.llm_provider_combo.setCurrentText(provider)
        
        model = self.config_manager.get_setting('llm.model', '')
        self.model_edit.setText(model)
        
        api_url = self.config_manager.get_setting('llm.api_url', '')
        self.api_url_edit.setText(api_url)
        
        api_key = self.config_manager.get_env_var('LLM_API_KEY', '')
        self.api_key_edit.setText(api_key)
        
        min_words = self.config_manager.get_setting('generator.article_min_words', 800)
        self.min_words_spin.setValue(min_words)
        
        max_words = self.config_manager.get_setting('generator.article_max_words', 1500)
        self.max_words_spin.setValue(max_words)
        
        auto_image = self.config_manager.get_setting('generator.auto_generate_image', True)
        self.auto_image_check.setChecked(auto_image)
        
        require_review = self.config_manager.get_setting('distributor.require_review', True)
        self.require_review_check.setChecked(require_review)
        
        interval = self.config_manager.get_setting('distributor.publish_interval', 10)
        self.publish_interval_spin.setValue(interval)
    
    def save_settings(self):
        if not self.config_manager:
            QMessageBox.warning(self, "错误", "配置管理器未初始化")
            return
        
        try:
            self.config_manager.set_setting('llm.provider', self.llm_provider_combo.currentText())
            self.config_manager.set_setting('llm.model', self.model_edit.text())
            self.config_manager.set_setting('llm.api_url', self.api_url_edit.text())
            self.config_manager.set_setting('generator.article_min_words', self.min_words_spin.value())
            self.config_manager.set_setting('generator.article_max_words', self.max_words_spin.value())
            self.config_manager.set_setting('generator.auto_generate_image', self.auto_image_check.isChecked())
            self.config_manager.set_setting('distributor.require_review', self.require_review_check.isChecked())
            self.config_manager.set_setting('distributor.publish_interval', self.publish_interval_spin.value())
            
            self.config_manager.save_settings(self.config_manager.settings)
            
            import os
            env_file = self.config_manager.get_env_var('ENV_FILE', '.env')
            if self.api_key_edit.text():
                with open(env_file, 'a') as f:
                    f.write(f"\nLLM_API_KEY={self.api_key_edit.text()}")
            
            QMessageBox.information(self, "成功", "设置已保存")
            self.close()
        except Exception as e:
            QMessageBox.error(self, "错误", f"保存失败: {str(e)}")