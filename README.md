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

