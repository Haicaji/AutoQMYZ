from selenium.webdriver.common.by import By

# 登入用戶
def login_user_by_verify_request(driver, verify_request_url):
    # 打开网页
    driver.get(verify_request_url)

def login_user_by_code(driver, name, passwd):
    # 打开网页
    url = ""
    driver.get(url)

    # 获取用户名和密码输入位置
    oauth_uname = driver.find_element(By.ID, 'oauth_uname_w')
    oauth_upwd = driver.find_element(By.ID, 'oauth_upwd_w')

    oauth_uname.send_keys(name)
    oauth_upwd.send_keys(passwd)

    oauth_check_login = driver.find_element(By.CLASS_NAME, "oauth_check_login")
    oauth_check_login.click()