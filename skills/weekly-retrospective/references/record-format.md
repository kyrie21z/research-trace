# 提取器输入合同

默认扫描 `--records-dir` 下的 `*.md`，读取 `<!-- research-record` 与 `-->` 之间的JSON；完整记录写法由目标项目PROVENANCE规定，生成模板可用独立的 research-record 技能。

提取器要求 id 为非空字符串，title/summary/scope 为字符串；topics、related、corrects、supersedes 若存在，须为字符串数组。

occurred_at 支持 null、YYYY-MM-DD、ISO时间戳（含历史UTC后缀）或由 `/`、`..`、`~`、`至` 分隔的两端区间；按各端来源日历日期筛选，不以 recorded_at 补缺或统一转换时区。

缺失或未知事件日期单列；无效日期、解析失败、重复ID和缺失关系目标列入 issues，退出码2表示提取不完整；该工具不检查完整记录schema或来源哈希。

JSON输出schema_version=2：records为窗口内记录，unknown_dates为全目录未知/无效日期记录，correction_context为双向修正链的跨期背景，relations保留关联，issues列出缺口。

分类默认 unclassified，原topics保留；可选 --routes-file 指定JSON对象，键为路线名、值为非空Python正则，匹配ID、标题和topics的大写文本（下划线转空格），多命中为review，两个状态名为保留名。

使用词边界或明确短语，避免用短子串匹配；路线示例仅演示一种视觉识别/检索项目，可替换为任何研究领域，不会默认启用。
