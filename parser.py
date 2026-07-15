from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re



def parse_chapter(html, url) -> tuple[str, str, str, ] | None:    # 依旧十分清晰.jpg
    parse = BeautifulSoup(html, "html.parser")
    title = ''
    content = ''
    next_url = ''


    # 提取标题（用正则表达式匹配“第X章”，个人不太喜欢用标签匹配）
    title_pattern = re.compile(r"^第[一二三四五六七八九十\d]+章")     # 限定为开头
    possible_titles = parse.find_all(string=title_pattern)    # 直接使用表达式匹配
    for t in possible_titles:
        print(f"获取到标题:{t}!", end= " ")
        if "_" not in t:        # 过滤可能带有广告的标题
            print("——适合的标题！")
            title = t
            break
        else:
            print("——标题可能受污染")
            continue

    if not title:
        print("未找到合适的标题，使用默认h1标签")
        title = parse.select_one("h1")
        if not title:
            print("匹配失败")
            return None



    # 提取正文（通过字数检测为正文）
    divs = []
    for div in parse.find_all("div"):   # 全文查找<div>标签（应该不会有缺德的不放在<div>里吧？），虽然效率低但是简单……
        if not div.find("div"):     # 只要叶子<div>容器
            if div.find_all("p") or div.find_all("br"):     # 检测是否有换行（或许会有缺德的没有，那没招）
                divs.append(div)
    print(f"共{len(divs)}个可能的div标签")

    result_list = []
    for div in divs:
        for br in div.find_all("br"):
            br.replace_with("\n")
        text = div.get_text(separator = '\n', strip = True)

        if len(text) > 400:
            result_list.append(text)

    print(f"过滤出{len(result_list)}个匹配正文！")

    if result_list:
        content = result_list[0]
        print("已默认选用第一个")
    else:
        print("寻找失败，启用第二方案")
        del text, divs, result_list
        CONTENT_SELECORS = \
            ['#content', '.content', '#chaptercontent', '.chapter-content',
             '.read-content', 'article', '#txtContent']  # 常见的正文容器，当然还有不常见的……

        for selector in CONTENT_SELECORS:
            text_div = parse.select_one(selector)
            if text_div:
                for br in text_div.find_all('br'):
                    br.replace_with('\n')
                text = text_div.get_text(separator='\n', strip=True)
                if len(text) > 50:
                    content = text
                    break

        if not content:
            print("寻找失败")
            return None
        print("成功找到正文")





    # 获取下一页url（匹配链接）
    next_pattern = re.compile(r'下一[章页]', re.IGNORECASE)
    next_tag = parse.find('a', string=next_pattern)
    if next_tag and next_tag.get("href"):
        next_url = urljoin(url, next_tag["href"])
        print("已找到下一页链接" + next_url)
    else:
        print("未查找到下一页链接！")

    return title, content, next_url



if __name__ == "__main__":
    with open("test/样例HTML.html", 'r', encoding = 'utf-8') as f:
        html = f.read()
    url = "https://www.erciyan.com/book/94536315/236731807.html"
    parse_chapter(html, url)