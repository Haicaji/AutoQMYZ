import os
from fake_useragent import UserAgent
from AutoQMYZ import get_project_root


def apply_stealth_script(driver, project_root=None):
    script_path = os.path.join(project_root or get_project_root(), "ChromeWithDriver", "stealth.min.js")
    if not os.path.exists(script_path):
        print(f"反检测脚本不存在: {script_path}")
        return False

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            stealth_script = f.read()
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": stealth_script}
        )
        return True
    except Exception as e:
        print(f"注入反检测脚本失败: {e}")
        return False

# 判断是否为刷题检测题
def detect_error(question):
    if '刷题' in question[0] or '刷题' in question[1]:
        print('\n\n出现防刷题题目\n\n')
        return True
    
# 随机生成UA
def get_ua():
    user_agent = UserAgent()
    ua =  user_agent.random

    return ua

if __name__ == '__main__':
    print(get_ua())
