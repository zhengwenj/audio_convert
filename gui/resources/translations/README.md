# 翻译目录

此目录用于存放应用程序的翻译文件。

翻译文件使用 Qt 的 .ts 和 .qm 格式，用于支持多语言界面。

## 支持的语言

应用程序计划支持以下语言：

- 中文 (zh_CN) - 默认
- 英语 (en_US)
- 日语 (ja_JP)
- 韩语 (ko_KR)
- 法语 (fr_FR)
- 德语 (de_DE)
- 西班牙语 (es_ES)
- 俄语 (ru_RU)

## 翻译文件命名

翻译文件应按以下格式命名：

```
audio_convert_<语言代码>.ts  # 源翻译文件
audio_convert_<语言代码>.qm  # 编译后的翻译文件
```

例如：`audio_convert_en_US.ts` 和 `audio_convert_en_US.qm`。

## 添加新翻译

要添加新的翻译，请使用 Qt Linguist 工具创建和编辑 .ts 文件，然后使用 lrelease 工具将其编译为 .qm 文件。 