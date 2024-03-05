from selenium.webdriver.common.by import By

# 进入答题页面
def into_answer_web(driver):
    answer_web_1 = driver.find_element(By.CSS_SELECTOR, '#homeWrapper > div.nav > ul > li:nth-child(2)')
    answer_web_1.click()
    answer_web_2 = driver.find_element(By.CSS_SELECTOR, 'body > div.mui-content > ul > li:nth-child(5) > a')
    # answer_web_2 = driver.find_element(By.CSS_SELECTOR, 'body > div.mui-content > ul > li:nth-child(1) > a')
    answer_web_2.click()

    return driver