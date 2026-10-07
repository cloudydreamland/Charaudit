"""diff_visible: explain why two look-alike strings are not equal."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from ._tables import classify, homoglyph_targets, is_invisible


@dataclass(frozen=True)
class DiffSegment:
    """One opcode segment. text_a/text_b concatenate back to a and b.

    op is "equal", "invisible" (difference caused by invisible characters), or
    "visible". hidden_a/hidden_b carry the invisible-class characters inside
    each side; homoglyphs are visible characters and are NOT counted hidden.
    """

    op: str  # "equal" / "invisible" / "visible"
    a_start: int
    a_end: int
    b_start: int
    b_end: int
    text_a: str
    text_b: str
    hidden_a: str
    hidden_b: str


@dataclass(frozen=True)
class DiffReport:
    a: str
    b: str
    equal: bool
    equal_visible: bool
    segments: tuple[DiffSegment, ...]

    def explain(self) -> str:
        """Chinese, human-readable explanation of every difference."""
        if self.equal:
            return "两个字符串完全相同。"
        lines: list[str] = []
        if self.equal_visible:
            lines.append(
                "可见内容一致：两串去掉隐形/控制类字符后逐字符相同，差异全部来自隐形字符。"
            )
        else:
            lines.append("存在可见内容差异：除隐形字符外，可见字符序列本身也不相同。")
        for side, text in (("a", self.a), ("b", self.b)):
            hidden = [
                (pos, f"U+{ord(ch):04X}", classify(ch))
                for pos, ch in enumerate(text)
                if is_invisible(ch)
            ]
            homoglyph = [
                (pos, f"U+{ord(ch):04X}", ch, homoglyph_targets(ch))
                for pos, ch in enumerate(text)
                if classify(ch) is not None and not is_invisible(ch)
            ]
            if not hidden:
                lines.append(f"{side} 侧无隐形字符")
            else:
                shown = "、".join(f"{cp}({cat})@{pos}" for pos, cp, cat in hidden[:8])
                more = f" …共 {len(hidden)} 处" if len(hidden) > 8 else ""
                lines.append(f"{side} 侧隐形字符 {len(hidden)} 处：{shown}{more}")
            if homoglyph:
                shown = "、".join(
                    f"{cp}({ch}≈{targets})@{pos}"
                    for pos, cp, ch, targets in homoglyph[:8]
                )
                more = f" …共 {len(homoglyph)} 处" if len(homoglyph) > 8 else ""
                lines.append(f"{side} 侧易混淆字符 {len(homoglyph)} 处：{shown}{more}")
        return "\n".join(lines)


def _common_prefix(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    i = 0
    while i < limit and a[i] == b[i]:
        i += 1
    return i


def _common_suffix(a: str, b: str, prefix: int) -> int:
    limit = min(len(a), len(b)) - prefix
    i = 0
    while i < limit and a[len(a) - 1 - i] == b[len(b) - 1 - i]:
        i += 1
    return i


def diff_visible(a: str, b: str) -> DiffReport:
    """Compare two strings and attribute each difference to hidden or visible cause.

    ``equal_visible`` is True when both strings are identical after dropping
    invisible-class characters — the answer to "why do these look-alike
    strings compare unequal?". Homoglyphs are visible characters (they only
    look alike); differences they cause are reported as visible segments and
    itemized in ``explain()``.

    Performance note: the common prefix and suffix are trimmed before
    difflib sees the input, so near-identical inputs cost O(n) instead of
    difflib's super-linear behavior on long repetitive text (measured 85.6s
    -> sub-second at ~100k chars; see benchmarks/RESULTS.md).
    """
    if not isinstance(a, str) or not isinstance(b, str):
        raise TypeError("charaudit diff_visible accepts str only")
    segments: list[DiffSegment] = []

    prefix = _common_prefix(a, b)
    suffix = _common_suffix(a, b, prefix)
    mid_a = a[prefix : len(a) - suffix]
    mid_b = b[prefix : len(b) - suffix]

    if prefix:
        segments.append(
            DiffSegment("equal", 0, prefix, 0, prefix, a[:prefix], b[:prefix], "", "")
        )
    if mid_a or mid_b:
        matcher = SequenceMatcher(None, mid_a, mid_b, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            text_a = mid_a[i1:i2]
            text_b = mid_b[j1:j2]
            if tag == "equal":
                segments.append(
                    DiffSegment(
                        "equal",
                        prefix + i1,
                        prefix + i2,
                        prefix + j1,
                        prefix + j2,
                        text_a,
                        text_b,
                        "",
                        "",
                    )
                )
                continue
            hidden_a = "".join(ch for ch in text_a if is_invisible(ch))
            hidden_b = "".join(ch for ch in text_b if is_invisible(ch))
            all_hidden_a = bool(text_a) and len(hidden_a) == len(text_a)
            all_hidden_b = bool(text_b) and len(hidden_b) == len(text_b)
            if (all_hidden_a or not text_a) and (all_hidden_b or not text_b):
                op = "invisible"
            else:
                op = "visible"
            segments.append(
                DiffSegment(
                    op,
                    prefix + i1,
                    prefix + i2,
                    prefix + j1,
                    prefix + j2,
                    text_a,
                    text_b,
                    hidden_a,
                    hidden_b,
                )
            )
    if suffix:
        segments.append(
            DiffSegment(
                "equal",
                len(a) - suffix,
                len(a),
                len(b) - suffix,
                len(b),
                a[len(a) - suffix :],
                b[len(b) - suffix :],
                "",
                "",
            )
        )
    visible_a = [ch for ch in a if not is_invisible(ch)]
    visible_b = [ch for ch in b if not is_invisible(ch)]
    return DiffReport(
        a=a,
        b=b,
        equal=(a == b),
        equal_visible=(visible_a == visible_b),
        segments=tuple(segments),
    )
