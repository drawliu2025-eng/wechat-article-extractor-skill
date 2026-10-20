# 公开正文与媒体读取

## 文字优先（Python 3.10+，仅标准库）

```bash
python3 scripts/wechat_public_article_extract.py 'https://mp.weixin.qq.com/s/ARTICLE' --include-text --no-model --no-media
```

公开 HTTP → DOM 正文校验 → 单次 MicroMessenger UA 兜底。不会读取 Cookie、微信聊天数据库或登录态，不执行页面 JavaScript。支持嵌套正文、短文及 JS 字符串中的正文；没有取得正文就是失败，不保证所有公众号可读。

退出码：0 完整纯文字；3 部分可读（正文或媒体引用）；1 未取得内容。`text_ok` 只表示文字已读；`ok`/`content_complete` 不包括未理解图片/视频。

## 可选模型

去掉 `--no-model` 后，对未知结构生成受限声明式提取方案。只选择现有 DOM 节点和白名单属性，不接受模型生成的“原文”，不执行任意代码。

模型路由：可选 `WECHAT_OPENCLAW_SHIM` 指定已有 Node stdin shim（输出含 `ok`、`outputs[0].text` 的单行 JSON）→ 已登录的 Codex CLI 只读临时会话。默认模型预算 55 秒；无需模型也能提取已知结构。没有可用模型时保留失败回执，不清除已读取文字。仓库不提供登录凭据或自动注册。

## 可选视频（不默认等待）

需要媒体时去掉 `--no-media` 和 `--no-model`。仅支持页面已公开包含的 `wxv` 播放记录及 `mpvideo.qpic.cn` 视频源，不调用隐藏播放接口。

依赖安装到已有约定的独立环境：

```bash
python3 -m venv ~/.local/share/wechat-media-venv
~/.local/share/wechat-media-venv/bin/pip install -r scripts/wechat_public_article_media.requirements.txt
```

首次转写可能下载 faster-whisper/base 模型。默认总预算 600 秒、最多 2 段、单段 30MB/15 分钟；机器音轨转写与 8 个时间点画面采样均是部分理解，不标整篇完整。独立图片理解及其他语音形式尚未全面支持。已有下载或分阶段结果由调用者通过 `analyze(..., local_files=...)` 复用；CLI 不提供跨进程自动缓存，不宣称自动续传。

## 校验

```bash
python3 tests/verify.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

离线合成样例用于测试结构兼容与失败边界，不代表每个线上页面都可读。旧 Node 元数据接口与说明保留在 scripts/extract.js 和 references/legacy-extractor.md，不作为代读首选路径。
