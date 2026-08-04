import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os
import time
from spider_core import SpiderCore
from configurator import save_config, load_config, reset_config


class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("小说爬虫器 v.alpha.1")
        # 计算一下居中位置（强迫症……）
        window_width = 900
        window_height = 650
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)  # 禁止拖拽大小（这么大应该够了吧
        self.root.configure(bg='#DCDAD5')

        style = ttk.Style()
        style.theme_use("clam")

        self.is_running = False  # 是否在爬
        self.spider = None  # 后面作为SpiderCore的对象
        self.spider_thread = None  # 多线程对象
        self.config = load_config()  # 配置

        self.novel_name_var = tk.StringVar()
        self.novel_url_var = tk.StringVar()
        self.max_chapters_var = tk.StringVar(value="1000")
        self.output_dir_var = tk.StringVar(value="output/")  # 在这里不拼接小说名称（在SpiderCore中自动拼接）
        self.wait_var = tk.BooleanVar(value=False)
        self.wait_min_var = tk.StringVar(value="1.0")
        self.wait_max_var = tk.StringVar(value="3.0")
        self.output_form_var = tk.StringVar(value="epub")
        self.progress_text_var = tk.StringVar(value="0/0")

        self._build_ui()
        self._log_output("程序启动成功", "info")
        self._load_config_to_ui()
        self._log_output("加载配置完毕", "info")
        self._toggle_wait_input()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_ui(self):
        row = 0  # 所在行
        # 起始网址输入
        ttk.Label(self.root, text= "起始网址：").grid(
            row= row, column= 0, sticky= "w", padx= 5, pady= 3)
        ttk.Entry(self.root, textvariable= self.novel_url_var, width= 70).grid(
            row= row, column= 1, columnspan= 2, sticky= "ew", padx= 5, pady= 3)
        # 小说名称输入
        row += 1
        ttk.Label(self.root, text= "小说名称：").grid(
            row= row, column= 0, sticky= "w", padx= 5, pady= 3)
        ttk.Entry(self.root, textvariable=self.novel_name_var, width=40).grid(
            row= row, column=1, sticky= "w", padx= 5, pady= 3)
        # 选择保存目录
        row += 1
        ttk.Label(self.root, text= "保存目录：").grid(
            row = row, column= 0, sticky= "w", padx= 5, pady= 3)
        ttk.Entry(self.root, textvariable= self.output_dir_var, width= 60).grid(
            row= row, column= 1, sticky= "ew", padx= 5, pady= 3)
        ttk.Button(self.root, text= "浏览", command= self._browse_output_dir).grid(
            row= row, column= 2, padx= 5, pady= 3)
        # 等待时间+最大章节设置
        row += 1
        ttk.Checkbutton(self.root, text= "启用等待", variable= self.wait_var,
                        onvalue= True, offvalue= False, command= self._toggle_wait_input).grid(   # 这里的这个方法用来禁用/启用等待时间输入
            row= row, column= 0, sticky= "w", padx= 5, pady= 3)
        ttk.Label(self.root, text= "等待时间：").grid(
            row= row, column= 1, sticky= "e", padx= (0, 260), pady= 3)
        self.entry_wait_min = ttk.Entry(self.root, textvariable= self.wait_min_var, width= 6)
        self.entry_wait_min.grid(row= row, column= 1, sticky="e", padx= (60, 200), pady= 3)
        ttk.Label(self.root, text= "~").grid(row= row, column= 1, padx= (105,155), pady= 3)
        self.entry_wait_max = ttk.Entry(self.root, textvariable= self.wait_max_var, width= 6)
        self.entry_wait_max.grid(row= row, column= 1, sticky="w", padx= (150, 110), pady= 3)
        ttk.Label(self.root, text= "秒").grid(row= row, column= 1, padx= (180, 80), pady= 3)

        ttk.Label(self.root, text= "最大爬取章节数（不可为0）：").grid(
            row= row, column= 2, columnspan=2, sticky= "e", padx= 10, pady= 3)
        ttk.Entry(self.root, textvariable= self.max_chapters_var, width= 10).grid(
            row= row, column= 4, sticky= "w", padx= 5, pady= 3)
        # 选择输出格式
        row += 1
        ttk.Label(self.root, text= "输出格式：").grid(
            row= row, column= 0, sticky= "w", padx= 5, pady= 3)
        ttk.Radiobutton(self.root, text="EPUB", variable= self.output_form_var, value= "epub").grid(
            row= row, column= 1, sticky= "w")
        ttk.Radiobutton(self.root, text= "TXT", variable= self.output_form_var, value= "txt").grid(
            row= row, column= 1, padx= (60, 20),sticky= "w")

        # 你别说，看着这一长溜看着真整齐

        # 开始、停止等各种按钮+进度文本
        row += 1
        # 在这里创建一个Frame容器来放下这么多按钮，避免影响上面的组件
        btn_frame = ttk.Frame(self.root, padding= 10, relief='solid', borderwidth=1)
        btn_frame.grid(row= row, column= 0, columnspan= 5, padx=10, pady=5, sticky="ew")
        # btn_frame.columnconfigure(0, weight=1)
        # 创建按钮
        self.button_start_spider = ttk.Button(btn_frame, text="开始爬取", command=self._start, width=10)
        self.button_start_spider.grid(row= 0, column= 0, padx= 5)
        self.button_stop_spider = ttk.Button(btn_frame, text="停止爬虫", command=self._stop, width=10, state= "disabled")
        self.button_stop_spider.grid(row=0, column=1, padx= 5)
        ttk.Button(btn_frame, text="测试网址", command=self._test_spider, width=10).grid(
            row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="打开目录", command=self._open_output_dir, width=10).grid(
            row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="重置配置", command=self._reset_config, width=10).grid(
            row=0, column=4, padx=5)
        # 进度标签
        ttk.Label(btn_frame, textvariable=self.progress_text_var, font=('', 10, 'bold')).grid(
            row= 0, column= 5, padx= 5)
        # btn_frame.columnconfigure(5, weight=1)

        # 日志+预览
        row += 1

        log_frame = ttk.Frame(self.root)
        log_frame.grid(row= row, column= 0, columnspan= 3, sticky= "nsew", padx= 10, pady= (10, 25))
        log_frame.rowconfigure(0, weight= 1)
        log_frame.columnconfigure(0,weight= 1)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap= tk.WORD, font=('Consolas', 9))
        self.log_text.grid(row= 0, column= 0, sticky= "nsew")
        self.log_text.tag_config("info", foreground='black')
        self.log_text.tag_config("warning", foreground='orange')
        self.log_text.tag_config("error", foreground= "red")        # 花花绿绿的日志……

        prev_frame = ttk.Frame(self.root)
        prev_frame.grid(row=row, column= 3, columnspan= 2, sticky= "nsew", padx= 5, pady= (10, 25))
        prev_frame.rowconfigure(0, weight=1)
        prev_frame.columnconfigure(0, weight=1)
        self.prev_text = scrolledtext.ScrolledText(
            prev_frame, wrap=tk.WORD, font=('宋体', 10), state= "disabled")   # 只读模式
        self.prev_text.grid(row= 0, column= 0, sticky= "nsew")

        self.root.columnconfigure(0, weight= 2, minsize=80)      # 设置列权重，让左边70%，右边30%
        self.root.columnconfigure(1, weight= 2, minsize=180)
        self.root.columnconfigure(2, weight= 3, minsize=100)
        self.root.columnconfigure(3, weight= 1, minsize=50)
        self.root.columnconfigure(4, weight= 2, minsize=80)

        self.root.rowconfigure(row, weight= 1)      # 这样可以自动顶住最底下


    def _load_config_to_ui(self):
        self.novel_url_var.set(self.config.get("url", ""))
        self.novel_name_var.set(self.config.get("novel_name", ""))
        self.max_chapters_var.set(self.config.get("max_chapters", "1000"))
        self.wait_var.set(self.config.get("wait", False))
        self.wait_min_var.set((self.config.get("wait_min", "1.0")))
        self.wait_max_var.set((self.config.get("wait_max", "3.0")))
        self.output_dir_var.set(self.config.get("save_dir", "output"))
        self.output_form_var.set(self.config.get("output_form", "epub"))
        # 写一半突然发现configurator.py没有对整个json检查，所以如果出现空，会读取不到。


    def _save_ui_to_config(self):
        self.config["url"] = self.novel_url_var.get()
        self.config["novel_name"] = self.novel_name_var.get()
        self.config["max_chapters"] = self.max_chapters_var.get()
        self.config["wait"] = self.wait_var.get()
        self.config["wait_min"] = self.wait_min_var.get()
        self.config["wait_max"] = self.wait_max_var.get()
        self.config["save_dir"] = self.output_dir_var.get()
        self.config["output_form"] = self.output_form_var.get()


    def _browse_output_dir(self):
        path = filedialog.askdirectory(title= "请选择保存目录")
        if path:
            self.output_dir_var.set(path)


    def _toggle_wait_input(self):
        if self.wait_var.get():
            state = "normal"
        else:
            state = "disabled"

        self.entry_wait_min.config(state= state)
        self.entry_wait_max.config(state= state)


    def _log_output(self, msg, msg_type= "info"):
        def _insert_log():
            out_color = "info" if msg_type == "info" else ("warning" if msg_type == "warning" else "error")
            msg_level = "INFO" if msg_type == "info" else ("WARNING" if msg_type == "warning" else "ERROR")
            message = f"[{time.strftime('%H:%M:%S', time.localtime())}][{msg_level}]|{msg}"
            self.log_text.insert(tk.END, message + "\n\n", out_color)
            if self.log_text.yview()[1] >= 0.8:
                self.log_text.see(tk.END)
        self.root.after(0, _insert_log)     # 保证线程安全


    def _update_progress_text(self, current, total):
        def _upd_progress():
            self.progress_text_var.set(f"{current}/{total}")
        self.root.after(0, _upd_progress)


    def _update_preview_text(self, content):
        def _upd_preview():
            self.prev_text.config(state= "normal")
            self.prev_text.delete(1.0, tk.END)  # 清屏
            self.prev_text.insert(tk.END, content)
            self.prev_text.config(state= "disabled")
        self.root.after(0, _upd_preview)


    def _convert_config_data(self):
        # config.json中的数据大部分为字符串，需要转化
        url = self.novel_url_var.get()
        novel_name = self.novel_name_var.get()
        max_chapters = int(self.max_chapters_var.get())
        wait = self.wait_var.get()
        w_min = float(self.wait_min_var.get())
        w_max = float(self.wait_max_var.get())
        out_dir = self.output_dir_var.get()
        form = self.output_form_var.get()

        return url, novel_name, max_chapters, out_dir, form, wait, w_min, w_max


    def _start(self):
        if self.is_running:
            return

        params = self._convert_config_data()

        if not params[0]:
            messagebox.showerror("错误", "请输入起始网址")
            return

        self.spider = SpiderCore(
            params[0],
            params[1],
            params[2],
            params[3],
            params[4],
            log_callback= self._log_output,
            progress_callback= self._update_progress_text,
            stop_callback= lambda: not self.is_running,
            prev_callback= self._update_preview_text,
            wait= params[5],
            wait_min= params[6],
            wait_max= params[7])

        self.is_running = True
        self._log_output("爬虫已启动", "info")
        self.button_start_spider.config(state= "disabled")
        self.button_stop_spider.config(state= "normal")

        self.spider_thread = threading.Thread(target= self.spider.start_spider, daemon= True)    # 设置单独线程用于爬虫，daemon= True可以防止被关掉还继续
        self.spider_thread.start()
        self._monitor()


    def _stop(self):
        if self.spider:
            self.spider.stop()
        self.is_running = False
        self._log_output("正在停止爬虫……","info")
        self.button_start_spider.config(state= "normal")
        self.button_stop_spider.config(state= "disabled")


    def _test_spider(self):
        url = self.novel_url_var.get()
        if not url:
            messagebox.showerror("错误", "请输入url")
            return
        self._log_output("正在测试解析","info")

        def _test():
            try:
                from fetcher import fetch_html
                from parser import parse_chapter

                title, content, next_url = parse_chapter(fetch_html(url) ,url)

                self._update_preview_text(f"{title}\n{content[:500]}(便于测试，截取前500字符)")
                self._log_output(f"测试解析成功，页面标题{title}，正文内容长度{len(content)}，正文已显示到预览栏", "info")
            except Exception as e:
                self._log_output(f"测试解析时出现错误：{e}\n测试解析失败", "error")

        threading.Thread(target=_test, daemon=True).start()


    def _open_output_dir(self):
        novel_dir = os.path.join(self._convert_config_data()[3], self._convert_config_data()[1])
        if not os.path.exists(novel_dir):
            os.makedirs(novel_dir, exist_ok=True)
        os.startfile(novel_dir)
        self._log_output("打开输出文件夹", "info")


    def _reset_config(self):
        reset_config()
        self.config = load_config()
        self._load_config_to_ui()
        self._log_output("配置已重置", 'info')


    def _monitor(self):
        if self.spider_thread and self.spider_thread.is_alive():
            self.root.after(400, self._monitor)
        else:
            self._spider_finished()


    def _spider_finished(self):
        self.is_running = False
        # self.config["url"] = " "
        # self.config["novel_name"] = " "
        # save_config(self.config)
        # self._load_config_to_ui()
        # self._log_output("爬虫已结束，已自动清空小说url以及小说名称", "info")
        self._log_output("爬虫已结束", "info")

        self.button_start_spider.config(state= "normal")
        self.button_stop_spider.config(state= "disabled")

    def _on_closing(self):
        self._save_ui_to_config()
        save_config(self.config)
        if self.is_running:
            if messagebox.askokcancel("是否退出", "爬虫正在运行，确定退出吗？"):
                self._stop()
                self.root.destroy()
        else:
            self.root.destroy()



if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()















