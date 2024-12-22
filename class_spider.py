import time

from oa_auth import OAAuth
from concurrent.futures import ThreadPoolExecutor
from parsel import Selector
from loguru import logger



class ClassSpider:
    def __init__(self, username, password):
        self.class_type = ["programTask", "commonTask", "sportTask"]
        self.choose_params = {
            "sportTask": "SportTask",
            "commonTask": "CommonTask",
            "programTask": "PlanTask",
        }
        self.oa = OAAuth(
            service="https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=studentPortal:DEFAULT_EVENT")
        self.oa.login(username, password)

    def get_class_main(self):
        executor = ThreadPoolExecutor(max_workers=4)
        for class_type in self.class_type:
            executor.submit(self.get_class_one_type, class_type)
        executor.shutdown(wait=True)



    def get_class_one_type(self, class_type):
        url = f"https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=chooseCourse:{class_type}&CT=1"
        res = self.oa.get_session().get(url)
        document = Selector(text=res.text)
        class_list = document.css(".courseShow")
        data_list = []
        for class_item in class_list:
            data = {
                "name": class_item.css(".name::text").get(),
                "cid": class_item.css(".trigger::attr(cid)").get(),
            }
            data_list.append(data)
        executor = ThreadPoolExecutor(max_workers=8)
        for item in data_list:
            executor.submit(self.get_class_one, class_type, item)
        executor.shutdown(wait=True)

    def get_class_one(self, class_type, class_data):
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://matrix.dean.swust.edu.cn",
            "priority": "u=1, i",
            "referer": "https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=chooseCourse:sportTask&CT=1",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        }
        url = "https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm"
        params = {
            "event": f"chooseCourse:api{self.choose_params[class_type]}Table"
        }
        data = {
            "CID": class_data["cid"],
        }
        res = self.oa.get_session().post(url, data=data, headers=headers, params=params)
        document = Selector(text=res.text)
        data = document.css(".editRows")
        for item in data:

            js_code = item.css("a::attr(href)").get()
            if not js_code:
                logger.warning("当前课程已满")
                continue

            js_code = js_code.replace(" ", "")
            choose_data = js_code.split("chooseCourse(")[1].strip(")';").split("','")
            # 将参数转换为字典
            data = {
                "CT": "1",  # 这个值是固定的，根据你的要求
                "TID": choose_data[2].strip("'"),
                "CID": choose_data[0].strip("'"),
                "CIDX": choose_data[1].strip("'"),
                "TSK": choose_data[4].strip("'"),
                "TT": choose_data[3].strip("'"),
                "ST": choose_data[5].strip("'"),
                "seed": int(time.time() * 1000)
            }


            url = "https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm"
            params = {
                "event": f"chooseCourse:apiChoose{self.choose_params[class_type]}"
            }
            headers = {
                "accept": "*/*",
                "accept-language": "zh-CN,zh;q=0.9",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "origin": "https://matrix.dean.swust.edu.cn",
                "priority": "u=1, i",
                "referer": "https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=chooseCourse:sportTask&CT=1",
                "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "x-requested-with": "XMLHttpRequest"
            }
            res = self.oa.get_session().post(url, data=data, headers=headers, params=params)
            if res.json()['success']:
                logger.success(f"成功选择: {class_data['name']}")
                return
            else:
                logger.error(f"选择{class_data['name']}失败")


test = ClassSpider("", "")
while True:
    try:
        test.get_class_main()
    except Exception as e:
        pass