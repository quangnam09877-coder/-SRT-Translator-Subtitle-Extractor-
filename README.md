# 字幕翻译器 & 字幕提取器

一个多合一字幕处理工具，集成了AI翻译、语音识别字幕提取和视频字幕合并功能。（韩娱人看不懂生肉且难以忍受机翻的崩溃产物...经尝试，gemini的翻译质量基本能保证语义通顺，但是遇到具体的人名等会有一定问题，对于时间轴以及字幕细节修改可以结合subeasy.ai平台！）

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 主要功能

### SRT 翻译
- 使用Google Gemini AI免费API进行翻译（前往 https://aistudio.google.com/app/apikey 申请免费api吧！）
- 目标语言可自由调节
- 批量处理，智能分批翻译避免API限制
- 支持代理设置
- 实时翻译进度显示

### 字幕提取
- 基于 Faster Whisper 的本地语音识别，自动识别视频语言
- 支持多种视频格式 (MP4, AVI, MKV, MOV, WMV, FLV, WebM)
- 支持本地模型，没有本地模型也可选择直接下载huggingface上的模型，多种模型选择 (tiny, base, small, medium, large-v1/v2/v3)
- CPU/CUDA/自动设备选择

### 视频字幕合并
- FFmpeg驱动的专业级视频处理
- 字体自定义选项
- 实时字体预览功能
- 多种编码格式支持
- 位置、颜色、大小全面可调

## 快速开始

### 方法1：直接使用exe程序
- 可直接从releases中获取最新的exe可执行程序

### 方法2：配置代码
### 环境要求

- Python 3.8 或更高版本
- Windows 10/11 (推荐)
- FFmpeg (用于视频合并功能)

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/Joycejinnn/-SRT-Translator-Subtitle-Extractor-.git
   cd SRT_Translator_&_Subtitle_Extractor
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **安装 FFmpeg** (可选，用于视频合并功能)
   - 下载: https://ffmpeg.org/download.html
   - 解压并添加到系统 PATH

4. **获取 Google API 密钥** (用于翻译功能)
   - 访问: https://aistudio.google.com/app/apikey
   - 创建新的 API 密钥

### 运行应用

```bash
python app.py
```

## 使用指南

### SRT 翻译功能

1. **设置 API 密钥**
   - 在翻译页面输入 Google Gemini API 密钥
   - 选择或输入模型名称 (默认免费模型: gemini-2.5-flash)

2. **选择文件**
   - 点击"Browse"选择输入的 SRT 字幕文件
   - 设置输出文件路径

3. **配置选项**
   - 选择目标语言
   - 如需要可配置代理设置

4. **开始翻译**
   - 点击"Start Translation"
   - 查看实时进度和日志

### 字幕提取功能

1. **选择视频文件**
   - 支持格式: MP4, AVI, MKV, MOV, WMV, FLV, WebM

2. **配置模型**
   - 选择设备: CPU, CUDA, 或自动选择
   - 从下拉菜单选择模型或使用本地模型路径
   - 首次使用会自动下载选定模型

3. **开始提取**
   - 点击"Extract Subtitles"
   - 等待处理完成

### 视频字幕合并功能

1. **选择文件**
   - 选择视频文件和 SRT 字幕文件
   - 设置输出视频路径

2. **字体设置**
   - 字体族：Microsoft YaHei, Arial, Times New Roman 等
   - 大小、粗体、斜体选项
   - 字体颜色和轮廓颜色选择
   - **实时预览**：查看字体效果

3. **位置设置**
   - 字幕位置：底部、顶部、居中
   - 垂直和水平边距调整

4. **高级选项**
   - 视频编码器: libx264, libx265, libvpx-vp9
   - 音频编码器: AAC, MP3
   - 质量设置 (CRF)
   - 字幕编码格式

## ⚙️ 配置选项

### Whisper 模型
| 模型 | 大小 | 速度 | 精度 | 说明 |
|------|------|------|------|------|
| tiny | ~39MB | 最快 | 较低 | 快速处理 |
| base | ~74MB | 快 | 一般 | 平衡选择 |
| small | ~244MB | 中等 | 较好 | 推荐日常使用 |
| medium | ~769MB | 较慢 | 好 | 高质量需求 |
| large-v3 | ~1550MB | 最慢 | 最佳 | 专业级精度 |

### 视频编码选项
- **libx264**: 通用兼容性好
- **libx265**: 更好的压缩率
- **libvpx-vp9**: 开源WebM格式
- **copy**: 复制原始编码(最快)

## 贡献指南
欢迎提交 Issue 和 Pull Request！

### 开发环境设置
1. Fork 本仓库
2. 创建特性分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送分支: `git push origin feature/AmazingFeature`
5. 提交 Pull Request

## 许可证
本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

**如果这个项目对你有帮助，请给个 ⭐ Star！**
