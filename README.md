# AutoQMYZ

青马易战自动答题脚本

## 版权声明

遵循 AGPL v3.0 协议

## 快速开始（Release 版本）

> 推荐大多数用户使用此方式，无需安装 Python 环境。

### 1. 下载

前往 [Releases](../../releases) 页面，下载最新版本的 `AutoQMYZ-vX.X.X.zip`。

### 2. 解压

将 zip 文件解压到任意目录（路径中**不要包含中文或空格**）。

### 3. 配置 AI API

编辑根目录下的 `config.toml`，填入你的 API 密钥和模型信息。支持 OpenAI 兼容的各大 AI API（OpenAI、DeepSeek、通义千问、Gemini 等）：

```toml
[ai]
api_key = "你的API密钥"
base_url = "https://api.openai.com/v1"   # 可替换为其他兼容 API 地址
model = "gpt-4o-mini"                    # 使用的模型名称
```

### 4. 启动程序

双击 `AutoQMYZ.exe` 启动程序。

### 5. 打开管理界面

启动成功后，在浏览器中打开 [http://127.0.0.1:8000](http://127.0.0.1:8000) 即可进入 WebUI 管理界面。

在管理界面中你可以：
- 创建和管理用户
- 配置答题任务（选择课程、设置题数、正确率等）
- 启动/停止答题队列
- 实时查看答题日志
- 修改系统设置

## 目录结构

```
AutoQMYZ/
|-- AutoQMYZ.exe                # 主程序（Release 版本）
|-- AutoQMYZ.py                 # 主程序源码（开发版本）
|
|-- AutoQMYZ/                   # 核心答题模块
|   |-- QingMYZMain.py          # 主类 QingMYZClass
|   |-- GetAnswerProcessing/    # 获取答案模块
|   |   |-- GetAnswer.py        # 本地题库/AI/人工 获取答案
|   |
|   |-- ImitateProcessing/      # 模拟浏览器操作模块
|   |   |-- Login.py            # 登入
|   |   |-- SubmitAnswer.py     # 提交答案
|   |   |-- GetQuestion.py      # 获取题目
|   |   |-- AfterAnswer.py      # 答题后操作(写入题库)
|   |   |-- IntoAnswerWeb.py    # 进入答题页面
|   |   |-- AntiRobotDetection.py # 防刷题检测
|   |   |-- StandardQuestion.py # 题目标准化
|
|-- ChromeWithDriver/           # 内置Chrome浏览器及对应版本驱动
|   |-- stealth.min.js          # 反爬虫检测脚本
|
|-- Data/                       # 数据文件
|   |-- logs/                   # 运行日志目录(按天轮转)
|   |-- Question_data/          # 存放题库文件
|   |   |-- 课程名称.csv        # 按课程命名的题库文件
|   |-- User/                   # 存放用户登入密钥及配置信息
|
|-- WebUI/                      # Web管理界面
|   |-- dist/                   # 编译后的前端静态文件
|
|-- config.toml                 # 全局配置文件
|-- README.md
```

## 开发者指南

如果你希望从源码运行或参与开发：

### 环境要求

- Python 3.12+
- Node.js 18+

### 安装依赖

```bash
# Python 依赖
pip install -r requirements.txt

# 前端依赖（如需修改 WebUI）
cd WebUI
npm install
npm run build
```

### 运行

```bash
python AutoQMYZ.py
```

### 发布新版本

推送一个以 `v` 开头的 tag 即可自动触发 GitHub Actions 构建并发布 Release：

```bash
git tag v1.0.0
git push origin v1.0.0
```

也可以在 GitHub Actions 页面手动触发 **Build and Release** workflow，输入版本号即可自动创建 tag 并发布。