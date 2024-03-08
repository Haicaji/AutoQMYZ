from selenium.webdriver.common.by import By

# 进入答题页面
def into_answer_web(driver, course_name):
    driver.get('http://112.5.88.114:31101/yiban-web/stu/toCourse.jhtml')

    course_list = driver.find_elements(By.CSS_SELECTOR, 'body > div.mui-content > ul > li')
    if len(course_list) != 0:
        for course in course_list:
            if course.text == course_name:
                course.click()
                return 
        raise Exception('未找到课程')
    else:
        raise Exception('未找到课程')

