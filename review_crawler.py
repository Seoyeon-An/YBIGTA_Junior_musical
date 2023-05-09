from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
import pandas as pd
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import re

class review_crawler:
    
    # input: driver path, url path
    def __init__(self, musical_title, url, closebutton, reviewbutton, num_best_review, more_xpath, next_page_xpath, ten_to_eleven_xpath, next_ten_pages_xpath, driverpath = None):
        self.musical_title = musical_title
        self.url = url
        self.closebutton = closebutton
        self.reviewbutton = reviewbutton
        self.num_best_review = num_best_review
        self.more_xpath = more_xpath
        self.next_page_xpath = next_page_xpath
        self.ten_to_eleven_xpath = ten_to_eleven_xpath
        self.next_ten_pages_xpath = next_ten_pages_xpath
        if driverpath == None:
            self.driver = webdriver.Chrome()
        else:
            self.driver = webdriver.Chrome(driverpath)
        
    def set(self):
        
        self.driver.get(self.url)

        try:
            close = self.driver.find_element(By.XPATH, self.closebutton)
            close.click()
        except:
            pass
        
        review = self.driver.find_element(By.XPATH, self.reviewbutton)
        review.click()
        
    def crawl_fc(self):
    
        columns = ['rate', 'review_title', 'review_text', 'review_date']
        values = []
        soup = BeautifulSoup(self.driver.page_source, 'lxml')

        data_rows = soup.find_all('li', attrs={'class':'bbsItem'})[self.num_best_review:] # best review 중복 집계 막기 위해 처음 n개 제외
        for row in data_rows:
            blank = []
            rate = row.find('div', attrs={'class':'prdStarIcon'})
            if rate:
                rate = rate['data-star'].strip()
                blank.append(rate)
            else:
                #print("<평점 없는 리뷰 제외합니다>")
                continue
            
            review_title = row.find('strong', attrs={'class':'bbsTitleText'})
            if review_title:
                review_title = review_title.get_text()
                blank.append(review_title)
            else:
                #print("<리뷰제목 없는 리뷰 제외합니다>")
                continue

            review_text = row.find('p', attrs={'class':'bbsText'})
            if review_text:
                review_text = review_text.get_text().strip()
                review_text = review_text.replace('\r', ' ') #줄바꿈 \r 표시 공백으로 변환
                blank.append(review_text)
            else:
                #print("<리뷰내용 없는 리뷰 제외합니다>")
                continue
            
            date = row.find_all('li', attrs={'class':'bbsItemInfoList'})[1]
            if date:
                date = date.get_text()
                blank.append(date)
            else:
                #print("<작성날짜 없는 리뷰 제외합니다>")
                continue
            
            values.append(blank)
            
        df = pd.DataFrame(values, columns = columns)
        df['musical_title'] = self.musical_title
        df = df[['musical_title', 'rate', 'review_title', 'review_text', 'review_date']]
        
        return df
    
    def do(self, timesleep):
        
        self.set()
        
        time.sleep(timesleep)
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        total_num = int(soup.find('span', {'class': 'num'}).get_text())
        num_page = total_num//15
        
        review_list = []

        # general case
        for k in range((num_page//10)+1):
            try:
                # 첫 번째 페이지 크롤링
                time.sleep(timesleep)
                print(k*10+1)
                for j in range(15):
                    more = self.driver.find_element(By.XPATH, self.more_xpath.format(j+1))
                    more.click()
                
                review_list.append(self.crawl_fc())
                
                # 2~10번째 페이지 크롤링
                for i in range(2, 11):
                    print(k*10+i, '/', num_page)
                    next_page = self.driver.find_element(By.XPATH, self.next_page_xpath.format(i))
                    next_page.click()
                    time.sleep(timesleep)
                    
                    for j in range(15):
                        try:                    
                            more = self.driver.find_element(By.XPATH, self.more_xpath.format(j+1))
                            more.click()
                        except:
                            pass
                    
                    review_list.append(self.crawl_fc())

                # 다음 열 개 페이지 로딩
                # 그런데 1-10에서 11-20으로 넘어가는 것만 좀 case가 달라서 따로 처리해줌
                if k == 0:
                    next_ten = self.driver.find_element(By.XPATH, self.ten_to_eleven_xpath)
                    next_ten.click()
                    time.sleep(timesleep)
                else:
                    next_ten = self.driver.find_element(By.XPATH, self.next_ten_pages_xpath)
                    next_ten.click()
                    time.sleep(timesleep+2)
                
            except:
                pass
             
        result = pd.concat(review_list).reset_index(drop=True) # index 초기화 해줘야함
        if len(result) == total_num:
            print('crawler worked succesfully!')
        else:
            print('Something is wrong with crawler...')
        
        return result
