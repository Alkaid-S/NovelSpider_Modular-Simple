import time
import re
import os
from ebooklib import epub

def safe_name(name):    # 其实原本没有这个方法，但是突然发现用了三遍相同的代码……就啊哈
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip(". ")
    return name[:50]


def save_page_txt(out_dir:str, index:int, page_title:str, page_content:str) -> str: # 所有方法中out_dir都是“自定义位置/小说名"
    safe_page_title = safe_name(page_title)  # 太长了就去掉

    save_pages_dir = os.path.join(out_dir, "pages")
    os.makedirs(save_pages_dir, exist_ok = True)    # exist_ok = True，这样如果目录存在不会报错

    file_name = f"{index:04d}_{safe_page_title}.txt"    # index:04d，可以保证输出为000X，自动补零
    save_page_path = os.path.join(save_pages_dir, file_name)

    with open(save_page_path, "w", encoding = 'utf-8') as f:
        f.write(page_content)

    return save_page_path

def merge_all_txt(out_dir:str, novel_name:str) -> str:  # 保存为.txt文件
    read_pages_dir = os.path.join(out_dir, "pages")
    read_files = [f for f in os.listdir(read_pages_dir) if f.endswith('.txt')]    # 阅读目录下.txt文件
    read_files.sort()    # 按序号排序

    safe_novel_name = safe_name(novel_name)
    save_novel_path = os.path.join(out_dir, f"{safe_novel_name}.txt")

    with open(save_novel_path, "w", encoding = "utf-8") as out:
        for index, read_file_name in enumerate(read_files):     # 流式输入？
            read_file_path = os.path.join(read_pages_dir, read_file_name)
            with open(read_file_path, "r", encoding = "utf-8") as rd:
                content = rd.read()
                out.write(content)
                out.write("\n\n\n")
                if index == len(read_files)-1:
                    out.write("恭喜你读完本书——非正文\n")
                    out.write("北斗出品")       # 夹带私货.jpg

    return save_novel_path


def merge_all_epub(out_dir:str, novel_name:str) -> str:     # 保存为.epub，我很喜欢
    safe_novel_name = safe_name(novel_name)

    read_file_dir = os.path.join(out_dir, "pages")
    read_files = [f for f in os.listdir(read_file_dir) if f.endswith(".txt")]    # 读文件，成列表
    read_files.sort()

    # 建电子书
    book = epub.EpubBook()
    book.set_identifier(time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime()))   # 使用当前时间，肯定唯一就对了
    book.set_title(novel_name)
    book.set_language("zh-CN")

    # 加封面（依旧夹带私货）
    cover_html = f'''
    <html>
        <body>
            <h1 style="font-size: 2em; margin-bottom: 0.5em">{novel_name}</h1>
            <p style "color: #14C1FF">北斗出品</p>
        </body>
    </html>        
    '''
    # 感觉自己写的好规范啊（

    save_novel_cover_page = epub.EpubHtml(
        title='封面',
        file_name='cover.xhtml',
        lang='zh-CN'
    )
    save_novel_cover_page.content = cover_html
    book.add_item(save_novel_cover_page)

    # 逐个加章节
    epub_chapters = []
    for read_file_name in read_files:
        # 先获取章节名字
        file_name_base = read_file_name[:-4]
        file_name_parts = file_name_base.split("_", 1)
        read_chapter_index, read_chapter_title = file_name_parts  # 首先不要在C++里这么写，别问我怎么知道的
        read_chapter_index = int(read_chapter_index)

        # 尽情阅读（读取文件内容）
        read_file_path = os.path.join(read_file_dir, read_file_name)
        with open(read_file_path, "r", encoding = "utf-8") as rd:
            read_chapter_content = rd.read()

        # 构建章节
        epub_chapter_new = epub.EpubHtml(
            title=read_chapter_title,  # 目录显示的标题
            file_name=f'chap_{read_chapter_index:04d}.xhtml',  # epub文件名，得唯一
            lang='zh-CN'
        )
        html_body = f'<h2>{read_chapter_title}</h2>\n<p>{read_chapter_content.replace("\n", "<br/>")}</p>'
            # 把换行更改为<br/>换行符
        epub_chapter_new.content = html_body

        book.add_item(epub_chapter_new) # 加进去
        epub_chapters.append(epub_chapter_new)

    # 加目录等
    book.toc = epub_chapters
    book.spine = [save_novel_cover_page, 'nav'] + epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    # 这里就不夹带私货了，略微有点难其实

    # 简单改一下我喜欢的样式
    style = '''
        body { font-family: "宋体", serif; } 
        h2 { text-align: center; font-weight:bold}
        p { text-indent: 2em}
    '''
    css_item = epub.EpubItem(uid="style", file_name="style/default.css",
                                 media_type="text/css", content=style)
    book.add_item(css_item)

    # 出！
    save_novel_path = os.path.join(out_dir, f"{safe_novel_name}.epub")
    epub.write_epub(save_novel_path, book)

    return save_novel_path



if __name__ == "__main__":
    novel_name = "不好，店长又双叒叕捡回兽耳娘啦"
    out_dir = os.path.join("test", novel_name)

    chapters = [
        [1, "第1章 饿倒在店门前的猫耳少女", ""],
        [2, "第2章 只存在于幻想之中的生物", ""]
    ]
    with open("test/测试用小说文本/1.txt", "r", encoding= "utf-8") as f:
        chapters[0][2] = f.read()
    with open("test/测试用小说文本/2.txt", "r", encoding= "utf-8") as f:
        chapters[1][2] = f.read()

    print("测试保存分章")
    for index, title, content in chapters:
        print("已经保存至" + save_page_txt(out_dir ,index, title, content))

    print("测试合并文本为txt")
    print("已经保存至" + merge_all_txt(out_dir, novel_name))

    print("测试合并文本为epub")
    print("已经保存至" + merge_all_epub(out_dir, novel_name))

