# 贡献指南

欢迎为本项目做出贡献！本指南将帮助你了解如何参与项目。

## 如何贡献

### 报告问题

如果您发现问题或有任何建议，请创建 Issue。在报告问题时，请提供：

- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（操作系统、Python 版本等）

### 提交代码

1. Fork 仓库
2. 创建新分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add some feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 提交 Pull Request

### 代码风格

- Python 代码遵循 PEP 8 规范
- 使用类型注解
- 添加必要的注释
- 保持代码简洁

## 开发环境设置

### Python 后端

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### WinUI 客户端

```bash
# 在 Windows 系统上
cd WinUI/AINewsPipeline.WinUI

# 还原 NuGet 包
dotnet restore

# 构建项目
dotnet build

# 运行项目
dotnet run
```

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov=src --cov-report=html
```

## 构建发布版本

### Python 后端

使用 PyInstaller 打包：

```bash
pip install pyinstaller
pyinstaller main.spec
```

### WinUI 客户端

```bash
cd WinUI/AINewsPipeline.WinUI
dotnet publish -c Release -r win-x64 --self-contained true -o bin/win-x64
```

## 许可证

通过提交代码，您同意您的贡献采用项目的 MIT 许可证。
