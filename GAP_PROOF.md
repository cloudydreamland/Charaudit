# GAP_PROOF — 为什么"中文隐形字符审计"这个缺口是真的

> 立项复核日：2026-10-07（与上游调研 `NEW_PROJECT_GAP_RESEARCH.md` §A 同日，本文件所有数字均为当日实抓复核，非照抄调研稿）。方法：GitHub REST API（archived/pushed_at/stars）+ pypistats.org（下载量）+ 原文逐条实抓（promptfoo / AWS / arXiv，HTTP 状态与标题核对）。所有数字标注来源与日期，过期不自动更新，引用前请复核。

## 1. 需求侧：维护者已撤退，需求长青，安全侧持续加温

- **对照组信号（品类需求的最硬证据）**：[confusable_homoglyphs](https://github.com/vhf/confusable_homoglyphs) 仓库 **archived: true**（GitHub API 实抓 2026-10-07），最后推送 2024-01-02，166★——但 pypistats 显示 **近 30 天下载 1,377,624 次、近 7 天 436,877 次**（pypistats.org `packages/confusable-homoglyphs/recent`，2026-10-07 读取）。维护者撤退两年半后下载量仍为百万级/月：这是一个"需求已被市场反复验证、而供给端已离场"的品类。
- **威胁面正从代码安全扩散到 LLM 供应链安全**（以下三篇均当日实抓确认存在）：
  - Promptfoo 官方博客（2025-04-10）《[The Invisible Threat: How Zero-Width Unicode Characters Can Silently Backdoor Your AI-Generated Code](https://www.promptfoo.dev/blog/invisible-unicode-threats/)》：演示在 Cursor 规则文件中用零宽字符（U+200B/C/D）编码隐藏指令。原文引句："While these characters are invisible to humans, LLMs see them as distinct, valid Unicode characters in the input stream."
  - AWS Security Blog（2025-09-30）《[Defending LLM applications against Unicode character smuggling](https://aws.amazon.com/blogs/security/defending-llm-applications-against-unicode-character-smuggling/)》（URL 实抓返回 200）——云厂商开始给"Unicode 走私"出防御指南。
  - arXiv [2510.11195](https://arxiv.org/abs/2510.11195)《RAG-Pull: Turning Retrieval into a Code-Injection Channel via Invisible Unicode Perturbations》（标题实抓 2026-10-07）——隐形 Unicode 已被证明是 RAG 检索通道上的代码注入媒介。
  - CSA AI Safety Initiative《Hidden Unicode Instruction Injection in AI Agent Skills》（labs.cloudsecurityalliance.org，搜索索引确认标题与发布日期 2026-03-10；站点直接抓取被 403 拦截，**全文未逐字核读**，诚实标注）。
- **中文侧现状**：NLP 数据清理的通行做法仍是手写正则 `[\u200b-\u200f\u2060\ufeff]` + NFKC。全半角混排、形近字（己/已、末/未、土/士）、CJK 兼容字符这些中文特有盲区，连这条"手写正则"都覆盖不到。

## 2. 供给侧：中文专属审计件为零

GitHub API 实抓（2026-10-07）：

| 仓库 | 星数 | 状态 | 为什么不解决本问题 |
|---|---|---|---|
| [panispani/sanitext](https://github.com/panispani/sanitext) | 45 | 活跃（最后推送 2026-01-04） | 英语场景，清"LLM 指纹"标点，无中文全半角/形近字概念 |
| [ACMCMC/silverspeak](https://github.com/ACMCMC/silverspeak) | 9 | 活跃（2026-07-07） | 定位是"执行与中和同形字攻击"（攻击工具），GPL，非审计库 |
| [shibing624/pycorrector](https://github.com/shibing624/pycorrector) | 6,530 | 活跃（2026-07-25） | ML 模型纠错（错别字），不是 Unicode/字符级审计，重依赖 |
| heckler | 1 | **本次复核未能在 GitHub 搜索定位到该仓库**（调研稿记 1★），暂不计入 | — |

**结论：月下载百万级的品类，供给端只有维护者已归档的英文同形字库 + 几个定位错位的小仓库；中文专属（全半角/形近字/CJK 兼容）的零依赖审计件为零。**

## 3. 我们与"简单拼凑"的边界

不做"正则集合 + replace"的复刻。本项目的可防守差异：

1. **中文优先**：全半角映射、形近字混淆集、CJK 兼容字符（`unicodedata.normalize('NFKC')` 变化点）是西文工具的系统性盲区，也是中文语料最高频的实际污染源。
2. **偏移不变量**（承袭 qiegao/mianju 的品牌承诺）：每个发现必须附带码点偏移，`source[start:end]` 与命中片段逐字节相等，由 fuzz 测试永久守护——审计结论可以精确引用回原文。
3. **场景化 API**：`audit_prompt()`（进模型前的安检）、`audit_corpus()`（语料体检，对接 worddael 切分前清洗）、`diff_visible(a, b)`（解释两个"看起来一样"的字符串为什么不相等——把"肉眼不可见"变成"报告可读"）。
4. **证据链报告**：每条发现 = 类别 + 码点 + Unicode 名称 + 出现次数与偏移 + 处置建议，JSON（机器）与表格（人）双输出，可进 CI。
5. **零必装依赖**：纯 `unicodedata` + 内置数据表，审计器本身可进任何管线的最底层。

## 4. 风险与诚实说明

- **"未发现"≠"证明干净"**：检测基于已知类别清单（零宽/双向控制/同形字/全半角/兼容字符…），不在清单内的异常不报；新 Unicode 版本带来的新类别需要跟进。README 与报告措辞将明确这一边界。
- **零宽字符有合法用途**：某些文字的正字法、水印、防拷贝水印都合法使用不可见字符。审计报告只给"发现+建议"，不做强制删除；任何自动清洗必须是显式 opt-in 并输出改写前后 diff。
- **NFKC 归一化有损**（如 ㍿ → 株式会社）：本库定位"审计+定位"，改写建议必须附带归一化前后对照，不做静默重写。
- **竞品动向**：sanitext 活跃且方向相邻（文本清理），若其扩展到中文场景会压缩时间窗；silverspeak 是攻击工具，与本库"审计"定位正交，不构成直接竞争。
- **未复核项**：调研稿中"社区 debug 3 周字符串不等"的一线案例，本次未追溯原始出处，暂不作为立项证据引用；heckler 未能定位（见上表）。

## 5. 数据来源清单（快照：2026-10-07）

- GitHub REST API：`api.github.com/repos/vhf/confusable_homoglyphs`（archived=true, pushed_at=2024-01-02, stars=166）、`.../repos/shibing624/pycorrector`（stars=6,530）、`.../repos/panispani/sanitext`（stars=45）、`.../repos/ACMCMC/silverspeak`（stars=9），读取于 2026-10-07
- pypistats.org：`api/packages/confusable-homoglyphs/recent` → last_month=1,377,624 / last_week=436,877 / last_day=78,778，读取于 2026-10-07
- Promptfoo 博客 2025-04-10：https://www.promptfoo.dev/blog/invisible-unicode-threats/ （实抓 2026-10-07）
- AWS Security Blog 2025-09-30：https://aws.amazon.com/blogs/security/defending-llm-applications-against-unicode-character-smuggling/ （HTTP 200，实抓 2026-10-07）
- arXiv 2510.11195：https://arxiv.org/abs/2510.11195 （标题实抓 2026-10-07）
- CSA Labs：labs.cloudsecurityalliance.org，2026-03-10（搜索索引确认；直接抓取 403，全文未核读）
- 上游调研：`../NEW_PROJECT_GAP_RESEARCH.md` §A（快照 2026-10-07）
