# -*- coding: utf-8 -*-
"""
Created on Wed Jul 21 10:13:13 2021
Latest Update on May 9 2022
@author: wy
@user_now: chen yq
"""
# 20220509更新：改写为模块化的代码，添加打卡状态提醒推送
# 本程序旨在解决钉钉打卡问题，拟输出成程序并直接运行
# 目前考虑有两种路线，一种是Chromedriver模拟点击，一种是参看是否可用requests库解决
# 参考代码：https://github.com/lgaheilongzi/ZJU-Clock-In#readme
import requests
import re
import time
import datetime
import json
import ddddocr


def post_msg_wechat(send_key, title, bodys):
    # 向微信推送消息
    url = r'https://sctapi.ftqq.com/' + send_key + '.send'
    data = {
        'title': title,
        'desp': bodys
    }
    r = requests.post(url, data=data)


def get_code(session, headers):
    # 获取验证码
    url_code = 'https://healthreport.zju.edu.cn/ncov/wap/default/code'
    ocr = ddddocr.DdddOcr()
    # resp = session.get(url_code)
    resp = session.get(url_code, headers=headers)
    code = ocr.classification(resp.content)
    return code


def get_date():
    """Get current date"""
    today = datetime.date.today()
    return "%4d%02d%02d" % (today.year, today.month, today.day)


def deal_person(cookies, send_key):
    # 此函数是打卡功能的顶层函数，通过传入不同的cookies实现为多人打卡，
    url_save = 'https://healthreport.zju.edu.cn/ncov/wap/default/save'
    url_index = 'https://healthreport.zju.edu.cn/ncov/wap/default/index'

    # 给出headers和cookies，令其可以免登录
    # headers和cookies的确定方法为：
    # 1. Chrome打开无痕页面，键入url_save网址，返回登录界面
    # 2. 右键审查元素或者按F12，找到network栏
    # 3. 输入账号密码并登录，然后找到“index”的“requests headers”一栏
    # 4. 将cookie中的所有内容全部复制粘贴到cookies = ‘’中，用以完成请求头。
    headers = {
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36'}
    cookies_dict = {i.split("=")[0]: i.split("=")[-1] for i in cookies.split("; ")}

    # 获取session requests
    session = requests.Session()

    # 存储cookies信息到session中
    s_cookies_stored = requests.utils.add_dict_to_cookiejar(session.cookies, cookies_dict)

    r = session.get(url_index, headers=headers)
    html = r.content.decode()

    # 填表
    old_infos = re.findall(r'oldInfo: ({[^\n]+})', html)
    old_info = json.loads(old_infos[0])
    new_info_tmp = json.loads(re.findall(r'def = ({[^\n]+})', html)[0])
    new_id = new_info_tmp['id']
    name = re.findall(r'realname: "([^\"]+)",', html)[0]
    number = re.findall(r"number: '([^\']+)',", html)[0]

    new_info = old_info.copy()

    new_info['id'] = new_id
    new_info['name'] = name
    new_info['number'] = number
    new_info["date"] = get_date()
    new_info["created"] = round(time.time())
    new_info["address"] = "浙江省杭州市西湖区"
    new_info["area"] = "浙江省 杭州市 西湖区"
    new_info["province"] = new_info["area"].split(' ')[0]
    new_info["city"] = new_info["area"].split(' ')[1]
    new_info['jrdqtlqk[]'] = 0
    new_info['jrdqjcqk[]'] = 0
    new_info['sfsqhzjkk'] = 1
    new_info['sqhzjkkys'] = 1
    new_info['sfqrxxss'] = 1
    new_info['jcqzrq'] = ""
    new_info['gwszdd'] = ""
    new_info['szgjcs'] = ""

    Forms = new_info
    Forms['verifyCode'] = get_code(session, headers)

    # 获取回应
    respon = session.post(url_save, data=Forms, headers=headers).content
    print(respon.decode())
    result_str = respon.decode()
    if '操作成功' in result_str:
        post_msg_wechat(send_key, '打卡状态：今日打卡成功！', result_str)
    elif '已经填报' in result_str:
        #  post_msg_wechat(send_key, '打卡状态：今日打卡成功！', result_str)
        print('Successful!')
    else:
        post_msg_wechat(send_key, '打卡状态：出现异常，请检查！！！', result_str)


# 请参阅https://sct.ftqq.com 获取sendkey，以获得微信消息推送
# 警告：请不要直接运行此代码，【必须】先更新自己的sendkey之后再运行代码
cookies1 = 'BSFIT_uyktm=; _ga=GA1.3.2061622337.1650703105; BSFIT_i+yu4=; BSFIT_/l6Ai=; BSFIT_h8qzu=; lang=zh-CN; _ga_RSHERGT34X=GS1.1.1653658116.1.0.1653658118.0; Hm_lvt_fe30bbc1ee45421ec1679d1b8d8f8453=1663679994; _csrf=S8mwplVi9KWoF2WQ0TlCeH5Xng6IWZTdou6Nvj6EZcE%3D; _pv0=b5xtoyrkW9ztSNZtbgdiI%2FBbjrn9GSKqNBCrVH3rs33hVF8emQNLC6GW205oO%2BbDVpLfx1ZPtlRkLCFq4SVw2WPXMciXSa1pUjaybzZdFxE9VoVt0G9d%2BQAOzLG7m4Ook6CCv0SKTbTK8LR2PVy80JzUs75zL988KjEz6heuiJ2s244zmJdKx%2B4x9m%2F8v%2BTdAJ7VRyGEKyW7fWz3DdEDRk93PLP7tt%2FG%2FT7XRYcKp%…dULTUyNDg1NjQtekFncnlIdEE5SzJuWTlzRXFZM0FrWFY5cFAwdVJ2V0hya215NUR1QVFiWk80VGZVUk4temp1LmVkdS5jbiM2; eai-sess=65ftvrsr31aa7iaubc37ds9tq1; UUkey=24e09498e41c47596b8790ec9c152808; iPlanetDirectoryPro=zSc79gv2Ect1baq9pyNCqr9UB8%2FSgSvaIWYFpZrMT2ilsZeuRwIn2VmtA1vg7qEyw1pX%2FDGoje4W%2FWpHvzl7KcEfpE4dR7wvpM4ntCNbZFc4O8oieXnxb6tA4wzJR2WYbwzAAyhqs80R3vBD3jOGmehF9IX8Nj6oOIfXmRD%2BWiAVhn4o4Ez6MF5YhHKKqFSIKkVU04GvCE2aIIHW2dZQCBhdGnPy04hq9qQw5JAzrkFAmg36pvVyddfYzQyMrUQrJ5Ac%2Bs1Uzmq6SMPvVNVIuPnw4dKpfxp5aUlXA%2FdXJHY%3D'
SendKey1 = 'SCT182250TxiCj5PgkfqkjytoRyROmV1je'  # cen wj
deal_person(cookies=cookies1, send_key=SendKey1)


