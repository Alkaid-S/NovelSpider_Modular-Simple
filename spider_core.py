import time
import random
import os

from fetcher import fetch_html
from parser import parse_chapter
from storage import save_page_txt, merge_all_txt, merge_all_epub

class SpiderCore:
    def __init__(self,
                 start_url: str,            # 起始网址
                 novel_name: str,           # 小说名
                 max_chapters: int,         # 最大章节数（后面可能会更改，太过死板了，后面可以尝试从目录提取？）
                 output_dir: str,           # 输出目录
                 output_form: str,          # 输出小说的形式（txt/epub）
                 log_callback = None,       # 日志调动（从这往后的就可以不填了，但三个调动基本上还是要填的），通过外部方法输出日志
                 progress_callback = None,  # 进度调动，调动外部进度。
                 stop_callback = None,      # 停止标签调动，可以通过外部方法停止爬虫。
                 wait: bool = False,        # 等不等（默认不等，等的话太man！目前也没有做多线程爬虫。）
                 wait_max: float = 2.0,     # 等待区间值（话说Pycharm怎么说这段中文有语法问题）
                 wait_min: float = 0.0):
        self.start_url = start_url
        self.novel_name = novel_name
        self.max_chapters = max_chapters
        self.output_dir = os.path.join(output_dir, novel_name)  # 额，我相信你不会输入非法字符的
        self.output_form = output_form
        self.wait = wait
        self.wait_max = wait_max
        self.wait_min = wait_min
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.stop_callback = stop_callback
        # 累死我……
        # 以上方便后面的方法调用

        self._stop_flag = False  # 你好，我是一个停止标签！


    def _log_out(self, message, type: int = 1):
        # python 3.10以下没有switch case语句，那我就不用了
        if type == 1:
            msg_type = "INFO"
        elif type == 2:
            msg_type = "WARNING"
        elif type == 3:
            msg_type = "ERROR"
        else:
            msg_type = "UNKNOWN"

        if self.log_callback:
            self.log_callback(f"[{time.strftime('%H:%M:%S', time.localtime())}][{msg_type}]|{message}")  # 啊米诺斯
        else:
            print(f"[{time.strftime('%H:%M:%S', time.localtime())}][{msg_type}]|{message}")      # 就算没有外部方法我也得看不是


    def _progress_out(self, current_progress):
        if self.progress_callback:
            self.progress_callback(current_progress, self.max_chapters) # 到时候也得这么定义


    def _should_stop(self):     # 这里停止检测只在某些关键步骤执行，所以没有办法即点即停，后面可以在优化
        if self._stop_flag: # 停止标签
            return True
        elif self.stop_callback and self.stop_callback():   # 通过外部检测
            return True

        return False


    def stop(self):
        self._stop_flag = True


    def start_spider(self):
        # 开！
        self._log_out(f"开始爬虫，小说名称{self.novel_name}",1)
        self._log_out(f"爬虫内容以{self.output_form}格式输出到{self.output_dir}", 1)

        current_url = self.start_url

        for i in range(1, self.max_chapters+1):
            # 先检测是否停止
            if self._should_stop():
                self._log_out("收到停止信号，正在停止爬虫", 1)
                break

            self._progress_out(i)       # 更新进度
            self._log_out(f"正在爬取第{i}章：{current_url}", 1)

            html = fetch_html(current_url)
            if not html:
                self._log_out(f"爬取第{i}章时出错：无法获取到网页！", 3)
                self.stop()
                break
            page_title, page_content, next_url = parse_chapter(html, current_url)

            # 检测一下是否出现问题
            if not page_content:
                self._log_out(f"爬取第{i}章时出错：未获取到正文", 3)
                self.stop()
                break

            if not page_title:  # 这里在parser.py里面会直接返回none，这里就为了增加稳定性吧。
                self._log_out(f"爬取第{i}章时：未获取到标题", 2)
                page_title = f"第{i}章"

            try:
                path = save_page_txt(self.output_dir, i, page_title, page_content)
                self._log_out(f"第{i}章已经保存至{os.path.basename(path)}", 1)
            except Exception as e:
                self._log_out(f"爬取第{i}章时出错：保存失败，具体错误：{e}", 3)
                self.stop()
                break

            if not next_url:
                self._log_out("已无下一章，爬虫结束", 1)
                break

            current_url = next_url

            if self.wait:
                wait_time = random.uniform(self.wait_min, self.wait_max)
                self._log_out(f"等待{wait_time}秒后继续……")
                time.sleep(wait_time)

        self._log_out("爬虫已结束，正在处理文本信息", 1)
        if self._stop_flag:
            self._log_out("爬虫非正常结束，取消文本处理", 2)  # 没有人想要错乱的文件……吧
        else:
            try:
                if self.output_form == "txt":
                    self._log_out(f"生成小说全本成功，位置{merge_all_txt(self.output_dir, self.novel_name)}")
                elif self.output_form == "epub":
                    self._log_out(f"生成小说全本成功，位置{merge_all_epub(self.output_dir, self.novel_name)}")
                else:
                    self._log_out(f"错误的输出格式{self.output_form}，自动使用epub", 2)
                    merge_all_epub(self.output_dir, self.novel_name)
            except Exception as e:
                self._log_out(f"保存时小说时出错：{e}", 3)

        self._log_out("小说爬取完成", 1)
        self._progress_out(self.max_chapters)



if __name__ == "__main__":
    # 先不要log，看看自身的输出如何
    def progress(current, total):
        print(f"[进度] {current}/{total}")


    def should_stop():
        return False


    spider = SpiderCore(
        start_url= "https://www.erciyan.com/book/94536315/236731807.html",
        novel_name= "不好，店长又双叒叕捡回兽耳娘啦",
        max_chapters= 2,
        output_dir= "test/",
        output_form= "epub",
        log_callback= None,
        progress_callback= progress,
        stop_callback= should_stop,
        wait= False,
    )

    spider.start_spider()
