# M3U8-Downloader
![demo](https://le.0x7e.tech/wp-content/uploads/2025/03/m3u8-downloader.png)
### 简介
这是一个简洁的M3U8视频下载脚本，只需要视频链接，便可以实现多线程下载TS片段，然后使用ffmpeg将片段合成.ts视频，最后再转化为.mp4视频。下载线程数量可以自定义，默认为32线程，速度还是挺快的，支持断点续传。
### 如何使用
- 将ffmpeg.7z中的ffmpeg.exe解压至当前目录，或者本地安装后添加至系统环境变量，[FFmpeg仓库](https://github.com/FFmpeg/FFmpeg)
- Python环境中安装requests库
```bash
pip install -r requirements.txt
```
- 双击运行run.pyw文件或通过以下指令运行
```bash
pythonw run.pyw
```
### 注意事项
- 下载完成后默认会清理所有临时文件，只保留.mp4文件，如需保留某些临时文件，请编辑run.pyw，注释掉清理对应临时文件的代码即可，清理代码开始于第236行。

### Introduction
This is a concise M3U8 video download script, which only needs a video link to achieve multi-threaded download of TS segments, and then uses ffmpeg to merge the segments into a .ts video, and finally converts it to a .mp4 video. The number of download threads can be customized, with a default of 32 threads, and the speed is still quite fast, supporting breakpoint resume.
### How to use
- Extract ffmpeg.exe from ffmpeg.7z to the current directory, or install it locally and add it to the system environment variable, [FFmpeg repository](https://github.com/FFmpeg/FFmpeg)
- Install the requests library in the Python environment
```bash
pip install -r requirements.txt
```
- Double-click to run the run.pyw file or run it through the following command
```bash
pythonw run.pyw
```
### Precautions
- After the download is complete, all temporary files will be cleaned up by default, and only the .mp4 file will be kept. If you need to keep some temporary files, please edit run.pyw, comment out the code that cleans up the corresponding temporary files, which starts from line 236.

