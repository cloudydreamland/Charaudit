# REPORT — The Ghosts in the Ink (charaudit) · 0.1.0a1

项目报告（2026-10-08）。面向评估者：这是什么、做到什么程度、证据在哪、边界在哪。开发过程账目见 `WORKLOG.md`，路线见 `ROADMAP.md`，立项证据见 `GAP_PROOF.md`。

## 1. 一句话定位

对 prompt、语料、文本管线做**确定性、字符级**的隐形字符与同形字审计：精确到原文偏移的证据报告，不判语义。中文场景优先。

## 2. 能力清单（全部带测试）

| 类别 | 覆盖 | 风险 |
|---|---|---|
| `ZERO_WIDTH` / `BIDI` / `TAG_BLOCK` / `SURROGATE_ORPHAN` / `CONTROL` | 零宽、双向控制、Unicode 标签块、孤立代理、C0/C1 | FORBIDDEN |
| `HOMOGLYPH_UN` | Unicode confusables.txt 18.0.0 过滤版，1,730 个混合文字→ASCII 混淆源 | SUSPICIOUS |
| `HOMOGLYPH_CJK` | 自策展形近字 250 组 / 650 字（一笔之差/部件/偏旁/形近四类，逐组标注） | SUSPICIOUS |
| `SOFT_HYPHEN` | U+00AD + LRM/RLM + 废弃格式符 | SUSPICIOUS |
| `FULLWIDTH_HALF` | 全角字母数字 + 半角假名（NFKC 可归一化） | INFO |
| `PUNCT_VARIANT` | 唯一上下文相关类：按整串主导脚本提示"入侵方"标点 | INFO |

API：`audit_text` / `audit_prompt`（strict）/ `audit_corpus`（流式、常数内存、急切策略校验）/ `diff_visible`（差异归因 + 中文解释）/ `sanitize`（只删不替 + 指回原文的 ChangeLog）。三套预置策略 + 自定义映射，`policy_version`/`table_version` 写入每个 Report。

## 3. 正确性守护（85 个测试）

- 偏移不变量 `finding.text == source[start:end]`：300 例种子 fuzz + 44 万字脚本交替边界用例。
- sanitize：200 例"删区间重建原文"等价 fuzz、UTF-16 surrogatepass 往返稳定、逐项类型拒绝。
- diff：400 例 fuzz 重建不变量、10k 近似相同不变量（100k 实测见 §4）。
- 同形字：西里尔/希腊/日文假名/CJK 已知向量；表指纹三重校验（文件 SHA-256、`_meta.map_sha256` 规范化校验、reload 稳定）。
- 运行方式：`cd 项目目录 && PYTHONPATH=src python -m unittest discover -s tests` → **Ran 85 tests, OK (0.7s)**。

## 4. 实测性能（2026-10-08，Python 3.13.2 / Win11 / 13 代酷睿；完整环境与命令见 benchmarks/RESULTS.md）

- `audit_text`：**0.67–0.85M 字符/秒**（strict 与 neutral 基本同速）。
- `sanitize`：**0.33–0.43M 字符/秒**。
- `diff_visible`：经 S4-2 线性化，100k 近似相同两串 **85.6s → 0.168s（~510×）**；内容完全不同的长文本保持 difflib 原速（非典型用途，如实说明）。
- 样本为种子化合成文本；数字只在同环境可比，禁止脱离环境引用。

## 5. 可审计证据链

- 数据来源：Unicode confusables.txt 18.0.0（原始文件入库 + SHA-256 + License v3 全文入 `licenses/`）；CJK 形近字自策展 MIT 表（策展规则与频次护栏写在数据文件内）。
- 打包表内嵌 `_meta`：来源 URL、版本、原始文件 SHA-256、过滤规则、逐级计数、map 规范化 SHA-256。
- demo 素材：`docs/assets/demo.txt` 由 `scripts/make_demo.py` 对当前代码真实运行生成（含表指纹），可一键复生成。
- 开发账目：组合级 `PIPELINE_STATE.md` + 项目级 `WORKLOG.md` 逐单元记录验证命令与真实结果（含 4 次自测纠错与 2 次执行环境事故，均如实记录）。

## 6. 诚实边界（完整清单见 ROADMAP §已知限制）

- 字符级检测不判语义；"未发现"≠"文本干净"。
- CJK 表是部分覆盖（250 组起步）；常用字命中（请→情晴清精族）是文档化的 REVIEW 提示面。
- PUNCT_VARIANT 上下文相关；ASCII 同形字（1/l 等）刻意未收录。
- sanitize 只删不替：删同形字会留空洞，不会替换成目标字符。
- alpha 阶段（0.1.0a1），未上 PyPI；Trusted Publisher 绑定与 S6 检查完成后才发布。

## 7. 下一步

S5 收尾（CHANGELOG 发布形态、pyproject 终审）→ S6 发布准备（干净 venv quickstart 断言、CI、publish workflow）→ S7 发布（建仓/PyPI/Release）→ S8 推广（一次一帖）→ S9 维护。
