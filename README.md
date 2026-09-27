# research-trace

跨项目科研留痕技能：记录实验依据、正负结果、失败、路线决定及后续修正，让研究经历能够检索、核验和复盘。

## 安装

将本仓库克隆到技能目录（目标目录需尚不存在）：

```bash
git clone https://github.com/kyrie21z/research-trace.git "${CODEX_HOME:-$HOME/.codex}/skills/research-trace"
```

已有同名技能时先检查并保留本地修改，再合并更新；新建会话加载技能。

## 使用

```text
使用 $research-trace 为当前项目建立科研留痕机制。
使用 $research-trace 归档本次实验结果，并关联已有记录。
使用 $research-trace 为旧结论追加修正，保留原记录。
```

默认接入 `docs/research/`，复用项目已有规则与发布器；需要接入项目时才合并 AGENTS.md 片段，普通归档不会自动改写代理规则。

## 文件

| 路径 | 用途 |
|---|---|
| [SKILL.md](SKILL.md) | 技能入口与执行流程 |
| [assets/PROVENANCE.md](assets/PROVENANCE.md) | 来源等级、发布和追加修正规则 |
| [assets/AGENTS.fragment.md](assets/AGENTS.fragment.md) | 项目接入片段 |
| [assets/templates/record.md](assets/templates/record.md) | 研究事件记录模板 |
| [assets/templates/retrospective.md](assets/templates/retrospective.md) | 一句话要点与最小结果表格的复盘模板 |

研究记录是唯一维护正文，实验产物提供测量事实，复盘引用原记录；不同数据、方法和协议的结论保留各自作用域。

本技能不附带自动发布器；无项目工具时采用手工审阅与发布，哈希一致不代表科学结论正确，也不保证留痕没有遗漏。
