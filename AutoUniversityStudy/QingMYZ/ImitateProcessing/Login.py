import base64
import re
import requests

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from AutoUniversityStudy.QingMYZ.ImitateProcessing.AntiRobotDetection import get_ua

# 登入用戶
def login_user_by_verify_request(driver, verify_request_url):
    # 打开网页
    driver.get(verify_request_url)
    # 刷新网页
    driver.refresh()

def encryptPassword(pwd):
    # 密码加密
    PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAzq0rgsM++ZxLRGHpdfre
Hu6UXhdlUS5P2WOxRG14qU8/iWSb/CkOqgOl8AGcOhlthkvolCdpUvVcVsVUxBv0
YRN0Jb64zPrn5aLVwQT4RJn5tXvoqLdHIXis7pljXAMDPVZOVlWJkDMk8YU6HDaA
MqsD6l5p9lg2LMP4OhMgaPX+CkO370LB5vRjJTHp03n+IqfxXoC7DEd+kxRIEM2C
EDgUSYDJBDgwBvGALZmvB/a1b0im9t1P/EmnuE7uN9NRFoWyVpOiEwo/Ti7rmJGf
qNT3vvtfWo4nXsm1rYQXsPayoKDSRaba3gFY/1SYWLAuSO2q2da5ZCcsAk5RKy0V
c1hUg8n6y0YLAvuzoXY5VyNMXkhH5Zc5Kg64b5RxILeZpZG0MV7GFY3sw//k7SNg
darKT8A0Iv3l3lfguX3HNi6dkf97kS/EiA0tbkIB/JNjv13mq8HL7LijRt2hkKqP
PhQW88xC/exZilU5pAavoZOPuZIOTUHqtpRq4ZeKl+wDf+e5lPYFDpihWGjplGpa
4BOSmGeo/SyVFPji9QF4Pk0DRJF/NjwJoAC60xHAVt5Z4gQSOOOjNZDCswA0ry2L
e8m5cv5vPGY75uVrGqALQ6Xm961PPc5cJ1q7tmEZMj+z5HE7tgAdhiPI6acKgrAv
+1k4N0OVqKamMS+PVpD05hUCAwEAAQ==
-----END PUBLIC KEY-----'''
    cipher = PKCS1_v1_5.new(RSA.importKey(PUBLIC_KEY))
    cipher_text = base64.b64encode(cipher.encrypt(bytes(pwd, encoding="utf8")))
    return cipher_text.decode("utf-8")

def login(name, passwd):
    params = {
        "mobile": name,			 # 必要，登录手机号
        "password": encryptPassword(passwd), # 必要，RSA加密后的登录密码，如 "password": encryptPassword("123456"), 
        "ct": "2",			 # 必要，固定参数
        "identify": "0",		 # 必要，固定参数
        }
    HEADERS = {
        "AppVersion": "5.0.17"		 # 必要，由最新app版本得到
        }
    COOKIES = {}
    # 配置登录数据
    response = requests.post("https://m.yiban.cn/api/v4/passport/login", data=params, allow_redirects=False, cookies=COOKIES, headers=HEADERS).json()
    if response is not None and response["response"] == 100:
        access_token = response["data"]["access_token"]
        yb_uid = response["data"]['user']["user_id"]

        return yb_uid, access_token
    else:
        raise Exception("登录失败")

def get_verify_request(access_token, UA):
    if UA != "":
        ua = UA
    else:
        ua = get_ua()
    COOKIES = {"loginToken": access_token}
    HEADERS = {
        "Origin": "m.yiban.cn",
        "origin":"api.uyiban.com",
        "origin":"https://c.uyiban.com",
        "authority": "api.uyiban.com",
        "AppVersion": "5.0.17",
        "x-requested-with": "com.yiban.app",
        "user-agent": ua + ";webank/h5face;webank/1.0 yiban_android/5.0.17"
        }
    iapp = requests.get("http://f.yiban.cn/iapp/index?act=iapp76127", headers=HEADERS, allow_redirects=False, cookies=COOKIES) # 利用 loginToken 访问获取 verifyRequest跳转数据
    act = iapp.headers["Location"] # 返回302跳转目标
    verifyRequest = re.findall(r"verify_request=(.*?)&", act)[0] # 正则取302跳转目标，得到 verify_request 数据

    return verifyRequest, ua

def login_user_by_code(driver, name, passwd, UA):
    yb_uid, access_token = login(name, passwd)
    verify_request, UA = get_verify_request(access_token, UA)
    verify_request_url = f'http://112.5.88.114:31101/yiban-web/stu/homePage.jhtml?verify_request={verify_request}&yb_uid={yb_uid}'
    print(verify_request_url)
    login_user_by_verify_request(driver, verify_request_url)

    return verify_request_url, UA