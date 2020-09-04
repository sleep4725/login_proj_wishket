from selenium import webdriver

class RetChromeDriver:

    ## 프로그램 상수__________________
    chrome_dirver_path = "C:\\Users\\EZFARM\\PycharmProjects\\login_proj_wishket\\Config\\chromedriver.exe"

    ## headless 형태의 instance를 return
    @classmethod
    def get_chrome_instance(cls):
        chrome_option = webdriver.ChromeOptions()
        chrome_option.add_argument("headless")
        chrome_option.add_argument("window-size=1920x1080")
        chrome_option.add_argument("disable-gpu")


        chrome_driver = webdriver.Chrome(executable_path= RetChromeDriver.chrome_dirver_path, chrome_options= chrome_option)
        chrome_driver.implicitly_wait(3)

        return chrome_driver