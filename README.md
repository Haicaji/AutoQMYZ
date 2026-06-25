# AutoQMYZ

青马易站自动答题脚本

## 版权声明

遵循 AGPL v3.0 协议

## 目录结构

```
AutoQMYZ/
|-- AutoBat/                    # bat一键启动脚本
|   |-- BeginQingMYZ.bat        # 启动答题脚本
|   |-- CombineQuestionCSV.bat  # 合并题库
|   |-- CreatQingMYZUsersJson.bat # 创建用户配置
|   |-- BatchModifyUserJson.bat # 批量修改用户配置
|   |-- pipEnv.bat              # 安装依赖
|
|-- AutoQMYZ/                   # 核心答题模块
|   |-- QingMYZMain.py          # 主类 QingMYZClass
|   |-- GetAnswerProcessing/    # 获取答案模块
|   |   |-- GetAnswer.py        # 本地题库/Gemini/人工 获取答案
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
|
|-- Data/                       # 数据文件(该文件夹内均为敏感信息, 请不要git上传)
|   |-- logs/                   # 运行日志目录(按天轮转)
|   |
|   |-- Question_data/          # 存放题库文件
|   |   |-- 课程名称.csv        # 按课程（题类）命名的题库文件
|   |
|   |-- User/                   # 存放用户登入密钥及配置信息
|   |   |-- finish/             # 全部完成的用户自动移入该目录
|   |   |   |-- ...json
|   |   |-- ...json
|
|-- Main_Scr/                   # 启动脚本
|   |-- QingMYZmultiUser.py     # 多用户答题
|   |-- CreatQingMYZUsersJson.py # 创建用户配置
|   |-- BatchModifyUserJson.py  # 批量修改用户配置
|   |-- CombineQuestionCSV.py   # 合并题库
|
|-- Python3118/                 # 内置Python3.11.8版本
|-- config.toml                 # 全局配置文件（敏感信息，请勿git上传）
|-- README.md
|-- TODO.md
```

## 使用说明

### 1. 安装依赖

双击 `AutoBat/pipEnv.bat` 安装所需 Python 依赖

### 2. 配置全局参数与 AI API

编辑根目录下的 `config.toml`，填入你的 API 密钥和模型信息。支持 OpenAI 兼容的各大 AI API（OpenAI、DeepSeek、通义千问、Gemini 等）：

```toml
[ai]
api_key = "你的API密钥"
base_url = "https://api.openai.com/v1"   # 可替换为其他兼容 API 地址
model = "gpt-4o-mini"                    # 使用的模型名称
```

### 3. 创建用户配置

双击 `AutoBat/CreatQingMYZUsersJson.bat` 按提示创建用户 JSON 配置文件

### 4. 开始答题

双击 `AutoBat/BeginQingMYZ.bat` 启动自动答题