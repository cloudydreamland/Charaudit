# charaudit 基准结果（真实运行，非虚构）

- 日期：2026-10-08（当地时间 00:35 前后）
- 命令：`cd /e/n_projects/charaudit && PYTHONPATH=src python benchmarks/run_bench.py`
- 环境：Python 3.13.2 (64bit) / Windows-11-10.0.26200-SP0 / Intel64 Family 6 Model 183（即 13 代酷睿桌面级，具体型号未单独核验）/ unicodedata 15.1.0
- 方法：样本为**合成文本**（`random.Random(20261008)` 从固定字符池生成，非真实语料）；每格测 5 次取 best/median（`time.perf_counter`）；数字只在同机同版本下可比，不构成跨库对比承诺。

## 原始输出（逐字粘贴，2026-10-08 实跑）

```text
== charaudit benchmark ==
python     : 3.13.2 (64bit)
platform   : Windows-11-10.0.26200-SP0
processor  : Intel64 Family 6 Model 183 Stepping 1, GenuineIntel
unicodedata: 15.1.0
method     : best/median of 5 runs per cell, time.perf_counter, seeded samples (seed=20261008)

operation / sample                                               best(ms)  median(ms)  best chars/s
audit_text strict   | prompt-short (~120 chars, mixed, planted)      0.15        0.16       783,801
audit_text neutral | prompt-short (~120 chars, mixed, planted)       0.16        0.26       771,208
sanitize strict    | prompt-short (~120 chars, mixed, planted)       0.32        0.34       379,387
diff_visible       | prompt-short (~120 chars, mixed, planted)       0.23        0.26       512,601
audit_text strict   | doc-medium (~6k chars, mixed, planted)         7.23        7.71       829,921
audit_text neutral | doc-medium (~6k chars, mixed, planted)          7.26        7.48       826,697
sanitize strict    | doc-medium (~6k chars, mixed, planted)         14.96       15.29       401,059
diff_visible       | doc-medium (~6k chars, mixed, planted)         38.50       38.89       155,862
audit_text strict   | cjk-dense (~60k chars, planted)               88.00       89.43       681,846
audit_text neutral | cjk-dense (~60k chars, planted)                89.95       90.83       667,059
sanitize strict    | cjk-dense (~60k chars, planted)               183.31      187.54       327,320
diff_visible       | cjk-dense (~60k chars, planted)              6704.02     6739.80         8,950

findings per sample (strict):
  prompt-short (~120 chars, mixed, planted): 22 findings, stats={'HOMOGLYPH_CJK': 12, 'ZERO_WIDTH': 2, 'PUNCT_VARIANT': 6, 'HOMOGLYPH_UN': 2}
  doc-medium (~6k chars, mixed, planted): 1078 findings, stats={'PUNCT_VARIANT': 365, 'HOMOGLYPH_CJK': 683, 'ZERO_WIDTH': 14, 'SOFT_HYPHEN': 5, 'HOMOGLYPH_UN': 11}
  cjk-dense (~60k chars, planted): 11283 findings, stats={'HOMOGLYPH_CJK': 10805, 'PUNCT_VARIANT': 358, 'ZERO_WIDTH': 68, 'HOMOGLYPH_UN': 32, 'SOFT_HYPHEN': 20}
```

## 观察与诚实结论

1. **audit_text**：0.67–0.83M 字符/秒，且 neutral（含 PUNCT_VARIANT 后处理）与 strict 基本同速——查表路径不是瓶颈，适合语料级批处理。
2. **sanitize**：约为 audit_text 的一半（~0.33–0.40M 字符/秒），符合"至少两遍审计"的实现预期，无线性异常。
3. **diff_visible 存在实测性能悬崖**：6 万字 CJK 密集样本（高重复字符率）6.7 秒（~9k 字符/秒），而 6k 混合样本仅 38ms。补充测量（同机同日，S4 边界测试中发现）：**近乎相同的两串**（仅末尾差 1 个 ZWSP）在 10k 字符时 0.87s、**100k 字符时 85.6s**；完全相同的 5k 串 0.16s——即使最佳情形也是超线性。原因与 `difflib.SequenceMatcher(autojunk=False)` 在高重复文本上的超线性回溯一致（关闭 autojunk 是为正确性：热门字符不当垃圾过滤，代价是此类样本变慢）。**已于 A-S4-2 修复**（见下节）。
4. 合成样本中形近字/标点混排按设计大量命中（cjk-dense 10.8k 条 HOMOGLYPH_CJK）——即 README 声明的 REVIEW 提示面，不是性能问题。
5. 样本生成、计时方法全部在 `run_bench.py` 中，任何人可复跑；不同机器/Python 版本数字会不同，禁止脱离环境引用本页数字。

## A-S4-2 修复后的复跑对比（2026-10-08，同机同方法）

改动：`diff_visible` 先裁公共前后缀、仅对中段跑 SequenceMatcher（`src/charaudit/diff.py`），segments 语义与重建不变量不变；全量测试 85 个保持全绿。

| 场景 | 修复前 | 修复后 | 备注 |
|---|---|---|---|
| diff 100k 近似相同（末尾差 1 ZWSP） | 85.6 s | **0.168 s**（~510×） | segments=2，重建不变量断言通过 |
| diff 100k 完全相同 | （同量级） | 0.166 s | 公共前后缀直裁，不进 difflib |
| diff 60k CJK 密集（仅末尾 1 字符差） | 6.70 s | **0.097 s** | best chars/s 8,950 → 616,624 |
| diff 6k 混合样本（末尾 1 字符差） | 38.5 ms | **8.6 ms** | 155,862 → 698,820 chars/s |
| diff 短 prompt | 0.23 ms | 0.17 ms | 持平（噪声内） |
| audit_text / sanitize 全部场景 | — | 持平 | 无回退（87ms/175ms 档位不变） |

复跑命令不变（见本文件开头）。完全不同内容的长文本两串不经过裁剪优化，行为与修复前一致（difflib 原速），此场景不在本库典型用途内，未做额外优化——如实说明。
