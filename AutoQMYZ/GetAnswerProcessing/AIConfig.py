# AI API 配置加载模块
import tomllib

from os.path import exists, join
from AutoQMYZ import get_project_root

# 配置文件路径
AI_CONFIG_PATH = join(get_project_root(), 'config.toml')

def load_ai_config():
    """
    加载 AI API 配置文件。

    返回：
    dict: 包含 'api_key', 'base_url', 'model' 的字典。
    如果配置文件不存在或 api_key 为空，返回 None。
    """
    if not exists(AI_CONFIG_PATH):
        print(f'AI 配置文件不存在: {AI_CONFIG_PATH}')
        return None
    
    with open(AI_CONFIG_PATH, 'rb') as f:
        config = tomllib.load(f)
    
    ai_config = config.get('ai', {})

    if not ai_config.get('api_key'):
        print('AI 配置文件中未设置 api_key')
        return None
    
    return {
        'api_key': ai_config['api_key'],
        'base_url': ai_config.get('base_url', 'https://api.deepseek.com'),
        'model': ai_config.get('model', 'deepseek-v4-flash'),
    }

def load_answer_config():
    """
    加载答题优先级和超时配置。
    """
    if not exists(AI_CONFIG_PATH):
        return {
            "answer_priority": ["db", "ai", "manual", "random"],
            "manual_timeout": 30.0
        }
    
    try:
        with open(AI_CONFIG_PATH, 'rb') as f:
            config = tomllib.load(f)
        
        answer_config = config.get('answer', {})
        return {
            "answer_priority": answer_config.get("answer_priority", ["db", "ai", "manual", "random"]),
            "manual_timeout": float(answer_config.get("manual_timeout", 30))
        }
    except Exception as e:
        print(f"加载答题优先级配置失败: {e}")
        return {
            "answer_priority": ["db", "ai", "manual", "random"],
            "manual_timeout": 30.0
        }
