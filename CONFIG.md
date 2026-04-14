# AI 新闻自动化系统 - 配置说明

## 快速开始

### 1. 复制环境变量文件
```bash
cp .env.example .env
```

### 2. 编辑 .env 文件
根据实际情况修改以下配置：

#### LLM 配置
- `LLM_PROVIDER`: 选择 `ollama`（本地）或 `openai`（云端）
- 如果使用 Ollama，确保本地运行 `ollama run qwen2:7b`
- 如果使用 OpenAI，设置 `OPENAI_API_KEY`

#### 图片生成 API
- `IMAGE_API_KEY`: 填写你的图片生成 API Key（可选）
- 推荐使用 SiliconFlow 的免费 API

#### 网站后台登录
- `WEBSITE_ADMIN_USER`: 你的网站后台用户名
- `WEBSITE_ADMIN_PASS`: 你的网站后台密码

### 3. 安装依赖
```bash
pip install -r requirements.txt
playwright install
```

### 4. 启动系统
```bash
# 启动 Web 管理后台
python main.py web --port 8080

# 命令行模式
python main.py run --industry "科技" --topic "人工智能" --count 10
```

## 配置说明

### LLM 提供商选择

**Ollama（推荐，免费）**
- 优点：本地运行，免费，隐私性好
- 缺点：需要本地有足够算力
- 安装：https://ollama.ai

**OpenAI 兼容 API**
- 优点：模型质量高，稳定
- 缺点：需要 API Key，按量收费
- 支持：OpenAI、SiliconFlow、Moonshot 等

### 图片生成

**本地 Stable Diffusion**
- 需要在 `image_generator.py` 中设置 `method="local"`
- 需要运行 SD WebUI: `./webui.sh --api`

**云端 API**
- SiliconFlow: 免费额度，支持 SDXL
- Stability AI: 付费，质量高

## 常见问题

### Q: LLM 调用失败？
A: 检查 Ollama 是否运行：`ollama list`

### Q: 浏览器采集失败？
A: 确保已安装 Playwright: `playwright install`

### Q: 图片无法生成？
A: 检查 `IMAGE_API_KEY` 是否正确配置
