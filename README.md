# AutoUniversityStudy

## 版权声明

遵循GPL v3.0协议, 禁止将此脚本封装或直接出售, 请使用者自行承担使用该脚本的风险, 遵照当地的法律法规, 作者不承担任何责任

## 目录结构

如果新增新的平台脚本, 请按照如下结构部署,方便后续维护

```
AutoUniversityStudy/
|-- AutoBat/ # bat一键启动脚本
|   |-- BeginQingMYZ.bat # 特定平台的bat启动脚本
|   |-- CombineQuestionCSV.bat # 合并题库
|   |-- ...bat # 其他bat脚本
|
|-- AutoUniversityStudy/ # 主体部分
|   |-- QingMa/ # 特定平台的前后端处理文件
|   |   |-- BackendProcessing/ # 后端处理文件(主要是获取答案)
|   |   |   |-- ...py
|   |   |
|   |   |-- FrontendProcessing/ # 前端处理文件(主要是模拟点击及校验)
|   |   |   |-- ...py
|   |
|   |-- .../ # 等等其他平台
|
|-- ChromeWithDriver/ # 内置Chrome浏览器及对应版本驱动, 不展开细说
|
|-- Data/ # 数据文件(该文件夹内均为敏感信息, 请不要git上传)
|   |-- API_key/ # 存放需要调用的API密钥
|   |   |-- Gemini/ # 分平台存储
|   |   |   |-- ...csv # 数据格式待定
|   |   |
|   |   |-- .../ # 其他平台
|   |
|   |-- Quetion_data/ # 存放题库文件
|   |   |-- QingMYZ/ # 分平台存储
|   |   |   |-- ...csv # 数据格式待定
|   |   |
|   |   |-- .../ # 其他平台
|   |
|   |-- User/ # 存放用户登入密钥及配置信息等, 便于多用户使用
|   |   |-- QingMYZ/ # 分平台存储
|   |   |   |-- ...json
|   |   |
|   |   |-- .../ # 其他平台
|
|-- Main_Scr/ # 启动脚本
|   |-- QingMYZmultiUser.py # 多用户使用脚本
|   |-- CombineQuestionCSV.py # 合并题库
|
|-- Python3118/ # 内置Python3.11.8版本, 不展开细说
|-- README.md
|-- TODO.md
```