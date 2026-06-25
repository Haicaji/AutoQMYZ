import os
import sys
import json
import logging
import threading
import time
from datetime import datetime
from glob import glob
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import toml

# Resolve path references — support both normal Python and PyInstaller frozen exe
if getattr(sys, 'frozen', False):
    # Running as compiled exe: use the directory containing the exe
    project_root = os.path.dirname(sys.executable)
else:
    project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Set up logging and add custom handler for streaming individual task logs
from AutoQMYZ.Logger import setup_logging
setup_logging()

class TaskLogHandler(logging.Handler):
    def __init__(self, task_logs_dir):
        super().__init__()
        self.task_logs_dir = task_logs_dir
        os.makedirs(task_logs_dir, exist_ok=True)
        
    def emit(self, record):
        thread_name = threading.current_thread().name
        if thread_name.startswith("task_"):
            task_id = thread_name[5:]
            log_file = os.path.join(self.task_logs_dir, f"{task_id}.log")
            log_entry = self.format(record) + "\n"
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry)
            except Exception:
                pass

# Register the task log handler
root_logger = logging.getLogger()
task_logs_dir = os.path.join(project_root, 'Data', 'logs', 'tasks')
task_handler = TaskLogHandler(task_logs_dir)
task_formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
task_handler.setFormatter(task_formatter)
root_logger.addHandler(task_handler)

app = FastAPI(title="AutoQMYZ Manager WebUI")

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Models -----------------
class ConfigSchema(BaseModel):
    api_key: str
    base_url: str
    model: str
    task_parallel_limit: int
    user_parallel_limit: int
    answer_priority: list[str]
    manual_timeout: int

class UserCreateSchema(BaseModel):
    username: str
    account: str
    password: str
    verify_request: str = ""

class TaskItemSchema(BaseModel):
    course_name: str
    aim_questions_num_total: int
    low_right_rate: float
    top_right_rate: float
    min_question_time: float
    current_question_num: int = 0
    current_right_num: int = 0
    finish: bool = False

class QueueControlSchema(BaseModel):
    active: bool

class QueueAddSchema(BaseModel):
    username: str
    course_name: str

class QueueRemoveSchema(BaseModel):
    id: str

# ----------------- Configuration APIs -----------------
CONFIG_FILE = os.path.join(project_root, "config.toml")

def load_toml_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "ai": {
                "api_key": "", 
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai", 
                "model": "gemini-3.1-flash-lite"
            },
            "system": {
                "task_parallel_limit": 1, 
                "user_parallel_limit": 1
            },
            "answer": {
                "answer_priority": ["db", "ai", "manual", "random"], 
                "manual_timeout": 20
            }
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                toml.dump(default_config, f)
        except Exception:
            pass
        return default_config
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return toml.load(f)

def save_toml_config(config_dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        toml.dump(config_dict, f)

# 启动时确保配置文件存在
load_toml_config()

@app.get("/api/config")
def get_config():
    config = load_toml_config()
    ai = config.get("ai", {})
    system = config.get("system", {})
    answer = config.get("answer", {})
    return {
        "api_key": ai.get("api_key", ""),
        "base_url": ai.get("base_url", "https://api.openai.com/v1"),
        "model": ai.get("model", "gpt-4o-mini"),
        "task_parallel_limit": system.get("task_parallel_limit", 1),
        "user_parallel_limit": system.get("user_parallel_limit", 1),
        "answer_priority": answer.get("answer_priority", ["db", "ai", "manual", "random"]),
        "manual_timeout": answer.get("manual_timeout", 30)
    }

@app.post("/api/config")
def post_config(schema: ConfigSchema):
    config = load_toml_config()
    config["ai"] = {
        "api_key": schema.api_key,
        "base_url": schema.base_url,
        "model": schema.model
    }
    config["system"] = {
        "task_parallel_limit": schema.task_parallel_limit,
        "user_parallel_limit": schema.user_parallel_limit
    }
    config["answer"] = {
        "answer_priority": schema.answer_priority,
        "manual_timeout": schema.manual_timeout
    }
    save_toml_config(config)
    return {"message": "配置更新成功"}

# ----------------- User APIs -----------------
USER_DIR = os.path.join(project_root, "Data", "User")
TEMPLATE_FILE = os.path.join(USER_DIR, "模板与解释.json")

def get_course_stats(course_name):
    csv_file = os.path.join(project_root, "Data", "Question_data", f"{course_name}.csv")
    if not os.path.exists(csv_file):
        return {"question_count": 0, "exists": False}
    try:
        with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        count = max(0, len(lines) - 1)
        return {"question_count": count, "exists": True}
    except Exception:
        return {"question_count": 0, "exists": False}

@app.get("/api/users")
def list_users():
    users = []
    os.makedirs(USER_DIR, exist_ok=True)
    # Scan user files
    for filepath in glob(os.path.join(USER_DIR, "*.json")):
        filename = os.path.basename(filepath)
        if filename == "模板与解释.json":
            continue
        username = os.path.splitext(filename)[0]
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                user_data = json.load(f)
            
            # Map verified courses with their local DB stats
            verified_courses_raw = user_data.get("other", {}).get("verified_courses", [])
            verified_courses = []
            for course_name in verified_courses_raw:
                stats = get_course_stats(course_name)
                verified_courses.append({
                    "name": course_name,
                    "question_count": stats["question_count"],
                    "exists": stats["exists"]
                })
                
            users.append({
                "username": username,
                "account": user_data.get("user", {}).get("account", ""),
                "verify_request": user_data.get("user", {}).get("verify_request", ""),
                "UA": user_data.get("other", {}).get("UA", ""),
                "tasks": user_data.get("tasks", []),
                "login_status": user_data.get("other", {}).get("login_status", "unverified"),
                "verified_courses": verified_courses
            })
        except Exception as e:
            root_logger.error(f"加载用户 {username} 配置失败: {e}")
    return users

@app.post("/api/users")
def create_user(schema: UserCreateSchema):
    os.makedirs(USER_DIR, exist_ok=True)
    user_file = os.path.join(USER_DIR, f"{schema.username}.json")
    if os.path.exists(user_file):
        raise HTTPException(status_code=400, detail="该用户已存在")
    
    # Initialize from template
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, "r", encoding="utf-8-sig") as f:
            template_data = json.load(f)
    else:
        template_data = {
            "user": {"account": "", "password": "", "verify_request": ""},
            "tasks": [],
            "other": {"UA": ""}
        }
    
    template_data["user"]["account"] = schema.account
    template_data["user"]["password"] = schema.password
    template_data["user"]["verify_request"] = schema.verify_request
    template_data["tasks"] = []  # Start with no default tasks
    if "other" not in template_data:
        template_data["other"] = {}
    template_data["other"]["UA"] = ""
    template_data["other"]["login_status"] = "unverified"
    template_data["other"]["verified_courses"] = []
    
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(template_data, f, ensure_ascii=False, indent=2)
    return {"message": f"用户 {schema.username} 创建成功"}

@app.delete("/api/users/{username}")
def delete_user(username: str):
    user_file = os.path.join(USER_DIR, f"{username}.json")
    if not os.path.exists(user_file):
        raise HTTPException(status_code=404, detail="用户不存在")
    try:
        os.remove(user_file)
        
        # 删除该用户的任务日志文件
        if os.path.exists(task_logs_dir):
            for filename in os.listdir(task_logs_dir):
                if filename.startswith(f"{username}_") and filename.endswith(".log"):
                    try:
                        os.remove(os.path.join(task_logs_dir, filename))
                    except Exception:
                        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除用户失败: {e}")
    return {"message": "用户删除成功"}

class UserUpdateSchema(BaseModel):
    account: str
    password: str = ""
    verify_request: str = ""
    UA: str = ""

@app.post("/api/users/{username}/update")
def update_user_info(username: str, schema: UserUpdateSchema):
    user_file = os.path.join(USER_DIR, f"{username}.json")
    if not os.path.exists(user_file):
        raise HTTPException(status_code=404, detail="用户不存在")
    
    with open(user_file, "r", encoding="utf-8-sig") as f:
        user_data = json.load(f)
        
    user_data["user"]["account"] = schema.account
    if schema.password:
        user_data["user"]["password"] = schema.password
    user_data["user"]["verify_request"] = schema.verify_request
    
    if "other" not in user_data:
        user_data["other"] = {}
    user_data["other"]["UA"] = schema.UA
    user_data["other"]["login_status"] = "unverified"
    user_data["other"]["verified_courses"] = []
    
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)
        
    return {"message": "用户信息更新成功"}

@app.post("/api/users/{username}/verify")
def verify_user_login(username: str):
    user_file = os.path.join(USER_DIR, f"{username}.json")
    if not os.path.exists(user_file):
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        with open(user_file, 'r', encoding='utf-8-sig') as f:
            user_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载用户配置文件失败: {e}")
        
    account = user_data.get("user", {}).get("account", "")
    password = user_data.get("user", {}).get("password", "")
    verify_request = user_data.get("user", {}).get("verify_request", "")
    ua = user_data.get("other", {}).get("UA", "")
    
    if not verify_request and (not account or not password):
        raise HTTPException(status_code=400, detail="登录凭证不完整（需提供账号密码或 verify_request）")
        
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from AutoQMYZ.ImitateProcessing.AntiRobotDetection import get_ua
    from AutoQMYZ.ImitateProcessing.Login import login_user_by_code, login_user_by_verify_request
    
    options = webdriver.ChromeOptions()
    options.binary_location = os.path.join(project_root, "ChromeWithDriver", "chrome.exe")
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    if not ua:
        ua = get_ua()
    options.add_argument('user-agent=' + ua + ";webank/h5face;webank/1.0 yiban_android/5.0.17")
    
    service = Service(os.path.join(project_root, "ChromeWithDriver", "chromedriver112.exe"))
    driver = None
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        
        login_ok = False
        verify_request_url = ""
        
        # Try verify_request first if available
        if verify_request:
            try:
                login_user_by_verify_request(driver, verify_request)
                driver.get('http://112.5.88.114:31101/yiban-web/stu/toCourse.jhtml')
                course_list = driver.find_elements(By.CSS_SELECTOR, 'body > div.mui-content > ul > li')
                if len(course_list) > 0:
                    login_ok = True
                    verify_request_url = verify_request
            except Exception:
                pass
                
        # Fall back to account/password login if token validation failed
        if not login_ok:
            if account and password:
                verify_request_url, ua = login_user_by_code(driver, account, password, ua)
                # Save fresh verify_request and UA to user file
                user_data["user"]["verify_request"] = verify_request_url
                if "other" not in user_data:
                    user_data["other"] = {}
                user_data["other"]["UA"] = ua
                with open(user_file, "w", encoding="utf-8") as f:
                    json.dump(user_data, f, separators=(',', ':'), ensure_ascii=False)
            else:
                if verify_request:
                    raise Exception('凭证 verify_request 已失效，且未配置账号密码，无法重新获取。')
                else:
                    raise Exception('凭证不完整。')
                    
        # Double check courses with the final verify_request_url
        driver.get('http://112.5.88.114:31101/yiban-web/stu/toCourse.jhtml')
        course_list = driver.find_elements(By.CSS_SELECTOR, 'body > div.mui-content > ul > li')
        if len(course_list) == 0:
            raise Exception('登录成功，但未读取到课程列表。请于手机端登陆账号，进入青马易战并授权后重试。')
            
        courses = [c.text for c in course_list if c.text]
        
        # Save verification status and courses list
        if "other" not in user_data:
            user_data["other"] = {}
        user_data["other"]["login_status"] = "verified"
        user_data["other"]["verified_courses"] = courses
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(user_data, f, separators=(',', ':'), ensure_ascii=False)
            
        return {
            "success": True, 
            "message": "登录验证成功，已成功获取课程列表！", 
            "verify_request_url": verify_request_url,
            "courses": courses
        }
    except Exception as e:
        error_msg = str(e)
        try:
            if "other" not in user_data:
                user_data["other"] = {}
            user_data["other"]["login_status"] = "failed"
            user_data["other"]["verified_courses"] = []
            with open(user_file, "w", encoding="utf-8") as f:
                json.dump(user_data, f, separators=(',', ':'), ensure_ascii=False)
        except Exception:
            pass
        return {
            "success": False,
            "message": f"验证失败: {error_msg}"
        }
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

# ----------------- Task APIs -----------------
@app.get("/api/courses")
def get_courses():
    courses_dir = os.path.join(project_root, "Data", "Question_data")
    if not os.path.exists(courses_dir):
        return []
    files = glob(os.path.join(courses_dir, "*.csv"))
    courses = []
    for f in files:
        course_name = os.path.splitext(os.path.basename(f))[0]
        stats = get_course_stats(course_name)
        courses.append({
            "name": course_name,
            "question_count": stats["question_count"],
            "exists": stats["exists"]
        })
    return sorted(courses, key=lambda x: x["name"])

@app.get("/api/users/{username}/tasks")
def get_user_tasks(username: str):
    user_file = os.path.join(USER_DIR, f"{username}.json")
    if not os.path.exists(user_file):
        raise HTTPException(status_code=404, detail="用户不存在")
    with open(user_file, "r", encoding="utf-8-sig") as f:
        user_data = json.load(f)
    return user_data.get("tasks", [])

@app.post("/api/users/{username}/tasks")
def update_user_tasks(username: str, tasks: list[TaskItemSchema]):
    user_file = os.path.join(USER_DIR, f"{username}.json")
    if not os.path.exists(user_file):
        raise HTTPException(status_code=404, detail="用户不存在")
    
    with open(user_file, "r", encoding="utf-8-sig") as f:
        user_data = json.load(f)
    
    old_tasks = user_data.get("tasks", [])
    old_task_names = {t["course_name"] for t in old_tasks}
    
    new_tasks = [t.model_dump() for t in tasks]
    new_task_names = {t["course_name"] for t in new_tasks}
    
    # 1. Handle deleted tasks: if a task was in old_tasks but not in new_tasks, remove it from queue
    deleted_task_names = old_task_names - new_task_names
    
    # Clean up logs for deleted tasks
    for deleted_name in deleted_task_names:
        task_id = f"{username}_{deleted_name}"
        log_file = os.path.join(task_logs_dir, f"{task_id}.log")
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
            except Exception:
                pass
                
    global queue_items
    with queue_lock:
        queue_modified = False
        
        # Remove deleted tasks from queue if they are not running
        new_queue_items = []
        for item in queue_items:
            if item["username"] == username and item["course_name"] in deleted_task_names:
                if item["status"] != "running":
                    queue_modified = True
                    continue
            new_queue_items.append(item)
        queue_items = new_queue_items
        
        # 2. Handle modified tasks: if a task is already in the queue, reset completion and queue status to pending
        for new_t in new_tasks:
            task_id = f"{username}_{new_t['course_name']}"
            for item in queue_items:
                if item["id"] == task_id:
                    if item["status"] != "running":
                        # Reset completion status and queue item status
                        new_t["finish"] = False
                        item["status"] = "pending"
                        item["error"] = ""
                        item["started_at"] = ""
                        item["finished_at"] = ""
                        queue_modified = True
                    break
                    
        if queue_modified:
            save_queue_to_disk()
            
    user_data["tasks"] = new_tasks
    
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(user_data, f, separators=(',', ':'), ensure_ascii=False)
        
    return {"message": "任务列表更新成功", "tasks": user_data["tasks"]}


# ----------------- Queue Engine & State -----------------
QUEUE_FILE = os.path.join(project_root, "Data", "queue.json")

queue_items = []  # items format: {id, username, course_name, status, error, added_at, started_at, finished_at}
queue_active = False
queue_lock = threading.Lock()
active_drivers = {}  # task_id -> QingMYZClass
active_drivers_lock = threading.Lock()

def save_queue_to_disk():
    try:
        os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue_items, f, ensure_ascii=False, indent=2)
    except Exception as e:
        root_logger.error(f"保存队列数据失败: {e}")

def load_queue_from_disk():
    global queue_items
    if not os.path.exists(QUEUE_FILE):
        queue_items = []
        return
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
        valid_items = []
        modified = False
        for item in items:
            if isinstance(item, dict) and "id" in item and "username" in item and "course_name" in item:
                if item.get("status") == "running":
                    item["status"] = "stopped"
                    item["finished_at"] = datetime.now().isoformat()
                    modified = True
                valid_items.append(item)
            else:
                modified = True
        queue_items = valid_items
        if modified:
            save_queue_to_disk()
    except Exception as e:
        root_logger.error(f"加载队列数据失败: {e}")
        queue_items = []

load_queue_from_disk()

def update_task_status(task_id, status, error=""):
    with queue_lock:
        for item in queue_items:
            if item["id"] == task_id:
                item["status"] = status
                if error:
                    item["error"] = error
                if status in ["success", "failed", "stopped"]:
                    item["finished_at"] = datetime.now().isoformat()
                break
    save_queue_to_disk()

def get_task_status(task_id):
    with queue_lock:
        for item in queue_items:
            if item["id"] == task_id:
                return item["status"]
    return None

def run_task_thread(task_id, username, course_name):
    root_logger.info(f"[Task Runner] Thread started for {task_id}")
    user_file = os.path.join(USER_DIR, f"{username}.json")
    
    # Reset log file for task
    log_file = os.path.join(task_logs_dir, f"{task_id}.log")
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"=== 任务启动: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    except Exception:
        pass
        
    try:
        from AutoQMYZ.QingMYZMain import QingMYZClass
        q = QingMYZClass(user_file)
        
        # Read the initial show_browser setting from queue
        show_browser = False
        with queue_lock:
            for item in queue_items:
                if item["id"] == task_id:
                    show_browser = item.get("show_browser", False)
                    break
        q.show_browser_gui = show_browser
        q.task_id = task_id
        
        with active_drivers_lock:
            active_drivers[task_id] = q
            
        q.run_single_task_by_name(course_name)
        
        update_task_status(task_id, "success")
        root_logger.info(f"[Task Runner] Task {task_id} completed successfully.")
        
    except Exception as e:
        status = get_task_status(task_id)
        if status == "stopped":
            root_logger.info(f"[Task Runner] Task {task_id} was stopped manually.")
        else:
            update_task_status(task_id, "failed", error=str(e))
            root_logger.error(f"[Task Runner] Task {task_id} failed: {e}")
            
    finally:
        with active_drivers_lock:
            if task_id in active_drivers:
                del active_drivers[task_id]

def process_queue():
    global queue_items, queue_active
    config = load_toml_config()
    task_limit = config.get("system", {}).get("task_parallel_limit", 1)
    user_limit = config.get("system", {}).get("user_parallel_limit", 1)
    
    with queue_lock:
        running_tasks = [item for item in queue_items if item["status"] == "running"]
        running_count = len(running_tasks)
        
        if running_count >= task_limit:
            return
            
        pending_tasks = [item for item in queue_items if item["status"] == "pending"]
        
        for item in pending_tasks:
            if running_count >= task_limit:
                break
                
            user_running_count = sum(1 for t in running_tasks if t["username"] == item["username"])
            if user_running_count >= user_limit:
                continue
                
            item["status"] = "running"
            item["started_at"] = datetime.now().isoformat()
            running_count += 1
            running_tasks.append(item)
            save_queue_to_disk()
            
            t = threading.Thread(
                target=run_task_thread,
                args=(item["id"], item["username"], item["course_name"]),
                name=f"task_{item['id']}",
                daemon=True
            )
            t.start()

def scheduling_loop():
    while True:
        try:
            if queue_active:
                process_queue()
        except Exception as e:
            print(f"Error in queue scheduling: {e}")
        time.sleep(1)

# Start background thread
threading.Thread(target=scheduling_loop, daemon=True).start()

# ----------------- Queue Control APIs -----------------
@app.get("/api/queue")
def get_queue():
    from AutoQMYZ.GetAnswerProcessing.GetAnswer import manual_questions
    
    enriched_items = []
    with queue_lock:
        for item in queue_items:
            enriched_item = dict(item)
            
            # Enrich with task statistics
            username = item["username"]
            course_name = item["course_name"]
            user_file = os.path.join(USER_DIR, f"{username}.json")
            if os.path.exists(user_file):
                try:
                    with open(user_file, "r", encoding="utf-8-sig") as f:
                        user_data = json.load(f)
                    user_tasks = user_data.get("tasks", [])
                    task = next((t for t in user_tasks if t["course_name"] == course_name), None)
                    if task:
                        enriched_item["current_question_num"] = task.get("current_question_num", 0)
                        enriched_item["current_right_num"] = task.get("current_right_num", 0)
                        enriched_item["low_right_rate"] = task.get("low_right_rate", 0.7)
                        enriched_item["top_right_rate"] = task.get("top_right_rate", 0.9)
                        enriched_item["finish"] = task.get("finish", False)
                except Exception as e:
                    root_logger.error(f"Error enriching queue item {item['id']}: {e}")
            
            if item["status"] == "running":
                q = manual_questions.get(item["id"])
                if q:
                    remaining = q["timeout"] - (time.time() - q["start_time"])
                    if remaining > 0:
                        enriched_item["manual_question"] = {
                            "type": q["question"][0],
                            "title": q["question"][1],
                            "options": q["question"][2],
                            "remaining_time": max(0, int(remaining))
                        }
            enriched_items.append(enriched_item)
            
    return {"items": enriched_items, "active": queue_active}

@app.post("/api/queue/control")
def post_queue_control(schema: QueueControlSchema):
    global queue_active
    queue_active = schema.active
    
    if not queue_active:
        with queue_lock:
            for item in queue_items:
                if item["status"] == "running":
                    item["status"] = "stopped"
                    item["finished_at"] = datetime.now().isoformat()
                    task_id = item["id"]
                    with active_drivers_lock:
                        q = active_drivers.get(task_id)
                        if q:
                            q.stopped = True
                            if q.driver:
                                try:
                                    q.driver.quit()
                                except Exception:
                                    pass
    else:
        # Resuming queue: change any stopped/failed tasks back to pending
        with queue_lock:
            for item in queue_items:
                if item["status"] in ["stopped", "failed"]:
                    item["status"] = "pending"
                    item["started_at"] = ""
                    item["finished_at"] = ""
                    item["error"] = ""
    save_queue_to_disk()
    return {"message": "队列状态已更新", "active": queue_active}

@app.post("/api/queue/add")
def post_queue_add(schema: QueueAddSchema):
    task_id = f"{schema.username}_{schema.course_name}"
    
    with queue_lock:
        for item in queue_items:
            if item["id"] == task_id:
                if item["status"] in ["pending", "running"]:
                    return {"message": "任务已经在队列中", "item": item}
                item["status"] = "pending"
                item["error"] = ""
                item["added_at"] = datetime.now().isoformat()
                item["started_at"] = ""
                item["finished_at"] = ""
                save_queue_to_disk()
                return {"message": "任务已重新加入队列", "item": item}
        
        new_item = {
            "id": task_id,
            "username": schema.username,
            "course_name": schema.course_name,
            "status": "pending",
            "error": "",
            "added_at": datetime.now().isoformat(),
            "started_at": "",
            "finished_at": "",
            "show_browser": False
        }
        queue_items.append(new_item)
        save_queue_to_disk()
    return {"message": "任务已加入队列", "item": new_item}

@app.post("/api/queue/remove")
def post_queue_remove(schema: QueueRemoveSchema):
    task_id = schema.id
    removed = False
    
    with queue_lock:
        for item in queue_items:
            if item["id"] == task_id:
                if item["status"] == "running":
                    item["status"] = "stopped"
                    item["finished_at"] = datetime.now().isoformat()
                    with active_drivers_lock:
                        q = active_drivers.get(task_id)
                        if q:
                            q.stopped = True
                            if q.driver:
                                try:
                                    q.driver.quit()
                                except Exception:
                                    pass
                    removed = True
                elif item["status"] == "pending":
                    item["status"] = "stopped"
                    item["finished_at"] = datetime.now().isoformat()
                    removed = True
                else:
                    queue_items.remove(item)
                    removed = True
                break
                
    if not removed:
        raise HTTPException(status_code=404, detail="找不到该队列任务")
    save_queue_to_disk()
    return {"message": "任务已移出队列"}

class BrowserVisibilitySchema(BaseModel):
    show: bool

@app.post("/api/queue/{task_id}/browser")
def post_queue_browser_visibility(task_id: str, schema: BrowserVisibilitySchema):
    with queue_lock:
        item = None
        for q_item in queue_items:
            if q_item["id"] == task_id:
                item = q_item
                break
        if not item:
            raise HTTPException(status_code=404, detail="找不到该队列任务")
            
        item["show_browser"] = schema.show
        save_queue_to_disk()
        
    with active_drivers_lock:
        q = active_drivers.get(task_id)
        if q:
            q.show_browser_gui = schema.show
            if schema.show:
                q.show_browser()
            else:
                q.hide_browser()
                
    return {"message": "浏览器显示状态已更新", "show": schema.show}

class SubmitManualAnswerSchema(BaseModel):
    answers: list[str]

@app.post("/api/queue/{task_id}/manual")
def post_manual_answer(task_id: str, schema: SubmitManualAnswerSchema):
    from AutoQMYZ.GetAnswerProcessing.GetAnswer import manual_questions
    
    q = manual_questions.get(task_id)
    if not q:
        raise HTTPException(status_code=400, detail="该任务当前没有等待人工作答的问题，或者已超时。")
    q["answer"] = schema.answers
    return {"message": "答案已成功提交"}

# ----------------- Logs APIs -----------------
@app.get("/api/logs/stats")
def get_logs_stats():
    import glob
    system_log_size = 0
    task_logs_size = 0
    task_logs_count = 0
    
    logs_dir = os.path.dirname(task_logs_dir)
    
    # Calculate system logs size
    if os.path.exists(logs_dir):
        for f in glob.glob(os.path.join(logs_dir, "app.log*")):
            if os.path.isfile(f):
                system_log_size += os.path.getsize(f)
                
    # Calculate task logs size
    if os.path.exists(task_logs_dir):
        for f in glob.glob(os.path.join(task_logs_dir, "*.log")):
            if os.path.isfile(f):
                task_logs_size += os.path.getsize(f)
                task_logs_count += 1
                
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
        
    return {
        "system_log_size": format_size(system_log_size),
        "task_logs_size": format_size(task_logs_size),
        "task_logs_count": task_logs_count
    }

@app.post("/api/logs/clear")
def clear_logs():
    import glob
    cleaned_files = 0
    errors = []
    
    # Determine running task ids
    running_task_ids = set()
    with queue_lock:
        for item in queue_items:
            if item["status"] == "running":
                running_task_ids.add(item["id"])
                
    # 1. Clear task logs (except running ones)
    if os.path.exists(task_logs_dir):
        for f in glob.glob(os.path.join(task_logs_dir, "*.log")):
            basename = os.path.basename(f)
            task_id = os.path.splitext(basename)[0]
            if task_id in running_task_ids:
                continue
            try:
                os.remove(f)
                cleaned_files += 1
            except Exception as e:
                errors.append(f"无法删除任务日志 {basename}: {e}")
                
    # 2. Clear app.log backups and truncate app.log
    logs_dir = os.path.dirname(task_logs_dir)
    if os.path.exists(logs_dir):
        for f in glob.glob(os.path.join(logs_dir, "app.log.*")):
            try:
                os.remove(f)
                cleaned_files += 1
            except Exception as e:
                errors.append(f"无法删除系统备份日志 {os.path.basename(f)}: {e}")
                
        main_app_log = os.path.join(logs_dir, "app.log")
        if os.path.exists(main_app_log):
            try:
                # 寻找指向 app.log 且打开状态的文件处理器，并将其关闭以释放句柄
                import logging
                file_handlers = []
                for handler in logging.getLogger().handlers:
                    if isinstance(handler, logging.FileHandler) and os.path.abspath(handler.baseFilename) == os.path.abspath(main_app_log):
                        file_handlers.append(handler)
                        
                for handler in file_handlers:
                    handler.close()
                    
                # 安全清空并重写 app.log
                with open(main_app_log, "w", encoding="utf-8") as f:
                    f.write(f"=== 系统日志已于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 由用户清空 ===\n")
                
                # 重置处理器的 stream 为 None，使其在下次写入时自动重新打开文件
                for handler in file_handlers:
                    handler.stream = None
                    
                cleaned_files += 1
            except Exception as e:
                errors.append(f"无法清空系统日志 app.log: {e}")
                
    return {
        "message": "日志清理完毕",
        "cleaned_files_count": cleaned_files,
        "errors": errors
    }

@app.get("/api/logs/{task_id}")
def get_task_logs(task_id: str):
    log_file = os.path.join(task_logs_dir, f"{task_id}.log")
    if not os.path.exists(log_file):
        return {"logs": "暂无该任务日志记录"}
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Return the last 600 lines to prevent sending too much data
        last_lines = lines[-600:]
        return {"logs": "".join(last_lines)}
    except Exception as e:
        return {"logs": f"读取日志出错: {e}"}

# ----------------- Static Frontend Assets Serve -----------------
dist_dir = os.path.join(project_root, "WebUI", "dist")

@app.get("/assets/{file_path:path}")
def get_assets(file_path: str):
    asset_file = os.path.join(dist_dir, "assets", file_path)
    if os.path.exists(asset_file):
        media_type = "application/javascript" if file_path.endswith(".js") else "text/css" if file_path.endswith(".css") else "application/octet-stream"
        try:
            with open(asset_file, "rb") as f:
                content = f.read()
            return Response(content=content, media_type=media_type)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取静态资源出错: {e}")
    raise HTTPException(status_code=404, detail="资源未找到")

@app.get("/{file_path:path}")
def serve_spa(file_path: str):
    if file_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API Endpoint not found")
        
    index_file = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_file):
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        except Exception as e:
            return HTMLResponse(content=f"加载页面出错: {e}", status_code=500)
            
    return HTMLResponse(content="<h3>WebUI 静态前端资源未找到！</h3><p>请先在 WebUI 目录下运行构建：<code>npm run build</code></p>", status_code=404)

# Main startup command wrapper
if __name__ == "__main__":
    import uvicorn
    # Automatically print friendly launch advice
    print("==================================================================")
    print("  AutoQMYZ WebUI 管理系统启动中...")
    print("  启动成功后，请在浏览器中打开： http://127.0.0.1:8000")
    print("==================================================================")
    uvicorn.run(app, host="127.0.0.1", port=8000)