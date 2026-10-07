# DESIGN — The Ghosts in the Ink（charaudit）

状态：S2 设计稿（2026-10-07，A-S2-1）。S3 实现以本文件为基准；实现中发现设计错误时回改本文件并在 WORKLOG 记录理由。
包名：`charaudit`（S1 已查证可用）；展示名：The Ghosts in the Ink。

## 1. 定位与边界（先说不是什么）

- **是**：确定性、字符级的隐形/可疑 Unicode 审计库，面向 prompt、语料、文本管线，中文场景优先。
- **不是**：语义检测器（不识别同义词伪装/谐音语义）；不是"防注入防火墙"（输出是证据报告，不承诺阻断攻击）；"未发现"只表示"该策略版本、该数据表版本下未命中"，不等于文本安全。

## 2. 字符类别与风险分级

类别用稳定枚举名（数据表版本化，随 Unicode 版本标注）：

| 枚举名 | 覆盖 | 默认风险（prompt 策略） | 依据 |
|---|---|---|---|
| `ZERO_WIDTH` | U+200B/200C/200D、U+2060、U+FEFF、U+2061–2064 | FORBIDDEN | promptfoo 2025-04-10 攻击载体 |
| `BIDI` | U+202A–202E、U+2066–2069 | FORBIDDEN | Trojan Source（CWE-180 相关） |
| `TAG_BLOCK` | U+E0000–U+E007F | FORBIDDEN | AWS 2025-09-30 |
| `SURROGATE_ORPHAN` | 孤立代理 U+D800–U+DFFF | FORBIDDEN | 破坏解码/重组隐患（AWS 代理对重组发现） |
| `CONTROL` | C0/C1 除 `\t\n\r` | FORBIDDEN | 终端注入/日志污染 |
| `SOFT_HYPHEN` 等其他 Cf | U+00AD 等 | SUSPICIOUS | 上下文依赖 |
| `HOMOGLYPH_UN` | Unicode confusables（拉丁/希腊/西里尔互混） | SUSPICIOUS | confusable_homoglyphs 同类 |
| `HOMOGLYPH_CJK` | 汉字形近字混淆集（己/已/巳、末/未、土/士…） | SUSPICIOUS | 中文优先，自建策展表 |
| `FULLWIDTH_HALF` | 全角 ASCII 变体、半角假名 | INFO | 中文归一化提示，不自动改写 |
| `PUNCT_VARIANT` | 中文/西文标点混排 | INFO | 同上 |

风险三级：`FORBIDDEN`（prompt 场景默认建议清除）/ `SUSPICIOUS`（需上下文判断）/ `INFO`（仅提示）。三套预置策略：`audit_prompt`（strict：FORBIDDEN 全激活）、`audit_corpus`（balanced：ZERO_WIDTH/BIDI/TAG_BLOCK/SURROGATE 激活，Cf 类降 SUSPICIOUS）、`audit_text`（neutral：只报告不预设清除建议）。策略可自定义（类别→风险的映射覆盖）。

设计取舍：U+200C（ZWNJ）在波斯文等正字法中合法——strict 策略仍报 FORBIDDEN 但 note 必须说明该例外；`FULLWIDTH_HALF` 在中文语料中普遍存在，默认 INFO 正是为了不制造误报噪音。

## 3. API 草案（v0 草案，实现期允许微调签名）

```python
@dataclass(frozen=True)
class Finding:
    category: str          # 枚举名
    risk: str              # FORBIDDEN / SUSPICIOUS / INFO
    start: int; end: int   # 原文码点偏移
    text: str              # invariant: text == source[start:end]
    codepoint: str         # 如 "U+200B"
    unicode_name: str
    note: str              # 含例外说明（如 ZWNJ 正字法）
    suggestion: str        # REMOVE / REVIEW / NORMALIZE_INFO
    confusable_with: str = ""   # HOMOGLYPH_* 专用：会被误认成什么（"с"→"c"、"己"→"已/巳"）

@dataclass
class Report:
    source: str
    findings: tuple[Finding, ...]
    policy: str; policy_version: str; table_version: str
    def stats(self) -> dict  # 按类别计数

def audit_text(text: str, *, policy: str | Policy = "neutral") -> Report
def audit_prompt(text: str, **kw) -> Report      # = audit_text(policy="strict")
def audit_corpus(texts: Iterable[str], **kw) -> Iterator[Report]   # 流式，常数内存
def diff_visible(a: str, b: str) -> DiffReport   # 逐码点对照，解释"看起来一样"为何不相等
def sanitize(text: str, *, policy: str | Policy = "strict") -> tuple[str, ChangeLog]
```

- **偏移不变量**（组合品牌承诺，fuzz 永久守护）：每个 Finding 满足 `finding.text == source[finding.start:finding.end]`。
- **diff_visible**：返回逐段对照（`a 段 / b 段 / 差异码点及名称`），核心卖点——回答"这两个字符串为什么不相等"。
- **sanitize**：只删不替（不引入新字符）；返回 ChangeLog（原偏移、被删码点、理由）；输出保证在策略激活类别上为空（含递归校验，见 §4）。

## 4. 正确性标准：递归清洗与 UTF-16 边界

AWS 博客证实的攻击面：UTF-16 编码字节流中滤掉代理对的一半，剩余半可与邻字节重组出**新的**隐形字符（U+E0000–E007F 区间尤其如此）。Python `str` 是码点序列，删字符不会造出新字符——**重组发生在字节边界**。因此：

1. 本库只接受 `str` 输入；收到 `bytes` 一律 TypeError，文档要求调用方自行 decode 并声明来源编码。
2. sanitize 在 strict 策略下执行 **UTF-16 往返校验**：`cleaned.encode("utf-16", "surrogatepass")` → decode 回 str → 再扫一遍激活类别，若产生新发现则再清洗，迭代至不动点（上限 8 轮，超出抛 RuntimeError——视为构造性对抗输入）。
3. 测试强制：fuzz 随机 Unicode 垃圾 + 构造性重组样例，断言"清洗后输出在激活类别上零残留"且"utf-16 往返稳定"。

## 5. 数据表来源与许可

| 表 | 来源 | 许可 | 打包方式 |
|---|---|---|---|
| HOMOGLYPH_UN | Unicode confusables.txt（S3-3 实装版本 18.0.0，2026-10-07 实抓；过滤：混合文字(MA/ML) + 单码点源 + 单 ASCII 可打印 target；排除 ASCII 源与全角/CJK 保留块） | Unicode License v3（Data Files and Software），全文入 `licenses/` | `scripts/build_tables.py` 预处理为紧凑 JSON（1,730 源字符），`_meta` 内嵌来源 URL、版本、原始文件 SHA-256、过滤规则、分级计数与 map 规范化 SHA-256；原始文件入库 `data/raw/` 作内容锚点 |
| ZERO_WIDTH/BIDI/TAG_BLOCK/CONTROL/Cf | unicodedata（stdlib）+ 手维护补充表 | Unicode 标准，自维护部分 MIT | 小型 JSON，标注所用 Unicode 版本（随 Python 3.13 为 Unicode 15.0/15.1，实现时以 `unicodedata.unidata_version` 实际值为准写入 table_version） |
| HOMOGLYPH_CJK | 仓内策展（S3-3 实装 250 组 / 650 字，kind 逐组标注），频次护栏排除最高频二三十字所在组 | MIT | 手写 `data/cjk_confusables.json` + `scripts/build_tables.py` 校验合并 |
| 全半角映射 | `unicodedata.normalize("NFKC")` 派生（只取 ASCII 全角区段） | 无数据文件 | 运行时生成，无表 |

规则：任何第三方数据入库前先核许可并记入 `licenses/`；`table_version = "<日期>-unicode<版本>+confusables<版本>"` 写入每个 Report，打包表文件另以 `TABLE_FINGERPRINTS`（SHA-256）暴露并由测试断言。

## 6. 实现与测试策略（S3/S4 预告）

- 纯 stdlib（`unicodedata`、`json`、`dataclasses`、`hashlib` 仅用于 table 指纹）；单遍扫描 + 策略过滤，性能目标 S4 实测后如实公布（不预设数字）。
- 已知向量测试：promptfoo 零宽 payload、AWS 标签块样例、Trojan Source bidi 样例、己/已/巳混淆集样例、孤立代理样例、西里尔/希腊同形字样例（S3-3 已落）。
- fuzz：偏移不变量、sanitize 零残留、utf-16 往返稳定三条性质；字母表含同形字字符。
- S3-3 语义修正（实现期决策，已回改本文件）：同形字是**可见**字符，diff 的 hidden/equal_visible 判定只认隐形五类（`is_invisible()`），`explain()` 单列"易混淆字符"行；`sanitize` 对同形字默认不删（只删不替——删除无法还原出目标字符），自定义策略可 REMOVE。

## 7. 诚实边界声明（S5 进 README）

- 确定性字符级检测；不识别语义级伪装；CJK 形近字表是部分覆盖（起步约 200 组，数字如实标注）；
- INFO 类是建议不是错误；
- "clean" 仅指"该策略、该数据表版本下激活类别零残留"；
- 本库不能证明文本"未被投毒"，只能证明"不含已知类别隐形字符"。
