# 主题目录

此目录用于存放应用程序的主题文件。

主题文件是包含 Qt 样式表的 JSON 文件，用于自定义应用程序的外观。

## 主题文件格式

主题文件应该是一个 JSON 文件，包含以下字段：

```json
{
  "name": "主题名称",
  "description": "主题描述",
  "author": "作者名称",
  "version": "1.0.0",
  "dark": true,  // 是否为深色主题
  "styles": {
    "app": "QWidget { ... }",
    "main_window": "QMainWindow { ... }",
    "buttons": "QPushButton { ... }",
    // 其他样式...
  }
}
```

## 内置主题

应用程序内置了两个主题：

- `light.json`: 浅色主题（默认）
- `dark.json`: 深色主题

用户可以在设置中选择主题。 