# research-trace

两个并列、可单独安装的科研技能：留痕保存依据，复盘综合证据。

| 技能 | 职责 | 入口 |
|---|---|---|
| `research-record` | 建立研究档案，记录结果、失败和决定，追加旧结论修正 | [SKILL.md](skills/research-record/SKILL.md) |
| `weekly-retrospective` | 按周、阶段或单假设复盘，输出精简结果表与结论 | [SKILL.md](skills/weekly-retrospective/SKILL.md) |

```text
skills/
  research-record/       # 留痕规则、记录模板、项目接入片段
  weekly-retrospective/  # 复盘流程、提取工具、精简模板、回归测试
```

## 安装

克隆到普通工作目录，然后分别复制所需技能到用户技能目录；仓库根目录不再是一个技能。

```bash
git clone https://github.com/kyrie21z/research-trace.git
cd research-trace
research_skill_dir="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$research_skill_dir"
# 每个目标目录必须不存在，已有安装先保留修改并人工合并。
if [ ! -e "$research_skill_dir/research-record" ]; then
  cp -R skills/research-record "$research_skill_dir/research-record"
fi
if [ ! -e "$research_skill_dir/weekly-retrospective" ]; then
  cp -R skills/weekly-retrospective "$research_skill_dir/weekly-retrospective"
fi
```

新会话加载安装后的技能；若项目已有同名技能，先比较项目版与用户版并选择适用版本，避免无意覆盖项目适配。

旧版用户级 `research-trace` 技能现改名为 `research-record`，仓库名称保持不变；更新安装后将旧技能移出发现目录留作备份，并更新自己的调用语句，旧会话上下文不会自动撤回。

## 使用

```text
使用 $research-record 为当前项目建立科研留痕机制。
使用 $research-record 归档本次实验结果，并关联已有记录。
使用 $research-record 为旧结论追加修正，保留原记录。
使用 $weekly-retrospective 复盘本周研究，每个要点一句话，结果用最小充分表格。
使用 $weekly-retrospective 对比指定实验，只输出基础方法表和增量表。
```

留痕默认接入 `docs/research/` 并复用项目规则，复盘读取档案与紧凑报告；两者均不授权重跑实验或改变冻结决定。

## 工具边界与验证

`research-record` 提供工作流与模板，不附带自动发布器；无项目工具时采用手工审阅与发布。

`weekly-retrospective` 的标准库提取器使用目标项目已验证的Python 3.10+，支持显式记录目录、事件日期区间、未知日期单列和修正链；默认无领域分类，可通过 `--routes-file` 提供项目自己的路线映射。

提取器只解析元数据，不核验来源哈希或科学结论，也不保证留痕没有遗漏；完整说明见 [输入合同](skills/weekly-retrospective/references/record-format.md)。

在项目已验证的Python环境中运行回归测试：

```bash
python -m unittest discover -s skills/weekly-retrospective/tests -v
```
