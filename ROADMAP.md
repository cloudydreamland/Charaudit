# ROADMAP — The Ghosts in the Ink（charaudit）

状态基线：2026-10-08，版本 0.1.0a1（pre-release）。本文件只写计划与已知限制，不写承诺性数字；完成情况以 `PIPELINE_STATE.md`（组合账本）与 `WORKLOG.md`（项目日志）为准。

## 已完成（S0–S4）

| 阶段 | 内容 | 证据 |
|---|---|---|
| S0 立项 | 四路调研空白方向 + 关键数字实抓复核 | GAP_PROOF.md |
| S1 命名 | charaudit / The Ghosts in the Ink，PyPI/GitHub 占用查证 | WORKLOG 2026-10-07 |
| S2 设计 | 10 类枚举 × 三级风险 × 三预置策略 + 正确性标准 | DESIGN.md |
| S3 实现 | FORBIDDEN 五类、sanitize、diff_visible、HOMOGLYPH_UN/CJK 双表、audit_corpus、INFO 类 | 85 tests |
| S4 加固 | 性能基准建档、diff 线性化（100k 近似相同 85.6s→0.168s）、边界 fuzz | benchmarks/RESULTS.md |

## 当前进行（S5 文档）

- [x] A-S5-1 `README.en.md`（英文首页，与中文版互链）+ `ROADMAP.md`（本文件）
- [ ] A-S5-2 `SECURITY.md` + `CONTRIBUTING.md` + `REPORT.md`（含实测基准引用）+ `docs/assets/demo.*`（由当前代码真实运行生成）
- [ ] S5 收尾：CHANGELOG 整理成发布形态、pyproject 元数据终审

## 计划（顺序执行，不设日期承诺）

### S6 发布准备

- 干净 venv `pip install` + README quickstart 逐字断言通过（含 README.en.md）
- CI workflow（GitHub Actions：3.10–3.13 全量测试；零依赖安装）
- publish workflow：Trusted Publisher（environment `pypi`）——**等用户在 PyPI 账户侧绑定后方可发布**

### S7 发布

- GitHub 建仓（`cloudydreamland/Charaudit`，gh 已认证）并 push
- PyPI 发布（前置：Trusted Publisher 绑定 + S6 全过）；版本 0.1.0a1，**不得标注为 stable**
- GitHub Release（changelog 摘录 + demo 资产链接）

### S8 推广（一次一帖，链接记入组合账本）

- 首发帖草稿：问题（隐形字符/同形字攻击的真实案例）→ 最短复现 → 现有方案缺口（confusable_homoglyphs 归档、pysubs2 只解析不质检等）→ 边界声明 → 安装方式
- 渠道按组合 PROMOTION_TARGETS 执行；V2EX/Reddit/HN 需要账户凭证，缺凭证时只出草稿
- awesome-list 申请（核对各列表收录标准后再提交）；上游（pysubs2、LlamaFactory 生态）集成评估

### S9 维护

- issue 首响、小版本迭代、月度复盘（组合账本 review 运行）
- Unicode confusables 新版本发布时重跑 `scripts/build_tables.py` 更新表并复跑测试与基准

## 已知限制（如实）

1. **CJK 形近字表是部分覆盖**：250 组 / 650 字，起步规模；频次护栏刻意排除最高频字（日/人/大 所在组不收录），待引入分级策略后重评。
2. **PUNCT_VARIANT 是唯一的上下文相关类别**：`classify()` 对标点恒返回 None，混排判定在扫描器内按整串主导脚本进行；单脚本文本零噪音，混排文本只提示不判错。
3. **ASCII 同形字（1/l、I/l、0/O）未收录**：会造成全文本噪音，可能在未来以 INFO 类别引入。
4. **全角符号区（＋＄％等 FF01–FF0F 等）未分类**：当前只收全角字母数字与全角标点，符号区待评估。
5. **diff_visible 对"内容完全不同"的长文本保持 difflib 原速**：裁剪优化只加速有公共前后缀的输入（本库典型用途）；完全随机长文本对比不是本库目标场景。
6. **基准数字绑定环境**：benchmarks/RESULTS.md 的数字仅在记录的机器/Python 版本下可复现，禁止脱离环境引用。
7. **审计不是担保**："未发现"只指"该策略、该数据表版本下未命中"；本库不判断语义，不证明文本未被投毒。

## 远期想法（不定承诺）

- `similar_names()` 成对相似度 API（typosquat 包名/域名检查场景）
- CJK 表按使用场景分级（corpus 宽松 / name-check 严格）
- 与组合内 E（变体引擎）、L（输入安检）共享归一化内核
