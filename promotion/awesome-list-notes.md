# awesome-list 摸底笔记 — 状态：DRAFT（2026-10-08 实查）

纪律：只投满足收录标准且项目状态匹配的列表；一次一个 PR；投递后把 PR 链接记入组合账本。以下数据全部为 2026-10-08 GitHub API 实抓。

## 候选清单（实抓结果）

| 列表 | stars | 最近 push | 收录方式 | 与 charaudit 的匹配 | 结论 |
|---|---|---|---|---|---|
| corca-ai/awesome-llm-security | 1,709 | 2025-08-20（约 13 个月前，欠活跃但未归档） | 遵循 Awesome Manifesto，"just submit a PR" | 匹配：prompt 注入/审计工具正是其主题域 | **等 PyPI 上线后投**——0★ alpha、不可 pip install 的条目说服力弱，且该列表已一年多无维护迹象，PR 可能石沉大海 |
| promptslab/Awesome-Prompt-Engineering | 6,360 | 2026-10-07（**当天仍在更新，活跃**） | PR 制，README 为分类表格（含 LLM Evaluation Tools 等类目） | 匹配：可入 security/auditing 类目 | **首选**。等 PyPI 上线后提 PR（表格行 + GitHub 链接 + 一句话诚实描述） |
| vinta/awesome-python | ~200k 级 | 活跃 | 极高门槛（成熟度/流行度） | 差距明显 | 不投（诚实评估：0★ alpha 不达标；若干月后若有真实采用再议） |
| crownpku/Awesome-Chinese-NLP | 7,921 | 2023-07-27（3 年未更新） | PR 制 | 主题匹配（中文文本处理）但列表停更 | 不投（维护者大概率不响应；如实记录） |
| lonePatient/awesome-pretrained-chinese-nlp-models | 5,594 | 2026-08-30 | PR 制 | 主题偏预训练模型，charaudit 是质检工具 | 弱匹配，暂不投 |

## 行动顺序（待触发）

1. **触发条件：PyPI 上线**（等用户绑定 Trusted Publisher + PUBLISH_ENABLED=true）。
2. 首投 promptslab/Awesome-Prompt-Engineering：先开 issue 询问类目归属（避免直接 PR 被视为推銷），再按其表格格式提 PR；一次一个列表。
3. 次投 corca-ai/awesome-llm-security（若届时仍活跃）。
4. 每次投递记录：PR/issue 链接、日期、结果（合/拒/无响应天数）——记入组合账本。

## 诚实自评（投递前复核条件）

- 必须已可 `pip install charaudit`；
- 必须仍是诚实措辞（alpha 如实、不夸大检测能力）；
- 若届时 README "Honest boundaries" 与数据表版本有更新，PR 描述同步更新。
