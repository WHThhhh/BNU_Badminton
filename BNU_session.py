import os
import re
from io import BytesIO
from PIL import Image
import base64
import time
import glob
import datetime
import ddddocr
import selenium
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By


class Session(object):
    """
    BNU 抢羽毛球
    """

    def __init__(self, usr, pwd, date, sport, stime, position, get_data=False):
        self.username = 'BNU'
        self.username = str(usr)
        self.password = str(pwd)
        self.Appointment_time = date
        self.sport_list = ["'5326'", "'5462'", "'68788'"]
        self.sport = self.sport_list[sport - 1]
        self.stime = str(stime - 6)
        self.position = str(position)
        self.ocr = ddddocr.DdddOcr()
        self.s_path = Service(glob.glob('./chromedriver/*')[0])
        self.driver = webdriver.Chrome(service=self.s_path)
        # just get valid data for model training
        self.get_data = get_data

    def run(self):
        self.ori_page_Login()
        self.get_GYM_page()
        self.check_page()
        self.select_time()
        while True:
            is_valid, now, valid_str = self.get_valid()
            while not is_valid:
                self.driver.refresh()
                time.sleep(0.5)
                self.select_time()
                is_valid, now, valid_str = self.get_valid()
            with open('./Valid_pic/' + now + '.txt', 'a+') as ans:
                ans.write(valid_str)
            if not self.get_data:
                break
            self.driver.refresh()
            time.sleep(0.1)
            self.select_time()

        self.success()

    # 登录
    def ori_page_Login(self):
        url = "https://onevpn.bnu.edu.cn/"
        self.driver.get(url)
        user_input = self.driver.find_element(by=By.XPATH, value='//input[@id="un"]')
        pw_input = self.driver.find_element(by=By.XPATH, value='//input[@id="pd"]')
        user_input.send_keys(self.username)
        pw_input.send_keys(self.password)
        login_btn = self.driver.find_element(by=By.CLASS_NAME, value='landing_btn_bg1')
        login_btn.click()
        time.sleep(0.5)
        return

    def get_GYM_page(self):
        GYM_btn = self.driver.find_element(by=By.XPATH, value='//*[@app_code="tygglyyxt"]/div/span')
        GYM_btn.click()
        time.sleep(1)
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[1])
        GYM_Agree = self.driver.find_element(by=By.XPATH, value='//*[@id="attentionModal"]/div[3]/button')
        GYM_Agree.click()
        time.sleep(0.5)
        return

    def check_page(self):
        alert_item = self.driver.find_elements(by=By.XPATH, value='//div[@class="alert alert-error fade in"]')
        while len(alert_item) != 0:
            time.sleep(0.05)
            self.driver.refresh()
            alert_item = self.driver.find_elements(by=By.XPATH, value='//div[@class="alert alert-error fade in"]')
            print("Page not open!")
        return

    def select_time(self):
        js_script = "javascript: changeDate('2'," + self.sport + ",'','3'," + self.Appointment_time + ");"
        self.driver.execute_script(js_script)
        time.sleep(0.5)
        choose_table = self.driver.find_element(by=By.XPATH, value='//iframe[@name="overlayView"]')
        self.driver.switch_to.frame(choose_table)
        choose = self.driver.find_element(by=By.XPATH, value='/html/body/table/tbody/tr[{}]/td[{}]'.format(self.stime,
                                                                                                           self.position))
        choose.click()
        # time.sleep(0.5)
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[1])
        appoint = self.driver.find_element(by=By.XPATH, value='//span[@class="btn btn-success fileinput-button"]')
        appoint.click()
        time.sleep(0.5)
        return

    def get_valid(self):
        js = "let c = document.createElement('canvas');let ctx = c.getContext('2d');" \
             "let img = document.getElementsByTagName('img')[1];" \
             "c.height=img.naturalHeight;c.width=img.naturalWidth;" \
             "ctx.drawImage(img, 0, 0,img.naturalWidth, img.naturalHeight);" \
             "let base64String = c.toDataURL();return base64String;"
        base64_str = self.driver.execute_script(js)
        base64_data = re.sub('^data:image/.+;base64,', '', base64_str)
        byte_data = base64.b64decode(base64_data)
        image_data = BytesIO(byte_data)
        img = Image.open(image_data)
        now = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S.%f')
        img.save('./Valid_pic/' + now + '.png')
        is_valid, valid_str = self.OCR(now)
        return is_valid, now, valid_str

    def success(self):
        self.driver.find_element(by=By.XPATH, value='//*[@id="contactCompanion"]/div[3]/a[1]').click()
        time.sleep(1)
        pay = self.driver.find_element(by=By.XPATH, value='//*[@id="div_pay"]/div[3]/a[2]')
        pay.click()
        time.sleep(100)
        return

    def OCR(self, now):
        with open('./Valid_pic/' + now + '.png', 'rb') as f:
            img_bytes = f.read()
        res = self.ocr.classification(img_bytes)
        res = res[:-1]
        symbol = ['+', '-']
        if '=' in res:
            res = res.replace('=', '')
        print(res)
        for i_s, s in enumerate(symbol):
            if s in res:
                num = res.split(s)
                if len(num[1]) == 0 or len(num[1]) == 0:
                    break
                if i_s == 0:
                    ans = int(num[0]) + int(num[1])
                else:
                    ans = int(num[0]) - int(num[1])
                check = self.send_check(ans)
                if check:
                    return True, str(num[0]) + s + str(num[1])

        res = ''.join(re.findall(r"\d+", res))

        for i in range(len(res) - 1):
            n_1 = int(res[:i + 1])
            n_2 = int(res[i + 1:])
            ans = [n_1 + n_2, n_1 - n_2]
            print(n_1, n_2)
            for ia, a in enumerate(ans):
                check = self.send_check(a)
                if check:
                    return True, str(n_1) + symbol[ia] + str(n_2)
        return False, None

    def send_check(self, ans):
        ans_input = self.driver.find_element(by=By.XPATH, value='//input[@id="checkcodeuser"]')
        # ans_input = self.driver.find_element(by=By.XPATH, value='/html/body/div[1]/form/div[3]/label/div/input')
        ans_input.clear()
        ans = str(ans)
        for a_ in ans:
            ans_input.send_keys(a_)
            time.sleep(0.02)
        time.sleep(0.05)
        color = self.driver.find_element(by=By.XPATH, value='//em[@id="msginfo"]').get_attribute('class')
        return color == "greencolor"
