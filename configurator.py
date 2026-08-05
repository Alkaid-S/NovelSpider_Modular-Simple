import os
import json

DEFAULT_CONFIG = {
  "url": "",
  "novel_name": "",
  "max_chapters": "1000",
  "wait": False,
  "wait_min": "1",
  "wait_max": "3",
  "save_dir": "output/",    # 不可拼接小说名称，会在SpiderCore自动拼接
  "output_form": "epub",    # 添加输出格式
}

CONFIG_FILE_NAME = "config.json"

def load_config() -> dict:  # 写不写都没关系，整齐一点有仪式感（bushi）
    if not os.path.exists(CONFIG_FILE_NAME):    # 检测是否存在
        return DEFAULT_CONFIG.copy()            # copy()可以对字典进行拷贝

    try:    # 万一有小笨蛋随便往里面放东西捏
        with open(CONFIG_FILE_NAME, "r", encoding= "utf-8") as rdf:
            local_config = json.load(rdf)
            return local_config
    except json.JSONDecodeError as json_error:
        print(f"出现错误：{json_error}")
        return DEFAULT_CONFIG.copy()
    except FileNotFoundError as file_error:     # 我都检测过了其实……
        print(f"出现错误：{file_error}")
        print("干点人事")
        return DEFAULT_CONFIG.copy()



def save_config(config: dict) -> None:      # 啥都不返回，嗯~
    with open(CONFIG_FILE_NAME, "w", encoding= "utf-8") as wtf:
        json.dump(config, wtf, indent= 2, ensure_ascii=False)   # indent参数可以自动缩进（看着好看些），ensure_ascii设成false可以输出中文


def reset_config():
    with open(CONFIG_FILE_NAME, "w", encoding= "utf-8") as wtf:
        json.dump(DEFAULT_CONFIG, wtf, indent= 2, ensure_ascii=False)

