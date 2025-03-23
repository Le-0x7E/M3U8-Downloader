import os
import sys
import requests
import subprocess
import time
import threading
from urllib.parse import urljoin
from tkinter import Tk, Label, Entry, Button, Text, StringVar, ttk
from concurrent.futures import ThreadPoolExecutor, as_completed

class M3U8Downloader:
    def __init__(self, root):
        self.root = root
        self.root.title("M3U8 视频下载器")
        self.root.geometry("600x380")

        # 变量
        self.m3u8_url = StringVar()
        self.max_workers = StringVar(value="32")   # 默认32线程
        self.downloading = False
        self.total_segments = 0
        self.downloaded_segments = 0
        self.start_time = None

        # GUI 组件
        self.url_label = Label(root, text="视频链接:")
        self.url_label.grid(row=0, column=0, padx=2, pady=15, sticky="e")

        self.url_entry = Entry(root, textvariable=self.m3u8_url, width=52)
        self.url_entry.grid(row=0, column=1, padx=0, pady=15, sticky="nsew")

        self.thread_label = Label(root, text="下载线程数量:")
        self.thread_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.thread_entry = Entry(root, textvariable=self.max_workers, width=2)
        self.thread_entry.grid(row=0, column=2, padx=25, pady=5, sticky="e")

        self.progress_label = Label(root, text="下载进度:")
        self.progress_label.grid(row=1, column=0, padx=2, pady=0, sticky="e")

        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.grid(row=1, column=1, columnspan=1, padx=0, pady=5, sticky="nsew")

        self.speed_label = Label(root, text="网速: 00.00 MB/s")
        self.speed_label.grid(row=1, column=2, columnspan=1, padx=5, pady=5, sticky="w")

        self.log_text = Text(root, height=15, width=78)
        self.log_text.grid(row=2, column=0, columnspan=3, padx=25, pady=15)

        self.start_button = Button(root, text="   开始下载   ", command=self.start_download)
        self.start_button.grid(row=3, column=1, columnspan=1, padx=60, pady=12, sticky="w")

        self.stop_button = Button(root, text="   终止下载   ", command=self.stop_download)
        self.stop_button.grid(row=3, column=1, columnspan=1, padx=25, pady=12, sticky="e")

    def log(self, message):
        # 输出msg到日志框
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def start_download(self):
        # 检查是否有URL
        if not self.m3u8_url.get():
            self.log("请先输入 M3U8 URL！")
            return
        
        # 检查线程数设置是否规范
        try:
            max_workers = int(self.max_workers.get())
            if max_workers <= 0:
                self.log("线程数必须大于 0！")
                return
        except ValueError:
            self.log("线程数必须是整数！")
            return
        
        # 开始下载任务
        self.log("开始下载")
        self.downloading = True
        self.start_time = time.time()
        self.downloaded_segments = 0
        self.progress_bar["value"] = 0
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        threading.Thread(target=self.download_m3u8_video, args=(max_workers,)).start()

    def stop_download(self):
        # 终止按钮终止任务
        self.downloading = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.log("下载已终止")

    def download_ts_file(self, ts_url, output_path):
        # 先检查downloading标志
        if not self.downloading:
            return
        if os.path.exists(output_path):
            # 若文件已存在，判断是否需要续传
            file_size = os.path.getsize(output_path)
            headers = {"Range": f"bytes={file_size}-"}   # 通过设置Range头，实现从已下载的位置继续
        else:
            file_size = 0
            headers = {}
        
        # 请求文件
        try:
            response = requests.get(ts_url, headers=headers, stream=True)
            if response.status_code != 200 and response.status_code != 206:   # 206表示部分内容
                raise Exception(f"Failed to download ts file: {ts_url}, status code: {response.status_code}")
            # 如果文件已存在则追加写入
            with open(output_path, "ab" if file_size else "wb") as f:   
                for chunk in response.iter_content(chunk_size=4096):
                    # 检查downloading标志
                    if not self.downloading:
                        return
                    f.write(chunk)
            return True
        except Exception as e:
            self.log(f"下载失败: {ts_url} - {e}")
        return False
        '''
        try:
            response = requests.get(ts_url, stream=True)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=4096):
                        if not self.downloading:
                            break
                        f.write(chunk)
                return True
        except Exception as e:
            self.log(f"下载失败: {ts_url} - {e}")
        return False
        '''

    def update_progress(self):
        # 更新下载进度
        if self.total_segments:
            # progress = (self.downloaded_segments / self.total_segments) * 100
            self.progress_bar["value"] = self.downloaded_segments   # 进度计算方法：已下载片段数/总片段数
        
        # 计算并更新网速
        elapsed_time = time.time() - self.start_time
        downloaded_size = self.downloaded_segments * 1024 * 512   # 假设每个片段512KB
        speed = downloaded_size / (elapsed_time * 1024 * 1024) if elapsed_time > 0 else 0
        self.speed_label.config(text=f"网速: {speed:.2f} MB/s")         

    def download_m3u8_video(self, max_workers):
        # 下载并合并m3u8视频
        try:
            m3u8_url = self.m3u8_url.get()
            temp_dir = "temp_ts_files"
            os.makedirs(temp_dir, exist_ok=True)
            
            # 获取m3u8文件内容
            response = requests.get(m3u8_url)
            if response.status_code != 200:
                self.log(f"无法下载 m3u8 文件: {response.status_code}")
                return
            m3u8_content = response.text.splitlines()
            
            # 获取TS文件列表
            ts_files = [line.strip() for line in m3u8_content if line.strip() and not line.startswith('#')]
            self.total_segments = len(ts_files)
            self.log(f"共发现 {self.total_segments} 个 TS 片段")
            self.progress_bar["maximum"] = self.total_segments   # 进度条上限设置为总片段数
            
            # 多线程下载所有TS文件
            ts_file_paths = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                # 提交下载任务
                for i, ts_file in enumerate(ts_files):
                    # 检查downloading标志
                    if not self.downloading:
                        break
                    ts_url = urljoin(m3u8_url, ts_file)
                    ts_file_path = os.path.join(temp_dir, f"segment_{i}.ts")
                    # self.log(f"队列中: {ts_file_path}")
                    futures[executor.submit(self.download_ts_file, ts_url, ts_file_path)] = ts_file_path
                    ts_file_paths.append(ts_file_path)
                
                # 监控下载任务
                for future in as_completed(futures):
                    # 检查downloading标志
                    if not self.downloading:
                        break
                    ts_file_path = futures[future]
                    if future.result():
                        self.downloaded_segments += 1
                        self.update_progress()
                        self.log(f"已下载: {ts_file_path}")
                    else:
                        self.log(f"未下载: {ts_file_path}")
            
            # TS文件下载完成，开始合并
            if self.downloading:   # 检查标志
                self.log("TS 文件下载完成！")
                self.log("正在合并 TS 文件...")
                temp_output_file = os.path.join(temp_dir, "output.ts")

                # 写入临时文件file_list.txt
                with open("file_list.txt", "w") as f:
                    for ts_file_path in ts_file_paths:
                        if os.path.exists(ts_file_path):
                            f.write(f"file '{ts_file_path}'\n")
                
                # 用ffmpeg合并TS片段为output.ts
                time.sleep(3)
                subprocess.run([
                    "ffmpeg", "-f", "concat", "-safe", "-0", "-i", "file_list.txt", "-c", "copy", temp_output_file
                ],
                stdout=subprocess.DEVNULL,   # 完全丢弃标准输出，隐藏ffmpeg的控制台
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                check=True)

                # 设置输出mp4的文件名
                self.log("合并完成！\n正在转换为 MP4...")
                base_name = "output"
                ext = ".mp4"
                output_file = f"{base_name}01{ext}"   # 初始文件名为output01.mp4
                counter = 2
                while os.path.exists(output_file):
                    output_file = f"{base_name}{counter:02d}{ext}"   
                    counter += 1
                
                # 把output.ts转换为mp4
                subprocess.run([
                    "ffmpeg", "-i", temp_output_file, "-c", "copy", output_file
                ],
                stdout=subprocess.DEVNULL,   # 完全丢弃标准输出，隐藏ffmpeg的控制台
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                check=True)

                # 清理临时文件（如果想保留哪些临时文件可以把对应清理代码注释掉）
                self.log("转换完成！\n正在清理临时文件...")
                # 清理file_list.txt
                os.remove("file_list.txt")
                # 清理所有TS片段
                for ts_file_path in ts_file_paths:
                    if os.path.exists(ts_file_path):
                        os.remove(ts_file_path)
                # 清理合成的TS视频
                os.remove(temp_output_file)
                # 删除临时文件夹
                os.rmdir(temp_dir)

                # 下载任务完成
                self.log(f"清理完成！\n视频已保存为 {output_file}")
                self.log(f"下载任务完成！\n")
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")

        except Exception as e:
            self.log(f"发生错误: {e}")
        finally:
            self.downloading = False

if __name__ == "__main__":
    root = Tk()
    app = M3U8Downloader(root)
    root.mainloop()
