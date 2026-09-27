---
name: weekly-retrospective
description: 基于 Research 记录进行周报、阶段或单假设复盘，以及研究结果对比与论文素材提炼；按用户范围输出精简证据表和结论，不将普通进度查询扩展为完整周报。
---

# 科研复盘

## 先确定输出范围

用户指定的结构、路线、检查点和文件路径优先；已有明确范围时直接整理可审阅结果，不增加例行批准步骤。

- **周报：** 按日期筛选事件，按实际研究路线分节，底座变化与后续建议仅在有内容时加入。
- **单假设或阶段复盘：** 按主题检索，不受本周日期限制，沿假设、实验、结果与决定组织。
- **结果对比：** 只输出所需表格；例如基础检索表与rerank增量表，不强行补齐周报章节。

默认使用 [精简模板](templates/retrospective_template.md)：Hypothesis一句话，Design每点一句话，Result最小充分表格，Conclusion每点一句话；用户要求深入解释时再展开。

## 提取与补读

1. 先读目标项目归档规则（默认 `docs/research/PROVENANCE.md`），按其 AGENTS.md 选用已验证的 Python 3.10+ 环境；提取工具仅依赖标准库，目录与记录schema不同则适配读取，不改写原始记录。
2. 从本技能目录解析 `scripts/extract_weekly_facts.py` 的绝对路径，在目标项目根目录运行（替换下面的解释器和技能路径）：

```bash
"<已验证的Python解释器>" "<本技能目录>/scripts/extract_weekly_facts.py" \
  --records-dir docs/research/records --since YYYY-MM-DD --until YYYY-MM-DD --json
```

工具仅提取元数据，不核验来源哈希或科学结论；JSON v2由 `records`、`unknown_dates`、`correction_context`、`relations`、`issues` 等字段构成，替代旧的裸数组输出。

事件归属依据 occurred_at 的来源日历日期，区间与窗口相交即纳入；未知日期单列，不以 recorded_at 或迁移时间代替；不同来源时区未统一换算，跨日敏感事件须核对原始时间依据。

默认不预设研究领域，保留 topics 并将路线标为 unclassified；需要自动分组时以 `--routes-file <JSON路径>` 指定路线名到正则的映射，可参考 [可选路线示例](references/routes.example.json)，按目标项目调整后使用，多个路线命中标为 review；解析错误和缺失关系会列入 issues 并返回退出码2，修复或披露缺口后再综合，不能当完整提取成功。

输入须为 `<!-- research-record` JSON元数据，字段见 [输入合同](references/record-format.md)；缺少档案时说明来源缺口，不把普通日志伪装成结构化记录。

3. 阅读选中记录正文中的实验条件与限制，并沿 related 按需补读背景；工具双向追踪 corrects/supersedes，跨期修正明确标为后续背景，不冒充本周发现。
4. 单主题任务先用 `rg` 检索 INDEX/records，随后补查指向这些ID的修正关系；不为复盘重放全部历史或运行模型。
5. 关键指标回到记录指定的紧凑实验报告核对，优先保留支持、反例与未定证据；需要来源完整性检查时使用项目归档工具，报告实际检查范围。

## 综合规则

- 明确数据版本、模型、候选集、split角色、指标分母和比较对象；训练规模或协议不同的结果分别列出。
- 增量逐行标注参照方法；消融分支不伪装为连续累加，统一舍入并区分百分比与百分点。
- 区分测量事实、解释假说和项目决定；相关性不自动成为因果，子集修复不自动成为整体改善。
- 保留负结果、受损样本和已有不确定性；未估计的区间不编造，开发集结果不称未见Final Test泛化。
- 路线状态依据当前作用域的决定记录，不预设某条路线成功、失败或永久冻结；因预算停止不等于方法普遍无效。
- 原始动机不可见时写未知，后续归纳明确标注；遇到来源冲突先核对修正链，无法消解则并列披露，实质决策冲突再询问用户。

## 保存与留痕

用户要求文件时直接保存可审阅稿；完整周报默认 `docs/research/weekly/YYYY-MM-DD_to_YYYY-MM-DD_retrospective.md`，其他输出遵循用户路径或仅在对话中呈现。

本技能负责检索与综合，研究事件的发布与修正遵循项目PROVENANCE，并可调用 research-record；若该技能不可用，使用项目既有流程。

纯复盘整理收尾用 `NO_RESEARCH_DELTA` 加原因；新决定、重要纠错或影响旧结论的问题需追加来源记录后引用，归档失败按项目规则报告 `ARCHIVE_PENDING`，不重跑实验。

周报不写入 records 的自动INDEX充当新实验；只有需要导航时更新周报入口，避免第二份人工维护的科研状态账本。
