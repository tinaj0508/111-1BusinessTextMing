from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *

from flask import Flask, request, abort
from pyquery import PyQuery as pq
from pypinyin import pinyin, lazy_pinyin, Style
from bs4 import BeautifulSoup 
import requests 
import os 
from time import sleep 
import re
import pandas as pd

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
 
####################################################

#隨機抽餐廳
def Random():
    table_MN = pd.read_html('https://github.com/tinaj0508/2023_reataurant2/blob/main2/README1.md')
    df = table_MN[0]
    df.columns = df.iloc[0]
    data = df[ df["num"]!="num"]
    output = data.sample()
    d = "餐廳名稱："+list(output["resname"])[0]
    e = "餐廳價位："+list(output["price"])[0]
    t = "地點："+list(output["MRTStation"])[0]+"捷運站附近"
    x = "餐廳種類："+list(output["restype"])[0]
    f = "兩年內餐廳星等平均值："+list(output["recstar"])[0]
    g = "兩年內餐廳星等標準差："+list(output["sd"])[0]

    #畫星等比例圖
    s0 = "接下來看看各個星等分布比例"
    s1 = "1星"+str(float(output["r1"]))+"  \n2星"+str(float(output["r2"]))+"  \n3星"+str(float(output["r3"]))+"  \n4星"+str(float(output["r4"]))+"  \n5星"+str(float(output["r5"]))


    #情緒分析結果
    a = "網友最在意這家餐廳的："+list(output["tenword"])[0][2:-2]
    b = "隨機一句好評："+list(output["good"])[0]
    c = "隨機一句負評："+list(output["bad"])[0]
    all = "◾"+t+"\n\n◾"+x+"\n\n◾"+d+"\n\n◾"+e+"\n\n◾"+f+"\n\n◾"+g+"\n\n◾"+s0+"\n◾"+s1+"\n\n◾"+a+"\n\n◾"+b+"\n\n◾"+c

    return all



#餐廳推薦

def Gen(i):
    table_MN = pd.read_html('https://github.com/tinaj0508/2023_reataurant2/blob/main2/README1.md')
    df = table_MN[0]
    df.columns = df.iloc[0]
    data = df[ df["num"]!="num"]
    i = i.split(" ")
    imrt = i[0]
    mrt = []
    for key, value in data.groupby(data["MRTStation"]):
        mrt.append(key)
    if imrt not in mrt:
        t = "無此捷運站，請重新輸入"
        return t
    else:
        t = "您輸入的是："+imrt+"捷運站"


        
        output = data[data["price"] == i[1]]
        output = output[output["MRTStation"] == imrt]
        output = output[output["restype"] == i[2]]
        if len(output["resname"]) > 1:
            output = output.sample()

        if len(output["resname"]) == 0:
            t = "糟糕!"+imrt+"捷運站附近500公尺，查無這種餐廳。請重新輸入。"

            return t

        else:
            d = "餐廳名稱："+list(output["resname"])[0]
            e = "餐廳價位："+i[1]
            f = "兩年內餐廳星等平均值："+list(output["recstar"])[0]
            g = "兩年內餐廳星等標準差："+list(output["sd"])[0]

            #畫星等比例圖
            s0 = "接下來看看各個星等分布比例"
            s1 = "1星"+str(float(output["r1"]))+"  \n2星"+str(float(output["r2"]))+"  \n3星"+str(float(output["r3"]))+"  \n4星"+str(float(output["r4"]))+"  \n5星"+str(float(output["r5"]))


            #情緒分析結果
            a = "網友最在意這家餐廳的："+list(output["tenword"])[0][2:-2]
            b = "隨機一句好評："+list(output["good"])[0]
            c = "隨機一句負評："+list(output["bad"])[0]
            all = "◾"+t+"\n\n◾"+d+"\n\n◾"+e+"\n\n◾"+f+"\n\n◾"+g+"\n\n◾"+s0+"\n◾"+s1+"\n\n◾"+a+"\n\n◾"+b+"\n\n◾"+c

            return all





##############其他#################

#百度搜尋
def Baidu(text):

    fuck=[]
    url = f'https://baike.baidu.com/item/{text}'
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}  #掛header，要把header改成自己電腦的（防止反爬蟲阻礙我們搞事情） 
    url_get = requests.get(url,headers = header) 
    url_decode = url_get.content.decode("utf-8","ignore").encode("gb2312","ignore") 
    url_soup = BeautifulSoup(url_decode,'html.parser') 

    #本來可以抓的更精確，但百度網頁很多都長得不太一樣，所以抓稍微籠統一點的文字
    url_meta = url_soup.find_all( attrs={'class':'para'}) 

    for title in url_meta:
        fuck.append(title.getText())
    fuck = "\n".join(fuck)
    fuck = re.sub("\[.{0,5}\]"," ",fuck) #把一些註解啥的給清掉
    fuck = re.sub("\n\n\n"," ",fuck)

    #沒有用到模糊搜尋的功能，所以搜不到網頁也會呈現搜不到
    if len(fuck) == 0 :                     
      fuck = "抱歉，百度百科尚未收录词条"+text

    #linebot測試發現，爬下來字太多無法呈現，所以直接限定字數(字太多在手機也很難閱讀)
    if len(fuck) > 2000: 
        fuck = fuck[0:2000]+"\n更多內容請看：\n"+url

    return fuck

#中文字轉漢語拼音
def PinYin(text):
    
    e = lazy_pinyin(text, v_to_u=True)   #有設定不要有聲調符號(配合我自己使用的需求)

    #如果輸入兩個字
    if len(e) == 2: 
        pin = e[0][0].upper()+e[0][1:],e[1][0].upper()+e[1][1:]
        #print(pin)

    #如果輸入三個字
    elif len(e)  == 3:
        pin = e[0][0].upper()+e[0][1:],e[1][0].upper()+e[1][1:]+e[2]
        #print(pin)

    #如果輸入不是兩個字或三個字
    else:
        pin = e
        #print(pin)
    pin = ' '.join(pin)
    return pin


#爬中央社新聞(最新的一筆)
def cnaNews():
    res = requests.get("https://www.cna.com.tw/list/aall.aspx")
    mainPageDoc = pq(res.text)
    title = mainPageDoc("#jsMainList > li:nth-child(1) > a > div > h2 > span")
    time = mainPageDoc("#jsMainList > li:nth-child(1) > a > div > div")
    dataList = mainPageDoc("#jsMainList > li:nth-child(1) > a")
    cateRes = requests.get(dataList.attr("href"))
    B = title.text()+"   "+time.text()+"   "+cateRes.url
    return B


#爬udn大陸新聞(五筆)
def udnChina():
    res = requests.get("https://udn.com/news/cate/2/6640")
    mainPageDoc = pq(res.text)
    artDict = {"Title": [], "Link": []}
    data = mainPageDoc(".story-list__text > h3 > a")
    num = 0
    for each in data.items():
        artDict["Title"].append(each.text())
        print(each.text())
        cateRes = requests.get("https://udn.com{}".format(each.attr("href")))
        artDict["Link"].append(cateRes.url)
        print(cateRes.url)
        num += 1
        if num == 5:
            break
    I2 = []
    for i in range(len(artDict["Link"])):
        I1 = artDict["Title"][i]+" "+artDict["Link"][i]
        I2.append(I1)
    I = I2[0]+"  "+I2[1]+"  "+I2[2]+"  "+I2[3]+"  "+I2[4]

    return I

#爬中新網新聞(五筆)
def crnttChina():
    res = requests.get(
        "http://hk.crntt.com/crn-webapp/coluOutline.jsp?coluid=151")
    mainPageDoc = pq(res.text)
    artDict = {"Title": [], "Time": [], "Link": []}
    data = mainPageDoc("li > a")
    num = 0
    num2 = 0
    for a in mainPageDoc(" li > font > em"):
        artDict["Time"].append(a.text)
        print(a.text)
        num += 1
        if num == 5:
            break
    for each in data.items():
        artDict["Title"].append(each.text())
        print(each.text())
        cateRes = requests.get(
            "http://hk.crntt.com{}".format(each.attr("href")))
        artDict["Link"].append(cateRes.url)
        print(cateRes.url)
        num2 += 1
        if num2 == 5:
            break
    J2 = []
    for i in range(len(artDict["Link"])):
        J1 = artDict["Title"][i]+" "+artDict["Time"][i]+"  "+artDict["Link"][i]
        J2.append(J1)
    J = J2[0]+"  "+J2[1]+"  "+J2[2]+"  "+J2[3]+"  "+J2[4]

    return J



###############################################



@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        

        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()



        for event in events:
            #如果是文字訊息才動，這樣傳圖片到linebot就不會理人了
            if isinstance(event, MessageEvent):  
                input_text = event.message.text
                
                #無聊的彩蛋訊息
                if input_text == '領袖好':
                    line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text='您好，我是江泽民，我并没有死，我因为私下支持白纸革命，被习近平软禁在中南海，通过贿赂保安，建立这支LineBot传递讯息给你，还差五千人民币就可以买通看守放我从密道出来，我的帐户是19890604，待革命事成之后，保证让你当上台湾岛岛主。'))
                elif input_text == '餐廳種類介紹':
                    Buttons_template = TemplateSendMessage(
                        alt_text='Buttons template',
                        template=ButtonsTemplate(
                            thumbnail_image_url='https://img.icons8.com/fluency/512/hamburger.png',
                            title='餐廳說明',
                            text='搜尋之前，先了解我們提供哪些種類吧~',
                            actions=[
                                
                                PostbackTemplateAction(
                                    label='捷運站',
                                    text='捷運站',
                                    data='捷運站'
                                ),                                    
                                PostbackTemplateAction(
                                    label='價位選擇',
                                    text='價位選擇',
                                    data='價位選擇'
                                ),                                    
                                PostbackTemplateAction(
                                    label='食物種類',
                                    text='食物種類',
                                    data='食物種類'
                                ),
                                PostbackTemplateAction(
                                    label='如何查餐廳',
                                    text='如何查餐廳',
                                    data='如何查餐廳'
                                )
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, Buttons_template)
                elif input_text == '捷運站':
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text="[中山國中\中正紀念堂\信義安和\內湖\六張犁\劍潭\南京復興\南港展覽館\南港軟體園區\台北101/世貿\台北車站\台大醫院\唭哩岸\大安\大安森林公園\大湖公園\大直\忠孝復興\文德\東湖\東門\松山機場\港墘\石牌\科技大樓\竹圍\萬芳醫院\葫洲\西湖\象山\麟光]"))

                elif input_text == '價位選擇':
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text="$/$$/$$$/$$$$"))

                elif input_text == '食物種類':
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text="American/Chinese/Indian/Italian/Japanese/Mexican/Pizza/Bar/Steak/Cafe/Hot Pot/Seafood/Others/居酒屋/燒烤/韓式料理/餐酒館/歐風餐廳/東南亞餐廳/素食餐廳"))
                elif input_text == '如何查餐廳':
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text="請以「吃 」開頭，輸入您所在的捷運站、期待價位與餐廳種類。\n以空格分割\n捷運站名不可加「站」字\n例如：\n吃 大安 $$ Chinese"))

                elif input_text[0] == "吃": #偵測到第一個字
                    text = input_text[2:] #取第三個字以後
                    BD = Gen(text)
                    line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=BD))

                elif input_text == "隨便吃~~~~": 
                    RD = Random()
                    line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=RD))




##########################################

                #連結上面爬的三家新聞網站，做一個新聞的按鈕
                elif input_text == '新聞':
                    Buttons_template = TemplateSendMessage(
                        alt_text='Buttons template',
                        template=ButtonsTemplate(
                            thumbnail_image_url='https://cdn-icons-png.flaticon.com/512/2965/2965879.png',
                            title='新聞',
                            text='喵',
                            actions=[
                                
                                PostbackTemplateAction(
                                    label='中央社',
                                    text='中央社',
                                    data='中央社'
                                ),                                    
                                PostbackTemplateAction(
                                    label='中新社',
                                    text='中新社',
                                    data='中新社'
                                ),                                    
                                PostbackTemplateAction(
                                    label='udn',
                                    text='udn',
                                    data='udn'
                                )
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, Buttons_template)


                elif input_text == '中新社':
                    crntt = crnttChina()
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text=crntt))

                elif input_text == '中央社':
                    Third = cnaNews()
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text=Third))

                elif input_text == 'udn':
                    china2 = udnChina()
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text=china2))


                #生活小工具的按鈕，存放一些用來更新的程式碼，未來有機會再加入其他功能
                elif input_text == '生活小工具':
                    Buttons_template = TemplateSendMessage(
                        alt_text='Buttons template',
                        template=ButtonsTemplate(
                            thumbnail_image_url='https://cdn-icons-png.flaticon.com/512/4873/4873868.png',
                            title='工具人在此',
                            text='主人需要什麼服務',
                            actions=[
                                PostbackTemplateAction(
                                    label='程式碼',
                                    text='程式碼',
                                    data='程式碼'
                                )
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, Buttons_template)

                #漢拚轉換功能，點下去可以告訴使用者要怎麼使用
                elif input_text == '漢拚轉換':
                    line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text='在開頭輸入轉，例如:轉習近平'))

                #百度搜尋功能，點下去可以告訴使用者要怎麼使用
                elif input_text == '百度搜尋':
                    line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text='在開頭輸入百，例如:百習近平'))
                
                #漢拚轉換
                elif input_text[0] == "轉":  #偵測到第一個字
                    text = input_text[1:]  #取第二個字以後
                    PY = PinYin(text)
                    line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=PY))

                #百度搜尋
                elif input_text[0] == "百": #偵測到第一個字
                    text = input_text[1:] #取第二個字以後
                    BD = Baidu(text)
                    line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=BD))



                #生活小工具中的程式碼儲存區
                elif input_text == '程式碼':
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(
                        text='cd LineBot\liyuenv\Scripts\LineBotNLP \n python manage.py makemigrations \n python manage.py migrate \n python manage.py runserver'))

                #如果有輸入的文字不符合上述格式，就會出現這個
                else:
                    message = TextSendMessage(text='請輸入正確關鍵字')
                    line_bot_api.reply_message(event.reply_token, message)

 
