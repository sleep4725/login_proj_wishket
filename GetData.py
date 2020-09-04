import os
import yaml
import json
import time
from elasticsearch import helpers
from bs4 import BeautifulSoup
import requests

from GetChromeDriver.RetChrome import RetChromeDriver
from Elastic.retElastic import RetElastic


"""
    __group study 2회차__1번 wishket 
    __author__ : KimJunHyeon
    __date__   : 20200905
    __comment__:    웹에서 데이터 크롤링 시 가장 문제가 되는 부분이 해당 사이트의 개편이다.
                    따라서 tag에 접근시에 예외처리 부분을 감싸 관리자가 이를 감지해야 한다.
                    
                    코드의 간단한 설계 구조는 위시켓에서 크롤링으로 가져온 데이터를 Elasticsearch에 indexing 하는 
                    구조이다. 따라서 Elasticsearch가 구동 중이지 않을 시 이 코드는 정상적으로 수행되지 않는다.
"""

class GetData:


    def __init__(self):

        self.es_client = RetElastic.get_elastic_node()
        self.es_index  = RetElastic.INDEX_
        self.chrome_driver = RetChromeDriver.get_chrome_instance()
        self.wishkey_url = GetData.get_url().get("url")
        self.secret_info = GetData.secret_data_get()
        self.action = list()
        self.collect_time = time.strftime("%Y%m%d %H:%M", time.localtime())

    def is_alive(self):

        sess = requests.Session()

        try:
            response = sess.get(url=self.wishkey_url)
        except requests.exceptions.ConnectionError as err:
            print(err)
            sess.close()
            exit(1)
        else:
            if response.status_code == 200 and response.ok:
                sess.close()
                self.do_login()
            else:
                print("request url error !!")
                sess.close()
                exit(1)

    def do_login(self):

        self.chrome_driver.get(url=self.wishkey_url)
        time.sleep(2)

        try:
            ## login 시도______________________________________________________________________________________________
            self.chrome_driver.find_element_by_xpath('//*[@id="id_identification"]').send_keys(self.secret_info["id_"])
            time.sleep(1)
            self.chrome_driver.find_element_by_xpath('//*[@id="id_password"]').send_keys(self.secret_info["pw_"])
            time.sleep(1)
        except:
            print("login error !!")
            exit(1)
        else:
            self.chrome_driver.find_element_by_xpath('//*[@id="submit"]').click()
            time.sleep(2)

        try:
            response = self.chrome_driver.find_element_by_css_selector("div.subtitle-1-medium.mb32.user-title")
        except:
            print("login에 실패한 것으로 보입니다.")
            exit(1)
        else:
            print(response.text)

        try:
            # 프로젝트 찾기 button_____________
            self.chrome_driver.find_element_by_xpath('/html/body/header/section[1]/div/div[1]/a[1]').click()
            time.sleep(2)
        except:
            print("project button find fail !!!")
        else:
            bs_object = BeautifulSoup(self.chrome_driver.page_source, "html.parser")
            self.html_parser(bs_object=bs_object)

    def html_parser(self, bs_object):

        try:
            proj_list_box = bs_object.select_one("div.project-list-box")
        except:
            print("list-box access fail !!")
            exit(1)

        try:
            proj_info_box = proj_list_box.select("div.project-info-box")
        except:
            print("info box access fail !!")
            exit(1)

        for c, i in enumerate(proj_info_box):

            try:
                proj_title = i.select_one("div.project-unit-heading > "
                                          "h4.project-title > "
                                          "a.subtitle-2-medium.project-link")
            except:
                print("subtitle-2-medium.project-link access fail !!")
                exit(1)

            try:
                proj_unit_body = i.select_one("div.project-unit-body > section.project-unit-info")
            except:
                print("section.project-unit-info access fail !!")
                exit(1)

            ##====================================================================
            try:
                ## estimated-box
                estimated_box = proj_unit_body.select_one("div.estimated-box")
            except:
                print("estimated-box access fail")
                exit(1)

            try:
                estimated_price = estimated_box.select_one("p.body-2-medium.estimated.estimated-price > "
                                                            "span.estimated-data")
            except:
                print("estimated-data access fail !!")
                exit(1)

            try:
                estimated_term  = estimated_box.select_one("p.body-2-medium.estimated.estimated-term > "
                                                            "span.estimated-data")
            except:
                print("estimated-data access fail !!")
                exit(1)

            ##====================================================================
            try:
                proj_description = proj_unit_body.select_one("div.body-3.project-description")
            except:
                print("body-3.project-description access fail !!")
                exit(1)

            self.action.append({
                    "_index" : self.es_index,
                    "_source":{
                        "title"           : proj_title.string,
                        "estimated_amount": int(str(estimated_price.string).replace(",", "").rstrip("원")),
                        "estimated_term"  : int(str(estimated_term.string).rstrip("일")),
                        "proj_description": str(proj_description.string).lstrip("프로젝트 개요 : "),
                        "collect_time"    : self.collect_time
                }
            })

            if c !=0 and c%2==0:
                self.document_bulk_insert()
                self.action.clear()

        if not self.action:
            self.document_bulk_insert()

    def document_bulk_insert(self):

        try:
            response = helpers.bulk(self.es_client, actions=self.action)
        except:
            print("elastic bulk insert fail")
        else:
            print(response)

    @classmethod
    def get_url(cls):
        wishket_path = "./Config/wishket_url.yml"
        result = os.path.isfile(path= wishket_path)
        if result:
            with open(wishket_path, "r", encoding="utf-8") as fr:
                wishket_infor = yaml.safe_load(fr)
                fr.close()
                return wishket_infor
        else:
            exit(1)

    @classmethod
    def secret_data_get(cls):
        secret_path = "./Config/secret_info.json"
        result = os.path.isfile(path=secret_path)
        if result:
            with open(secret_path, "r", encoding="utf-8") as fr:
                json_data = json.load(fr)
                fr.close()
                return json_data
        else:
            exit(1)

    def __del__(self):
        try:
            self.chrome_driver.close()
        except:
            pass
        else:
            print("chrome driver close !!")


if __name__ == "__main__":
    start_time = time.time()
    #============================================

    obj = GetData()
    obj.do_login()

    result = "{:.2f} sec".format(time.time() - start_time)
    print(result)