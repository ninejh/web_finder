from selenium import webdriver
from flask import Flask, render_template, request
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup 
import requests
from konlpy.tag import Okt
from wordcloud import WordCloud
import pandas as pd
import os


okt= Okt()
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)

def google_news(keyword):
    title_keyword=[]
    '''=======================구글======================='''
    url="https://news.google.com/topstories?hl=ko&gl=KR&ceid=KR:ko"
    driver.get(url)
    elem = driver.find_element_by_xpath("//*[@id='gb']/div[2]/div[2]/div/form/div[1]/div/div/div/div/div[1]/input[2]")
    elem.clear()
    elem.send_keys(keyword) #키워드를 구글 뉴스에 입력 
    elem.send_keys(Keys.ENTER) 
    '''웹 스크래핑 중'''
    url = driver.current_url
    res = requests.get(url)
    res.raise_for_status()
    soup=BeautifulSoup(res.text,'lxml')
    titles = soup.find_all("h3", attrs={"class":"ipQwMb ekueJc RD0gLb"})
    for title in titles:
        news_title = title.find("a").get_text()
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        title_keyword.append(news_title)
    return title_keyword
        
def daum_news(keyword,title_keyword):
    '''=======================다음======================='''
    for i in range(1,9,1):
        url=(f"https://search.daum.net/search?nil_suggest=btn&w=news&DA=PGD&q={keyword}&p={i}")
        driver.get(url)
        '''웹 스크래핑 중'''
        url = driver.current_url
        res = requests.get(url)
        res.raise_for_status()
        soup=BeautifulSoup(res.text, 'lxml')
        titles = soup.find_all("div", attrs={"class":"wrap_cont"})
        for title in titles:
            news_title = title.find("a").get_text()
            title_keyword.append(news_title)
    return title_keyword
            
def naver_news(keyword,title_keyword):
    '''======================네이버======================='''
    for i in range(1,91,10):
        url=(f"https://search.naver.com/search.naver?where=news&sm=tab_pge&query={keyword}&sort=0&photo=0&field=0&pd=0&ds=&de=&cluster_rank=0&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so:r,p:all,a:all&start={i})")
        driver.get(url)
        '''웹 스크래핑 중'''
        url = driver.current_url
        res = requests.get(url)
        res.raise_for_status()
        soup=BeautifulSoup(res.text, 'lxml')
        titles= soup.find_all("a",attrs={"class":"news_tit"})
        for title in titles:
            news_title = title.get_text()
            title_keyword.append(news_title)
    return title_keyword
            
def delete_same(title_keyword):
    #중복제거
    global cnt #전역변수
    cnt = 0
    new_title_keyword=[]
    for i in title_keyword:
        if i not in new_title_keyword:
            new_title_keyword.append(i)
            cnt+=1
    
    return new_title_keyword

def find_noun(new_title_keyword):
    #리스트 합치고 단어 찾기(전치사 제거)
    Str_new_title_keyword=" ".join(new_title_keyword) #string형태
    main_keyword=okt.nouns(Str_new_title_keyword) #리스트 형태

    return main_keyword 

def user_keyword(keyword):
    #유저 검색 키워드 단어 나누기
    noun_user_keyword=okt.nouns(keyword) #리스트 형태

    return noun_user_keyword 

def delete_small(main_keyword):
    #2자리 이상 단어
    for i,v in enumerate(main_keyword):
        if len(v) < 2:
            main_keyword.pop(i)

    return main_keyword

# def delete_user_keyword(noun_user_keyword,main_keyword):
#     #유저 검색 키워드와 뉴스 키워드 비교 및 제거
#     for i in range(0,len(noun_user_keyword),1):
#         for j,v in enumerate(main_keyword):
#             if noun_user_keyword[i] == v:
#                 main_keyword.pop(j)
#     Str_main_keyword=" ".join(main_keyword)
    
#     return Str_main_keyword


def delete_user_keyword_for_counter(noun_user_keyword,main_keyword):
    #유저 검색 키워드와 뉴스 키워드 비교 및 제거
    for i in range(0,len(noun_user_keyword),1):
        for j,v in enumerate(main_keyword):
            if noun_user_keyword[i] == v:
                main_keyword.pop(j)
    return main_keyword

# os.remove오류로 인해 사용 불가
# def wordcloud_keyword(Str_main_keyword):
#     wc = WordCloud(
#         font_path="/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
#         background_color = 'white',
#         height = 600,
#         width = 1000,
#         max_font_size = 110
#     )
#     wc.generate(Str_main_keyword)
#     wc.to_file("./static/image/result1.png")
    
def count_keyword(main_keyword):
    #글자 수 세기
    col_name=['keyword']
    cnt_df=pd.DataFrame(main_keyword,columns=col_name)
    #가장 많이 언급된 30단어
    cnt_df=cnt_df['keyword'].value_counts()[:30].index.tolist()
    return cnt_df
    
app = Flask(__name__)

@app.route('/')
def home():
   return render_template('home.html')

@app.route('/result',methods = ['POST', 'GET'])
def result():
   if request.method == 'POST':
      keyword = request.form['keyword']
      if os.path.exists('./static/image/result1.png'):
          os.remove('./static/image/result1.png')
      title_keyword=google_news(keyword)
      title_keyword=naver_news(keyword,title_keyword)
      title_keyword=daum_news(keyword,title_keyword)
      new_title_keyword=delete_same(title_keyword)
      main_keyword=find_noun(new_title_keyword)
      noun_user_keyword=user_keyword(keyword)
      main_keyword=delete_small(main_keyword)
    #   Str_main_keyword=delete_user_keyword(noun_user_keyword, main_keyword)
      main_keyword=delete_user_keyword_for_counter(noun_user_keyword, main_keyword)
      cnt_df=count_keyword(main_keyword)
    #   wordcloud_keyword(Str_main_keyword)          
      value1=cnt_df[0]
      value2=cnt_df[1]
      value3=cnt_df[2]
      value4=cnt_df[3]
      value5=cnt_df[4]
      value6=cnt_df[5]
      value7=cnt_df[6]
      value8=cnt_df[7]
      value9=cnt_df[8]
      value10=cnt_df[9]
      value11=cnt_df[10]
      value12=cnt_df[11]
      value13=cnt_df[12]
      value14=cnt_df[13]
      value15=cnt_df[14]
      value16=cnt_df[15]
      value17=cnt_df[16]
      value18=cnt_df[17]
      value19=cnt_df[18]
      value20=cnt_df[19]
      value21=cnt_df[20]
      value22=cnt_df[21]
      value23=cnt_df[22]
      value24=cnt_df[23]
      value25=cnt_df[24]
      value26=cnt_df[25]
      value27=cnt_df[26]
      value28=cnt_df[27]
      value29=cnt_df[28]
      value30=cnt_df[29]
      return render_template("result.html",keyword=keyword, cnt = cnt, value1 = value1, value2 = value2, value3 = value3, value4 = value4, value5 = value5, value6 = value6, value7 = value7, value8 = value8, value9 = value9, value10 = value10, value11 = value11, value12 = value12, value13 = value13, value14 = value14, value15 = value15, value16 = value16, value17 = value17, value18 = value18, value19 = value19 ,value20 = value20, value21 = value21, value22 = value22, value23 = value23, value24 = value24, value25 = value25, value26 = value26, value27 = value27, value28 = value28, value29 = value29 ,value30 = value30)
      

if __name__ == '__main__':
   app.run(host='0.0.0.0',port=80 ,debug = True)