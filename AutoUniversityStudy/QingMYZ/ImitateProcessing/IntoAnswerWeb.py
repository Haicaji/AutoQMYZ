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
        raise Exception('未找到课程,请检查课程名是否正确')
    else:
        raise Exception('未读取到课程列表,请于手机端登陆账号,进入青马易战并授权,然后退出手机端并此程序,经测试该操作能解决绝大部分此类问题')
