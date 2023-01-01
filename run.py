import BNU_session
import os
import schedule
import time

"""
usr:校园网账号
pwd:校园网密码

run_time:
    几点开始抢
    建议提前1-2min
    ie. 7:29

sport：
    羽毛球：1
    乒乓球：2
    网球：3
    
stime(范围8-21)：
    ie. 8-9点：8
    ...
    给起始时间
    
position(场地)：
    自己提前看看都有哪些
    然后给第几列
    
get_data:
    不进行最后一步的确认，只保存验证码为了模型训练  
"""

if not os.path.exists('./Valid_pic'):
    os.mkdir('./Valid_pic')

run_time = "7:29"

BNU = BNU_session.Session(
    usr='202221061068',
    pwd='',
    date="'2023-01-03'",
    sport=1,
    stime=16,
    position=1,
    get_data=False)

schedule.every().day.at(run_time).do(BNU.run)

while True:
    schedule.run_pending()
    time.sleep(1)



