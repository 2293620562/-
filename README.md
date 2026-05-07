#成品说明（已实现的功能）

*支持“添加连接”（RTMP/M3U8）→ 选择条目 → 开始/停止 → 实时滚动字幕显示（类似你截图的“添加链接+后台处理”流程），见 main_window.py / add_dialog.py
*后台自动拉流取音频（内置 ffmpeg 调用）并分片处理，见 audio_stream.py / ffmpeg.py
*离线实时语音转文字（faster-whisper，本地模型目录加载），见 transcriber.py
*自动说话人分离：对每段字幕做说话人嵌入 + 在线聚类，输出 S1/S2… 标注，见 speaker.py / session.py
*导出 TXT / SRT； 另提供“按说话人整理 + 简易摘要/关键词”导出，见 exporter.py

#如何拿到 Windows 10 可运行 EXE（离线自带模型/插件）
*代码与脚本在 README.md
*Windows 打包流程：
**先下载离线资源（Whisper 模型、说话人模型、Windows 版 ffmpeg）：prepare_offline_assets.py
**再用 PyInstaller 打包： build_windows_exe.py
*也提供 GitHub Actions 一键构建产物（自动下载模型并打包，产物在 workflow artifact 里）：build-windows.yml

#使用方式
*运行后点“添加”粘贴 RTMP/M3U8 → 选中条目点“开始”，字幕会实时滚动； 需要文件就点“导出TXT/SRT”或“导出整理/摘要”。

#已补上“链接解析器”这一层：现在“添加连接”里既可以粘贴 RTMP/M3U8，也可以直接粘贴抖音/快手/B站等网页/分享链接，后台会先自动解析成可供 ffmpeg 拉流的真实地址，再进入实时转写与说话人分离流程。
改动点
*新增通用解析器（优先 yt-dlp）：link_resolver.py
**会话启动时自动解析并在状态栏显示“解析链接中/拉流中/运行中”：session.py
**“添加连接”输入框提示支持网页分享链接：add_dialog.py
**更新依赖与 Windows 打包收集 yt-dlp：
***requirements.txt
***build_windows_exe.py

#使用方式
*直接把抖音/快手/B站直播间链接或分享短链粘贴到“链接”，点开始即可； 如果解析失败，会弹窗显示具体错误原因（通常是链接无效/平台临时风控/需要登录但当前未启用Cookie导入）。

# LiveSTT

输入 RTMP / M3U8 链接，后台拉流取音频，实时语音转文字并自动区分发言者；支持导出 TXT / SRT，并可按说话人整理与生成简易摘要。

## 目录约定

- `models/whisper/`：离线转写模型（默认使用 `Systran/faster-whisper-small` 的本地快照）
- `models/speaker/`：说话人嵌入模型（默认使用 `speechbrain/spkrec-ecapa-voxceleb` 的本地快照）
- `assets/ffmpeg/`：打包时放入 Windows 版 ffmpeg（`ffmpeg.exe`）

## 本地运行（开发态）

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m livestt
```

## 打包 EXE（Windows 10 64位）

在 Windows 环境执行：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
python scripts\prepare_offline_assets.py
python scripts\build_windows_exe.py
```

也可以使用 GitHub Actions 直接生成可下载的 EXE 产物（见 `.github/workflows/build-windows.yml`）。

