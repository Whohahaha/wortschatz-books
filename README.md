# Wortschatz 词书

德语背单词 App（Wortschatz）可以下载的词书。App 在「设置 → 词书 → 下载词书」里读取这里的 `index.json`，
从 GitHub 或 jsDelivr 镜像下载词书和发音。

| 词书 | 内容 |
| --- | --- |
| 歌德 A2 词书 | 歌德 A2 词表里比 A1 新增的词 |
| 歌德 B1 词书 | 歌德 B1 词表里比 A1、A2 新增的词 |

歌德 A1 词书内置在 App 里，`base/goethe_a1.tsv` 只用来去重。

## 来源和授权

- 词头依据歌德学院 Goethe-Zertifikat A2、B1 公开词表。中文释义和例句都是本项目自己写的，没有照搬官方词表里的例句。
- 复数和动词变位来自 Wiktionary（经 kaikki.org 整理），CC BY-SA 4.0。
- 发音用 Piper 离线神经网络 TTS 生成，德语 Thorsten 音色（CC0）。

## 怎么改词书

1. 改 `sources/<词书>/source_*.tsv`。每行：词性、词头（名词带冠词，可分动词用 `|` 标前缀，如 `an|rufen`）、中文释义、德语例句、例句翻译，
   名词可选第 6 列写复数（`-` 表示没有复数），动词可选第 6 列写完成时助动词（haben / sein）。
2. 推送到 main。GitHub Actions 会重新生成词书和发音；词表有变化的词书版本号加一，App 里会出现「更新」按钮。
   词条 id 由词头生成、不会变，更新后学习进度不丢。

## 文件

- `index.json`：词书列表（App 读取）。
- `<词书 id>/<id>-<版本>.tsv`：词书，App 的词书格式。
- `<词书 id>/<id>-<版本>-audio-<n>.zip`：发音（每个文件小于 20 MB，方便 jsDelivr 镜像）。
- `books.json`：要发布哪些词书；`tools/`：生成脚本。
