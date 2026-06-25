# AI API 配置加载模块
import tomllib

from os.path import abspath, dirname, exists, join

# 当前所在绝对路径
current_dir = dirname(abspath(__file__))
# 返回上一级目录(GetAnswerProcessing/ -> AutoQMYZ/ -> 项目根目录)
current_dir = dirname(current_dir)
current_dir = dirname(current_dir)

# 配置文件路径
AI_CONFIG_PATH = join(current_dir, 'config.toml')

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
        'base_url': ai_config.get('base_url', 'https://api.openai.com/v1'),
        'model': ai_config.get('model', 'gpt-4o-mini'),
    }
