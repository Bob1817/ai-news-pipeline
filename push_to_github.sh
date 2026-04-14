#!/bin/bash

# AI新闻自动化系统 - GitHub 推送脚本

echo "=============================================="
echo "AI新闻自动化系统 - GitHub 推送脚本"
echo "=============================================="
echo ""

# 检查是否已设置远程仓库
REMOTE_URL=$(git config --get remote.origin.url)

if [ -z "$REMOTE_URL" ]; then
    echo "请输入您的 GitHub 仓库 URL:"
    read -p "例如: https://github.com/your-username/ai-news-pipeline.git: " GITHUB_URL
    
    if [ -z "$GITHUB_URL" ]; then
        echo "错误: 仓库 URL 不能为空"
        exit 1
    fi
    
    # 添加远程仓库
    git remote add origin "$GITHUB_URL"
    echo "已添加远程仓库: $GITHUB_URL"
else
    echo "已配置远程仓库: $REMOTE_URL"
    echo "是否更新远程仓库URL? (y/N)"
    read UPDATE_REMOTE
    if [ "$UPDATE_REMOTE" = "y" ] || [ "$UPDATE_REMOTE" = "Y" ]; then
        echo "请输入新的 GitHub 仓库 URL:"
        read -p "例如: https://github.com/your-username/ai-news-pipeline.git: " GITHUB_URL
        git remote set-url origin "$GITHUB_URL"
        echo "已更新远程仓库: $GITHUB_URL"
    fi
fi

echo ""
echo "开始推送代码到 GitHub..."
echo ""

# 推送代码
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "=============================================="
    echo "推送成功!"
    echo "=============================================="
    echo ""
    echo "下一步操作:"
    echo "1. 登录 GitHub 查看您的仓库"
    echo "2. 进入 Actions 页面"
    echo "3. 等待 GitHub Actions 自动构建"
    echo "4. 构建完成后，从 Releases 页面下载安装包"
    echo ""
    echo "GitHub Actions 会自动:"
    echo "- 构建 WinUI 应用"
    echo "- 打包成 ZIP 文件"
    echo "- 创建 Release 并上传安装包"
    echo ""
else
    echo ""
    echo "=============================================="
    echo "推送失败!"
    echo "=============================================="
    echo ""
    echo "可能的原因:"
    echo "1. GitHub 仓库 URL 不正确"
    echo "2. 没有正确的访问权限"
    echo "3. 网络问题"
    echo ""
    echo "请检查并重新运行脚本"
    exit 1
fi