import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from AutoQMYZ import get_project_root

class LoggerWriter:
    """
    一个文件类对象，用于将 stdout/stderr 写入重定向到 logging 系统中。
    采用缓冲区设计，只有在写入换行符时才触发日志记录，保证多参数 print 处于同一行。
    """
    def __init__(self, logger, level, original_stream):
        self.logger = logger
        self.level = level
        self.original_stream = original_stream
        self.buffer = ""

    def write(self, message):
        self.buffer += message
        # 只要缓冲区中存在换行符，就切分整行并进行日志输出
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            msg = line.strip()
            if msg:
                self.logger.log(self.level, msg)

    def flush(self):
        # 刷新时若缓冲区还有残留内容，则输出并清空
        msg = self.buffer.strip()
        if msg:
            self.logger.log(self.level, msg)
            self.buffer = ""
        self.original_stream.flush()

    def isatty(self):
        return False

def setup_logging():
    project_root = get_project_root()
    logs_dir = os.path.join(project_root, 'Data', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # 自动清理 7 天前未修改过的任务日志文件
    import time
    task_logs_dir = os.path.join(logs_dir, 'tasks')
    if os.path.exists(task_logs_dir):
        now = time.time()
        retention_period = 7 * 24 * 3600  # 7 days in seconds
        try:
            for filename in os.listdir(task_logs_dir):
                file_path = os.path.join(task_logs_dir, filename)
                if os.path.isfile(file_path) and filename.endswith('.log'):
                    if (now - os.path.getmtime(file_path)) > retention_period:
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
        except Exception as e:
            sys.__stderr__.write(f"自动清理历史任务日志失败: {e}\n")
    
    # 日志输出格式
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置文件日志处理器：每天午夜轮转，保留 7 天备份
    log_file = os.path.join(logs_dir, 'app.log')
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='D',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 配置控制台日志处理器：直接向 sys.__stdout__ 写入以避免重定向死循环
    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.setFormatter(formatter)
    
    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清空已有 handler 防止重复加载
    logger.handlers.clear()
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 重定向 stdout 和 stderr 到 logger
    sys.stdout = LoggerWriter(logger, logging.INFO, sys.__stdout__)
    sys.stderr = LoggerWriter(logger, logging.ERROR, sys.__stderr__)
