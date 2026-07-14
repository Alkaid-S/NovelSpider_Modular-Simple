import requests
import time


headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

def fetch_html(url) -> str | None:  # 其实不用这么写，但是似乎更清晰一点……
    for attempt in range(1,4):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()

            if resp.encoding and resp.encoding.lower() != "utf-8":  # 优先用网站自己的
                pass
            else:
                resp.encoding = resp.apparent_encoding  # 猜！

            return resp.text
        except requests.RequestException as e:
            print(f"第{attempt}次尝试出现错误：{e}")
            if attempt < 3:
                time.sleep(2.0)
            else:
                return None

# 添加一个测试的程序
if __name__ == "__main__":
    url = "https://www.erciyan.com/book/94536315/236731807.html" # 不好，店长又双叒叕捡回来兽耳娘啦
    html_text = fetch_html(url)
    if html_text:
        print('获取到了文本，内容如下')
        print(f"{html_text}")
    else:
        print("未获取到文本，请检查url或者网络连接")
