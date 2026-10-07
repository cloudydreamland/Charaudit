# WORKLOG — charaudit

## 2026-10-07 · A-S1-1 命名查证（S1 完成）

**结论：包名 `charaudit`，展示名 `The Ghosts in the Ink — charaudit`。**

### 查证记录（全部实抓，2026-10-07）

| 检查项 | 命令/方式 | 结果 |
|---|---|---|
| PyPI 包名占用 | `curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/charaudit/json` | **404 → 未占用，可用** |
| GitHub 全站同名仓库 | `api.github.com/search/repositories?q=charaudit+in:name` | **total_count: 0** |
| GitHub 自有命名空间 | `api.github.com/repos/cloudydreamland/charaudit` | 404 → 可建仓 |
| 搜索引擎联想 | 全网精确搜索 `"charaudit"` | 无现有品牌/术语；结果均为 "char audit" 分词模糊匹配（医疗表单、印度判例书、1937 年报纸档等），无负面联想、无明显商标实体。注意点：英语医疗语境有 "chart audit" 一词，SEO 有轻微噪音但不构成冲突 |
| 备选名占用 | PyPI `uniglyph`、`ghostchar` | 均 404（如需切换可用） |
| 负面歧义 | 人工审读 | "char"+"audit" 结构，各主要语言无已知负面义；与既有六包名（helan/worddael/sothstan/siftan/tellan/gewita）风格兼容：展示名负责意象，包名承担功能可搜索性（符合 GROWTH_PLAN §9 搜索发现策略） |

### 展示名决策

- **选定：The Ghosts in the Ink**（5 词，符合 2–5 词规范）——隐形字符是"藏在墨迹里的幽灵"，与 helan "The Veil of Hidden Names" 的意象族一致但不重复（gewita 已占用 "Margins" 意象，避开）。
- 备选（未采用）：The Hollow Ink；Whispers in the Blank。
- 副标题草案（S5 文档阶段定稿）：*Chinese-first invisible-character auditing for prompts, corpora, and text pipelines*。
- 词源声明：`charaudit` 为 char + audit 的现代合成词，不做虚假词源宣称。

### 遗留给 S2

- 数据表来源与许可待清单化：Unicode confusables.txt（Unicode Data Files 许可）、全半角映射（unicodedata 生成）、形近字混淆集（需选定可再分发来源）、双向控制符/标签块/零宽字符清单（Unicode 标准）。
- 正确性标准：AWS 博客证实的 UTF-16 代理对重组问题 → 清洗必须递归并 fuzz 验证。

## 2026-10-07 · A-S3-3 HOMOGLYPH 表（S3-3 完成）

**交付：`HOMOGLYPH_UN`（Unicode confusables.txt 18.0.0 过滤版，1,730 源字符）+ `HOMOGLYPH_CJK`（自策展形近字，250 组 / 650 字）+ classify 扩展 + 28 个新测试；全量 60 测试 OK。**

### 数据采集与许可（全部实抓，2026-10-07）

| 项 | 记录 |
|---|---|
| 原始文件 | `https://www.unicode.org/Public/security/latest/confusables.txt`，头标 Version 18.0.0（Date 2026-08-06），763,128 字节 |
| SHA-256 | `6ed3ee967c9dfdf6677d563c9985182fbc50a2efb7d6059cd57b2e2ce18f5b92`（原始文件已入库 `data/raw/confusables.txt`） |
| 许可 | Unicode License v3（Data Files and Software），全文存 `licenses/unicode-data-files-license.txt`（SHA-256 `e7a93b00…53d96`） |
| 锁定 URL 细节（如实记录） | 截至 2026-10-07 unicode.org 仅钉扎 `/Public/security/15.1.0/` 与 `/16.0.0/`（均已实测 200）；`/18.0.0/` 实测 404，18.0.0 仅经 `/latest/` 提供——故以入库原始文件 + SHA-256 为内容锚点，该细节写入打包表 `_meta.note_pinned_url` |

### UN 表过滤规则与 dry-run 计数（build_tables.py 实际输出，如实记录）

输入 6,712 数据行（全部为 MA 类型；本版本无 ML/SA/SL 行）：多码点 target 跳过 2,459；target 非 ASCII 可打印跳过 2,408；**ASCII 源跳过 5**（`0 1 I ` |` 等 ASCII→ASCII 同形字会误报所有普通文本，归属未来 INFO 类——这是首轮生成 1,735 条后发现并补的规则，重建后 1,730）；保留块排除 110 条（其中全角源 91 条，其余 19 条为 CJK/兼容表意区；另有 64 条全角源因 target 非 ASCII 已在 target 阶段被拦）；保留 **1,730 个源字符**，打包 30,256 字节。多码点 source（如 `030B → 0301 0301`）零条（规则已备）。无多 target 条目。

### CJK 表策展说明（诚实边界）

- **来源**：维护者依据中文语文教学中长期使用的形近字对照自行整理、逐组人工校验；未复制任何第三方数据集。共 **250 组 / 650 字**（覆盖 一笔之差/部件增减/偏旁互换/整体形近 四类，逐组 `kind` 标注）。
- **频次护栏**：组内含最高频约二三十字（的一是不了人我在有他这中大来上国和地到时要说就也）的组暂缓收录——人/入、了/子、大/太/犬、日/曰、上/下 等经典组因此未入表，待 S4 分级策略再评估。护栏清单是维护者依据通用字频常识拟定，非引用特定字频数据集（已在数据文件中如实声明）。
- **误报面（必须说清）**：常用字（请/情/晴/清、自、全、无、于、试等）命中属预期行为，REVIEW 仅是提示；README 诚实边界已写明。

### 设计修正（回改 DESIGN 前的工程决策，均记录在案）

1. **diff 的"隐形"与"易混淆"必须分离**：同形字是可见字符，原 `classify()≠None 即 hidden` 的语义会把 `с` 标成隐形——新增 `is_invisible()`（INVISIBLE_CATEGORIES 五类），diff 的 hidden/equal_visible 只认隐形类；`explain()` 新增"易混淆字符"行。`equal_visible` 对隐形字符语义不变（旧测试全过）。
2. **Finding 新增 `confusable_with` 可选字段**（默认 ""，向后兼容）：审计证据输出"这个字符会被误认成什么"（`с`→`c`、`己`→`已/巳`、run `сο`→`cO` 欺骗渲染）。
3. **POLICY_VERSION 1→2**：三套预置全部纳入两个 HOMOGLYPH 类（SUSPICIOUS/REVIEW，所有预置一致——按 DESIGN §2 表格默认风险），自定义映射可升级为 FORBIDDEN/REMOVE。
4. **TABLE_VERSION 扩展**：`2026.10-unicode15.1.0+confusables18.0.0`；新增 `TABLE_FINGERPRINTS`（打包表 SHA-256，测试断言与文件一致 + `_meta.map_sha256` 与规范化 map 一致 + reload 稳定）。

### 测试与验证

- 新增 `tests/test_homoglyph.py` 28 用例：混淆向量（西里尔 с→c、希腊 Ο→O、己/已/巳、sеcure/paypal 样式）、表内容边界（无 ASCII 源、无 CJK 入 UN 表、全角排除）、指纹三重校验、策略/sanitize/diff 集成、reload 稳定。
- 旧测试修正 4 处：`policy_version` "1"→"2"；"干净文本"样例改为纯 ASCII（干/净 本身在策展表中，命中是**正确行为**）；两个 fuzz 的"可见"判定改用 `is_invisible` 并向字母表加入 с/己/已；sanitize 字母表加同形字验证 REVIEW 不删。
- 过程中发现并修复：打包 CJK 表加载时误将字符值当 hex 解析（ValueError，首跑即拦截）。
- 最终：`PYTHONPATH=src python -m unittest discover -s tests` → **Ran 60 tests, OK**（0.09s，seed 固定可复现）。
- README 三个示例输出（paypal 域名 / 知己知彼 / diff）均为当前代码实跑核实。

### 遗留给 S3-4

- `audit_corpus` 流式迭代器；SOFT_HYPHEN / FULLWIDTH_HALF / PUNCT_VARIANT 三个 INFO 类（全半角映射按 DESIGN §5 由 NFKC 运行时派生，无数据文件）。

## 2026-10-07 · A-S3-4 流式语料审计 + INFO 类（S3-4 完成，S3 全部完成）

**交付：`audit_corpus` 流式审计 + `SOFT_HYPHEN`（SUSPICIOUS）/ `FULLWIDTH_HALF`、`PUNCT_VARIANT`（INFO）三类 + 20 个新测试；全量 80 测试 OK。POLICY_VERSION 2→3。**

### 实现要点与设计决策

1. **FULLWIDTH_HALF 范围修正（重要）**：最初按 FF01–FF5E 全角区段整体收录，首跑即发现与 PUNCT_VARIANT 语义冲突——全角标点（，！？（）FF0C/FF01/FF1F/FF08/FF09）被静态归类 FULLWIDTH_HALF，PUNCT_VARIANT 的"少数文案标点"判定落空。修正为**全角字母数字（FF10–FF19/FF21–FF3A/FF41–FF5A）+ 半角假名（FF61–FF9F）**，全角标点移交 PUNCT_VARIANT 上下文判定。此决策已符合 DESIGN §2 原意（"中文/西文标点混排"归 PUNCT_VARIANT），DESIGN §5 的"只取 ASCII 全角区段"注释按实际收窄范围理解（字母数字）。
2. **PUNCT_VARIANT 是唯一上下文相关类别**：`classify()` 保持无上下文（对标点恒返回 None，防单脚本文本噪音）；扫描器按整串主文案语境（是否含 CJK 区段 0x2E80–0x9FFF/F900–FAFF/AC00–D7AF）判主导脚本，只报"入侵方"标点：中文语境报 ASCII 标点 `",;:?!()\"'"`，非中文语境报全角标点 `，；：？！（）`。confusable_with 指向主导脚本对应标点（如 `,`→`，`、`"`→`“”`）。句点/连字符刻意不入表（3.14 小数点是合法混用）。
3. **audit_corpus 急切校验 + 惰性消费**：首版把 `resolve_policy` 写在生成器函数体内，调用时不执行（生成器惰性），坏策略名要等首次迭代才炸——改为普通函数先校验再返回内部生成器。测试用"生成器陷阱"验证：坏策略在消费前抛 ValueError，可迭代体一次都不被执行。
4. **SOFT_HYPHEN 类**：U+00AD + U+061C（Arabic letter mark）+ U+180E（蒙古元音分隔符，Unicode 6.3 起 Cf）+ U+200E/200F（LRM/RLM）+ U+206A–206F（废弃格式符），SUSPICIOUS/REVIEW 全预置一致；归入 INVISIBLE_CATEGORIES（diff 视为隐藏字符）。
5. **NEUTRAL 预置构造顺序 bug（自测拦截）**：初版 `{c: REVIEW for c in ALL}` 把 INFO 类也覆盖成 SUSPICIOUS，与"INFO 在所有预置保持 INFO"不一致——修正为 FORBIDDEN+SUSPICIOUS→REVIEW、INFO 类保持 INFO。

### 测试与验证

- 新增 `tests/test_corpus_info.py` 20 用例：软连字符/方向标记全预置向量、全角字母数字+半角假名 INFO 向量（Ａｐｐｌｅ１２３/ｱｲｳ，纯 ASCII/全角假名不误报）、标点混排双向向量与偏移不变量、classify 上下文无关性、策略开关、`audit_corpus` 顺序/惰性/急切校验/逐项 TypeError/空输入。
- 过程中发现并修复 4 处自测错误：`boom` 误写成普通函数（应为生成器）；NEUTRAL 覆盖 INFO 类（见上）；"再见"的"见"恰在自家策展表（贝/见组）——换用实测不在表中的"和平"；方向标记向量计数笔误 3≠4。
- 最终：`cd /e/n_projects/charaudit && PYTHONPATH=src python -m unittest discover -s tests` → **Ran 80 tests, OK**。注意：本轮曾有一次未显式 cd 的后台运行误入其他项目 tests 套件（S3-2 同款事故），已终止重跑——教训再次确认：测试命令必须显式 cd。
- README 新增 `audit_corpus` 示例，三行输出实跑核实；诚实边界新增 PUNCT_VARIANT 上下文规则说明。

### S3 阶段收尾状态

- 四个实现单元（S3-1 骨架+FORBIDDEN、S3-2 sanitize+diff、S3-3 HOMOGLYPH 双表、S3-4 corpus+INFO 类）全部完成；DESIGN §2 十类字符中九类已实装（`PUNCT_VARIANT` 为上下文类）。
- 下一阶段 S4 加固：性能基准（如实实测，附环境与命令）、fuzz 加压、失败模式梳理、sanitize/diff 与新类别的交互边界。

## 2026-10-08 · A-S4-1 性能基准 + 边界 fuzz（S4-1 完成）

**交付：`benchmarks/run_bench.py`（可复现、种子化、纯 stdlib）+ `benchmarks/RESULTS.md`（真实运行逐字记录）+ `tests/test_boundaries.py` 5 个边界用例；全量 85 测试 OK（1.5s）。**

### 实测结果（环境：Python 3.13.2 / Win11 / 13 代酷睿，2026-10-08，详见 benchmarks/RESULTS.md）

- `audit_text`：**0.67–0.83M 字符/秒**（neutral 含 PUNCT_VARIANT 后处理与 strict 基本同速）。
- `sanitize`：~0.33–0.40M 字符/秒，符合"至少两遍审计"预期。
- `diff_visible`：小样本正常（0.5M/0.16M 字符/秒），但**存在实测性能悬崖**——6 万字 CJK 密集样本 6.7 秒；更严重的是边界测试实测**近乎相同**的 10 万字符两串耗时 **85.6 秒**（10k 时 0.87s，5k 完全相同 0.16s）——即使最佳情形也超线性。归因 `difflib.SequenceMatcher(autojunk=False)` 在高重复文本上的回溯代价（关 autojunk 保正确性）。**如实记录为已知限制**，确立下一单元 A-S4-2：裁公共前后缀 + 中段定向比较的线性路径，修完必须复跑基准对比。

### 过程记录

- 基准脚本首跑即暴露 `bench()` 关键字冲突（policy 撞 repeats），修正透传后跑通。
- 边界测试两处算术笔误自测拦截：6×60000=360000≠300001（改 50000）；16 个 ZWSP 拼成连续块被合并为 1 个 finding（改为周期插入）——测试断言修正是测试的事，库行为全程正确。
- 100k diff 测试使套件达 85s，与测量目的一致后缩至 10k 并在测试内注释保留 100k 实测数字（不掩盖、不假装快）。
- 验证：`cd /e/n_projects/charaudit && PYTHONPATH=src python -m unittest discover -s tests` → **Ran 85 tests, OK (1.524s)**；基准与补充测量均为实跑输出。

### 遗留给 S4-2

- diff_visible 线性化改造 + 基准复跑对比（目标：100k 近似相同从 85.6s 降到亚秒级，如实报告达到与否）。

## 2026-10-08 · A-S4-2 diff_visible 线性化（S4-2 完成，S4 阶段完成）

**交付：`diff_visible` 公共前后缀裁剪改造 + 基准复跑对比（RESULTS.md 新增前后对照表）；全量 85 测试 OK（0.69s）。**

### 实现与验证

- 改动仅 `src/charaudit/diff.py`：`_common_prefix/_common_suffix` 先行，中段才进 `SequenceMatcher(autojunk=False)`；equal 前后缀段偏移重排后，segments 仍满足"拼接还原 a/b"不变量与 hidden/op 语义。
- **实测前后对比（同机同法，详见 benchmarks/RESULTS.md 对照表）**：
  - 100k 近似相同两串：**85.6s → 0.168s（约 510 倍）**，segments=2、重建不变量断言通过；
  - 100k 完全相同：0.166s（直裁不进 difflib）；
  - 60k CJK 密集：6.70s → 0.097s；6k 混合：38.5ms → 8.6ms；短样本持平；
  - audit_text / sanitize 各场景无回退。
- 诚实边界：内容完全不同的长文本不走裁剪路径，保持 difflib 原速——该场景非本库典型用途，未额外优化，已写入 RESULTS.md。
- 验证：`cd /e/n_projects/charaudit && PYTHONPATH=src python -m unittest discover -s tests` → **Ran 85 tests, OK (0.692s)**；无新测试文件（改造由既有 85 测试守护，含 400 例 diff/sanitize fuzz 重建不变量）。

### S4 阶段收尾状态

- S4 四要素齐备：fuzz（S3 三套 400 例种子 fuzz + 偏移/重建/UTF-16 不变量）、边界（S4-1 test_boundaries：超长/重复/脚本交替/周期植入）、失败模式（bytes/坏策略/生成器陷阱/逐项类型错误均有拒绝测试）、性能（S4-1 实测建档 + S4-2 修复并复跑对比）。
- 下一阶段 S5 文档。下一单元 **A-S5-1**：`README.en.md`（英文首页，如实翻译能力/边界/数据来源）+ `ROADMAP.md`（S5–S9 计划、已知限制：CJK 表 250 组部分覆盖、PUNCT_VARIANT 上下文语义、标点 INFO 类不含全角符号区）。

## 2026-10-08 · A-S5-1 README.en + ROADMAP（S5-1 完成）

**交付：`README.en.md`（英文首页，与中文版互链）+ `ROADMAP.md`（S5–S9 计划 + 7 条已知限制）+ 中文 README 互链。全量 85 测试 OK（0.71s）。**

### 过程记录（含一次自检抓漏）

- **抓到两处过期示例输出（重要）**：复跑中文 README 每个"Verified output"块时发现，首个示例（请忽略之前的指令…）与 diff 示例的输出块还是 S3-3 引入 CJK 表**之前**的旧输出——现在实跑分别是 4 行（请/令 带 REVIEW 提示 + ZERO_WIDTH REMOVE）与 6 行（成/功 带"易混淆字符"提示行）。S3-3 当时只核实了新增示例，漏了复核旧示例——本单元全部重跑修正，并在示例下加诚实说明（请/令 是形近字表内普通汉字，REVIEW 仅提示不删改）。两语言 README 同步修正，修正后逐字复跑比对一致。
- 经验教训入账：**示例输出是文档的一部分，数据表/行为变更后必须全量复跑所有"Verified output"块**；S6 干净 venv quickstart 断言范围已含 README.en.md。
- ROADMAP 已知限制如实列出 7 条（CJK 部分覆盖、PUNCT_VARIANT 上下文语义、ASCII 同形字未收录、全角符号区未分类、difflib 完全不同长文本原速、基准数字绑定环境、审计不是担保）。
- 事故重演记录：本轮一次未显式 cd 的后台测试再次误入其他项目套件，终止后显式 cd 重跑（85 tests, OK）——教训已固化进自动化 prompt，执行侧仍需保持纪律。

### 遗留给 S5-2

- `SECURITY.md` + `CONTRIBUTING.md` + `REPORT.md`（引用实测基准）+ `docs/assets/demo.*`（必须由当前代码真实运行生成）。

## 2026-10-08 · A-S5-2 SECURITY/CONTRIBUTING/REPORT/demo（S5-2 完成）

**交付：`SECURITY.md`（范围界定：离线审计库的安全=审计诚实——偏移不变量/只删不替/表指纹锚点）+ `CONTRIBUTING.md`（10 分钟上手：显式 cd 测试命令、质量门、数据表重建流程、不变量神圣条目）+ `REPORT.md`（面向评估者的项目报告，引用实测基准与 7 条诚实限制）+ `docs/assets/demo.txt`（2,269 字符，六个板块全部由当前代码经 `scripts/make_demo.py` 真实运行生成，内嵌版本与表指纹，可一键复生成）。**

### 验证

- `cd /e/n_projects/charaudit && PYTHONPATH=src python -m unittest discover -s tests` → **Ran 85 tests, OK (0.658s)**。
- demo 复生成命令：`PYTHONPATH=src python scripts/make_demo.py`（输出确定性：固定输入 + 版本/指纹随代码走）。
- REPORT 中的性能区间（audit 0.67–0.85M、sanitize 0.33–0.43M 字符/秒）与 benchmarks/RESULTS.md 两轮实测一致，未引用未测数字。

### 遗留给 S5-3（S5 收尾）

- CHANGELOG 整理成发布形态（0.1.0a1 条目终审）；pyproject 元数据终审（keywords/classifiers/urls）；README 两语言互查。

## 2026-10-08 · A-S5-3 S5 收尾（S5 阶段完成）

**交付：CHANGELOG 发布形态终审 + pyproject 元数据终审 + 两语言 README 互查。全量 85 测试 OK（0.667s）。**

### 终审内容

- CHANGELOG：修正两处过期表述——"80 tests"→85（S4-1 边界测试后未同步）；"performance benchmarks land in S4"已落地（S4-1/S4-2），改为如实描述基准与 demo 资产已存在。补记文档资产条目（双语 README/ROADMAP/SECURITY/CONTRIBUTING/REPORT/benchmarks/demo）。alpha 措辞核查：Development Status :: 3 - Alpha、版本 0.1.0a1、无 stable 宣称 ✓。
- pyproject：keywords 补 homoglyph/confusables/text-processing（9 个）；classifiers 补 Natural Language :: English（README.en.md 实存）；TOML 解析验证通过；wheel 重建验证通过（build_check 即删）。
- README 互查：中文版 Evidence 节补 ROADMAP 与英文版链接（与英文版对齐）；四组关键示例输出复跑（首示例 3 findings、diff equal_visible=True + explain 5 行=README 块 6 行）全部一致。

### S5 阶段收尾状态

- S5 三单元完成（README.en+ROADMAP / SECURITY+CONTRIBUTING+REPORT+demo / 收尾终审），S0–S5 全部完成。
- 下一阶段 S6 发布准备。下一单元 **A-S6-1**：干净 venv `pip install .` + 两语言 README quickstart 逐字断言（脚本化断言，输出块不匹配即失败）+ CI workflow（GitHub Actions，3.10–3.13 矩阵，零依赖安装 + 全量测试）。

## 2026-10-08 · A-S6-1 干净 venv 验证 + quickstart 断言 + CI（S6-1 完成）

**交付：`scripts/assert_quickstart.py`（双层守卫：期望输出块必须逐字存在于两语言 README + 实跑 stdout 必须与之相等；子进程剥离 PYTHONPATH——验证的是安装包而非 src）+ 干净 venv 全流程验证 + `.github/workflows/ci.yml`（ubuntu+windows × 3.10–3.13 矩阵：全量测试、数据表确定性重建 diff 断言、干净安装 quickstart 断言）。**

### 验证（真实执行）

- 干净 venv：`python -m venv build_venv && pip install .`（build isolation 自动取 setuptools）→ 安装位 build_venv/Lib/site-packages/charaudit，版本 0.1.0a1。
- **quickstart 断言（干净 venv 内，已安装包）：5/5 blocks verified against both READMEs**；套件在 venv 内同样 OK。
- 首跑暴露 Windows 管道 stdout 的 CRLF 问题（内容逐字相同仅换行符差异），按平台换行归一化后通过——归一化只处理 `\r\n`，不改内容。
- 事故重演：本轮 venv 首建落到上级目录（cwd 重置），已删并以显式 cd 重做——显式 cd 纪律再次生效。
- workflow YAML 解析验证通过（本地 yaml.safe_load）；推送后实际运行状态取决于 S7 建仓。
- 回归：`cd /e/n_projects/charaudit && PYTHONPATH=src python -m unittest discover -s tests` → **Ran 85 tests, OK (0.691s)**。

### 遗留给 S6-2

- publish workflow（Trusted Publisher，environment `pypi`，**PyPI 侧绑定前绝不触发**）+ sdist/wheel 构建产物内容清单终检。

## 2026-10-08 · A-S6-2 publish workflow + 构建产物终检（S6-2 完成，S6 阶段完成）

**交付：`.github/workflows/publish.yml`（release published / workflow_dispatch 触发；tag 与 pyproject 版本一致性门；发布 job 额外受仓库变量 `PUBLISH_ENABLED == "true"` 门控——Trusted Publisher 绑定前绝不触碰 PyPI，构建产物照常生成上传 artifact）+ `MANIFEST.in`（sdist 补齐双语 README/CHANGELOG/ROADMAP/SECURITY/CONTRIBUTING/REPORT/demo）+ `scripts/check_dist.py`（sdist/wheel 内容清单断言器）。**

### 终检结果（真实构建，dist_check 即删）

- wheel（charaudit-0.1.0a1-py3-none-any.whl）：7 模块 + 两数据 JSON + dist-info/licenses/LICENSE；**零越界条目**（仅 charaudit/ 与 dist-info/ 前缀）。
- sdist（charaudit-0.1.0a1.tar.gz）：pyproject/MANIFEST/双 README/CHANGELOG/ROADMAP/SECURITY/CONTRIBUTING/REPORT/LICENSE/demo.txt/两数据 JSON 全在；**data/raw 763KB 原始文件未入**。
- 决策记录：sdist 含 tests/ 是 setuptools 无 git 元数据时的默认行为，与下游打包者可直接跑测试的通行实践一致——**保留**，check_dist.py 相应断言改为只禁 data/raw 并注释理由。
- 回归：`cd /e/n_projects/charaudit && PYTHONPATH=src python -m unittest discover -s tests` → **Ran 85 tests, OK**。事故重演：本轮又一次 cwd 重置（dist_venv 落上级目录），删后显式 cd 重做。

### S6 收尾状态与发布就绪度（如实）

- S6 两单元完成：干净安装断言、CI、publish workflow、构建产物清单全部就绪。
- S7 拆解：**S7-1 GitHub 建仓 + push（gh 已认证，可立即执行）**；S7-2 PyPI 上传（硬前置：用户在 pypi.org 绑定 Trusted Publisher 并设仓库变量 PUBLISH_ENABLED=true，在此之前发布 workflow 只产 artifact 不上传）；S7-3 GitHub Release（Release 触发 publish workflow，无 TP 时仅构建）。

## 2026-10-08 · A-S7-2 对齐 + tag + GitHub Release（S7-2 完成，S7 除 PyPI 上传外全部完成）

**交付：本地/远端对齐（fetch 成功，网络恢复；reset 到 8bad2bb，弃用等价提交 c9bafeb）+ tag v0.1.0a1 + GitHub Release https://github.com/cloudydreamland/Charaudit/releases/tag/v0.1.0a1（CHANGELOG 摘录 + alpha 状态如实说明 + demo.txt 资产）。**

### publish workflow 首次实战行为（按设计，如实记录）

Release 触发 publish.yml（run 37672667949，completed/success）：**gate=success（PUBLISH_ENABLED 未设 → 判定不发布）、build=success（sdist+wheel 已构建并上传为 workflow artifact）、publish=skipped**——全程未触碰 PyPI，门控设计与实际行为一致。

### 验证

- `git fetch origin && git reset --hard origin/main` → HEAD=8bad2bb（与远端一致，c9bafeb 弃用）。
- Release 页含 demo.txt 资产；tag v0.1.0a1 指向 8bad2bb。
- 回归：**Ran 85 tests, OK**（本轮无代码改动，例行过门）。
- 仓库实况：stars=0（新仓如实记录）。

### 遗留与状态

- S7 剩余唯一动作：PyPI 上传——**等用户**在 pypi.org 绑定 Trusted Publisher 并设仓库变量 PUBLISH_ENABLED=true（此后任何一次 Release/workflow_dispatch 都会把已构建的 artifact 推上 PyPI）。
- 下一单元 **A-S8-1**：首发帖草稿（中文 V2EX 版 + 英文 r/Python 版；结构：问题/最短复现/现有方案不足/诚实边界/安装；凭证缺失只出草稿并入等用户清单）。

## 2026-10-08 · A-S8-1 首发帖草稿（S8-1 完成）

**交付：`promotion/v2ex-zh.md`（中文，分享创造节点）+ `promotion/reddit-python-en.md`（英文 r/Python）——结构按管线 §4-S8：问题（三个实抓案例：promptfoo 2025-04 零宽注入 / AWS 2025-09-30 标签块与代理对重组 / 西里尔同形字钓鱼）→ 现有方案缺口（confusable_homoglyphs 月下载约 137 万但 2024-01 起归档且只管同形字；llm-guard 归档）→ 最短复现（README 已实跑核实的输出块）→ 诚实边界（不判语义/非防火墙/alpha 未上 PyPI/CJK 提示面）→ 源码安装 → 实测性能（引用 RESULTS.md）→ 征集意见三问。**

### 状态与纪律

- **DRAFT**：两帖均标记 DRAFT，等社区凭证；发布时一次一帖，链接回填账本。
- 数字纪律自查：草稿只引用 GAP_PROOF 实抓证据与 RESULTS.md 实测数字，无编造用户/星数/性能；alpha 全文如实。
- 提交 e05ae54 已推送（含 S7-2/S8-1 WORKLOG 补记）；回归 **Ran 85 tests, OK (0.78s)**。事故记录：本轮第 4 次踩"未显式 cd 后台跑测试"坑（已终止重做），该模式在自动化长会话中反复出现——后续执行轮次必须在任何测试命令前带显式 cd。

### 遗留给 S8-2

- Show HN 草稿（英文，更短更技术）+ awesome-list 摸底（实查候选 list 收录标准：awesome-llm、awesome-python-security 等，不盲投）。
