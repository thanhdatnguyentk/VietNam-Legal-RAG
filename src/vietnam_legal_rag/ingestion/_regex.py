"""Compiled regular-expression patterns for parsing Vietnamese legal text.

These patterns are deliberately conservative — they only match the most
common formatting conventions found in scraped Vietnamese legal documents:

* **Article** (``Điều``): ``Điều 1.``, ``Điều 23:``, ``Điều 15 `` — optionally followed
  by a title on the same line.
* **Clause** (``Khoản``): ``1.``, ``2)`` — a line that starts with one or more digits
  followed by ``.`` or ``)``.
* **Point** (``Điểm``): ``a)``, ``b)``, ``đ)`` — a single lowercase Vietnamese letter
  followed by ``)``.

Edge cases (numbered articles after a chapter heading, articles with Roman numerals,
articles whose titles span multiple lines) are out of scope for phase 2. We can
widen the patterns later without breaking the public interface.

All patterns use ``re.MULTILINE`` so that ``^`` matches the start of any line.
"""

from __future__ import annotations

import re

# Matches an article heading at the start of a line.
#   group(1) = article number (digits only)
#   group(2) = optional title text on the same line (may be empty)
# Examples:
#   "Điều 1. Phạm vi điều chỉnh"  -> ("1", "Phạm vi điều chỉnh")
#   "Điều 23:"                    -> ("23", "")
#   "Điều 15 Quy định chung"      -> ("15", "Quy định chung")
ARTICLE_PATTERN: re.Pattern[str] = re.compile(
    r"^Điều\s+(\d+)\s*(?:\.|:|\s)?\s*([^\n]*)$",
    re.MULTILINE,
)

# Matches a clause heading at the start of a line.
#   group(1) = clause number (digits only)
#   group(2) = first non-whitespace character on the line (so the body
#              can be re-anchored from that position to keep the leading
#              capital letter, e.g. "Đ" in "Đây là khoản").
# Examples:
#   "1. Công dân Việt Nam;"       -> ("1", "C")
#   "2) Tổ chức, cá nhân;"       -> ("2", "T")
#   "10. Một số quy định ..."    -> ("10", "M")
CLAUSE_PATTERN: re.Pattern[str] = re.compile(
    r"^(\d+)\s*[\.\)]\s+(\S)",
    re.MULTILINE,
)

# Matches a point heading at the start of a line.
#   group(1) = point letter (single lowercase Latin or Vietnamese letter)
#   group(2) = first non-whitespace character after ``)`` (anchor point
#              for re-anchoring the body without losing the first letter)
# Examples:
#   "a) Đường bộ là gì;"         -> ("a", "Đ")
#   "đ) Phương tiện khác;"        -> ("đ", "P")
#
# We list common Vietnamese consonants instead of ``\p{Ll}`` because the
# Python ``re`` module does not support Unicode property escapes. Letters
# not in the class (rare in legal documents) will simply fail to match and
# fall through to the char splitter fallback.
_VN_LOWER_LETTERS = "abcdefghijklmnopqrstuvwxyzăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ"
POINT_PATTERN: re.Pattern[str] = re.compile(
    rf"^([{_VN_LOWER_LETTERS}])\s*\)\s+(\S)",
    re.MULTILINE,
)

__all__ = ["ARTICLE_PATTERN", "CLAUSE_PATTERN", "POINT_PATTERN"]
