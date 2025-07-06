import json
import re

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import time
import random
from fake_useragent import UserAgent
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 只获取桌面版 User-Agent
ua = UserAgent()
user_agent = ua.chrome  # 或者 ua.firefox, ua.ie 等，确保是桌面浏览器

# 配置 Chrome 选项
options = webdriver.ChromeOptions()
options.add_argument(f'user-agent={user_agent}')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# 启动浏览器
driver = webdriver.Chrome(options=options)

# 修改 navigator.webdriver 属性
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    result = {
        "jobs": []
    }
    # 访问目标网站
    for p in range(1,50) :
        url = f"https://we.51job.com/api/job/search-pc?api_key=51job&timestamp={int(time.time())}&keyword=python&searchType=2&jobArea=040000&sortType=0&pageNum={p}&pageSize=20&source=1&pageCode=sou%7Csou%7Csoulb&scene=7"
        driver.get(url)
        time.sleep(random.uniform(1, 10))
        # 等待滑块元素出现（最多10秒）
        slider = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "nc_1_n1z"))
        )
        while True:
        # 滑动操作
            action = ActionChains(driver)
            action.click_and_hold(slider).perform()

            # 模拟人工滑动（更随机化）
            total_distance = 260  # 滑块轨道总长度
            steps = random.randint(4, 6)  # 合理步数
            base_offset = total_distance // steps  # 基础步长
            remainder = total_distance % steps  # 剩余距离

            for i in range(steps):
                # 最后一步补足余数
                offset = base_offset + (remainder if i == steps - 1 else 0)
                # 添加±5px随机扰动模拟人工
                offset += random.randint(-5, 5)

                action.move_by_offset(offset, 0).perform()
                time.sleep(random.uniform(0.1, 0.3))

            action.release().perform()
            print("滑块验证通过")

        # page_source = driver.page_source

            time.sleep(random.uniform(1, 10))
        # 解析JSON
            try:
                data = driver.execute_script("""
                    return JSON.parse(document.body.innerText.match(/{.*}/s)[0]);
                """)

                for item in data['resultbody']['job']['items']:
                    job_info = {
                        "岗位名称": item['jobName'],
                        "标签": item['jobTags'],
                        "工作区域": item['jobAreaString'],
                        "薪资": item['provideSalaryString'],
                        "发布时间": item['issueDateString'],
                        "经验要求": item['workYearString'],
                        "学历要求": item['degreeString'],
                        "公司名称": item['fullCompanyName'],
                        "公司类型": item['companyTypeString'],
                        "行业": item['companyIndustryType1Str'],
                        "职位描述": item['jobDescribe']
                    }
                    result['jobs'].append(job_info)

                # 保存到JSON文件

                print(f"数据{p}已保存到 51job_python_jobs.json")

                time.sleep(random.uniform(1, 10))
                break
            except:
                pass
        with open('51job_python_jobs.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        # 处理每个职位信息

finally:
    driver.quit()