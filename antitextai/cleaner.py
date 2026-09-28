"""Deterministic de-AI text/code cleaner. Spec: SKILL.md (same directory).

Only the mechanical passes live here: characters, frames, whole-line fluff, comment noise.
Judgment work (em/en dashes, docstrings, naming, WHAT-comments) is deliberately excluded.
"""
import re
import unicodedata

# A marker is a comment only when the line starts with it or whitespace precedes it.
# That anchoring is what keeps `x = "# end of loop"` out of the end-marker rule.
CP = r"(?://|#|--|\*)"

INVISIBLE = re.compile(r"[\u200B\u200C\u200D\u2060\uFEFF\u00AD\u200E\u200F]")
NBSP      = re.compile(r"[\u00A0\u202F]")
SMART     = {0x201C: '"', 0x201D: '"', 0x2018: "'", 0x2019: "'", 0x2026: "...",
             0x2032: "'", 0x2033: '"', 0x00D7: "x", 0x2212: "-"}

BULLET_LEAD = re.compile(r"(?m)^([ \t]*)\u2022[ \t]*")

# --- Conversational framing -----------------------------------------------------------------
# Framing is stripped, not the line it sits on: "In today's market, revenue grew." must become
# "Revenue grew.", not vanish. Deleting whole lines here once emptied files that had substance
# appended after the opener.
FLUFF_START = (r"certainly|sure thing|sure|of course|absolutely|great question|excellent question"
               r"|no problem|got it")
BARE_FLUFF = re.compile(
    r"(?im)^[ \t]*(?:" + FLUFF_START + r"|hope (?:this|that) helps|thanks|thank you)[,.!]?[ \t]*$\n?")
# "Hope this helps!" / "Let me know if…" are pure sign-offs: nothing substantive follows on the line.
SALUTATION = re.compile(r"(?im)^[ \t]*(?:hope (?:this|that) helps|let me know if|feedback welcome)[^\n]*$\n?")
# "Certainly! The build passes." -> "The build passes." Frame dropped, content recapitalized.
INTERJECT = re.compile(
    r"(?im)^[ \t]*(?:" + FLUFF_START + r")[,.:;!][ \t]+(\w)")
# Adverbial openers end at their comma: "In today's market, revenue grew." -> "Revenue grew."
CLAUSE = re.compile(
    r"(?im)^[ \t]*(?:in today'?s|overall|that said|in conclusion|to summari[sz]e|in summary"
    r"|needless to say)[^,.!?;:\n]*,[ \t]+(\w)")
# Complementizers carry no comma and introduce the sentence's subject: the frame ends at "that",
# and the clause it introduces MUST be kept. Deleting through the sentence here loses information.
SUBORDINATE = re.compile(
    r"(?im)^[ \t]*(?:it'?s important to note that|it'?s worth (?:noting|mentioning) that"
    r"|please note that|note that)[ \t]+(\w)")
# Mid-paragraph gestures: the opener follows a sentence boundary, so prose like
# "Caching is essential. Please note that TTLs prevent stale data." loses the frame.
GESTURE_INLINE = re.compile(
    r"(?i)([.!?][ \t]+)(?:it'?s important to note that|it'?s worth (?:noting|mentioning) that"
    r"|please note that|note that|needless to say,|that said,|in conclusion,|to summari[sz]e,"
    r"|in summary,|overall,)[ \t]+(\w)")

PRECODE  = re.compile(r"(?im)^[ \t]*here(?:'s| is) (?:the|a) (?:complete|full)?[^\n]*:[ \t]*$\n?")
END_WHOLE = re.compile(
    rf"(?im)^[ \t]*{CP}[ \t]*end[ \t]+(?:of[ \t]+)?"
    r"(?:block|loop|function|class|method|if|switch|try|module|def)\b[^\n]*$\n?")
# Trailing form: drop the comment, keep the code. The lookbehind avoids consuming the code's
# last character; a whole-line replacement here would delete executable lines.
END_TRAIL = re.compile(
    r"(?im)(?<=\S)[ \t]+(?:"
    + CP
    + r"|/\*)[ \t]*end[ \t]+(?:of[ \t]+)?"
    r"(?:block|loop|function|class|method|if|switch|try|module|def)\b[^\n]*$")
NARRATION = re.compile(
    rf"(?im)^[ \t]*{CP}[ \t]*(?:now|then|first|next|finally|here)[ \t]*,[ \t]*(?:we|i)[ \t]+[^\n]*$\n?")
STEPNARR  = re.compile(rf"(?im)^[ \t]*{CP}[ \t]*step[ \t]*\d+[ \t]*:?[^\n]*$\n?")
SEPARATOR = re.compile(rf"(?m)^[ \t]*(?:{CP}|/\*)?[ \t]*[=\-*_]{{5,}}[ \t]*(?:\*/|//|#)?[ \t]*$\n?")
# A trailing sign-off appended to a content line: "...is a solid choice. Hope this helps!".
# Requires a sentence boundary, so `will let me know if the job fails` is never truncated.
INLINE_OUTRO = re.compile(
    r"(?im)(?<=[.!?])[ \t]+(?:hope (?:this|that) helps|feedback welcome)[.!]?[ \t]*$"
    r"|(?<=[.!?])[ \t]+let me know if[^\n]*$")
# Setext underline: a run of `=`/`-` directly under a text line makes an H1/H2. SEPARATOR would
# eat it and silently demote the heading to body text, so those lines are held out of the rules.
SETEXT = re.compile(r"^([=-])\1+[ \t]*$")
FRONTMATTER = re.compile(r"\A(---[ \t]*\r?\n.*?\r?\n---[ \t]*\r?\n)", re.S)

CHAR_RULES = (("INVISIBLE", INVISIBLE), ("NBSP", NBSP), ("BULLET", BULLET_LEAD))
LINE_RULES = (("BARE_FLUFF", BARE_FLUFF), ("SALUTATION", SALUTATION), ("INLINE_OUTRO", INLINE_OUTRO),
              ("PRECODE", PRECODE), ("END_WHOLE", END_WHOLE), ("END_TRAIL", END_TRAIL),
              ("NARRATION", NARRATION), ("STEPNARR", STEPNARR), ("SEPARATOR", SEPARATOR))


def split_frontmatter(text: str):
    fm = FRONTMATTER.match(text)
    return (fm.group(1), text[fm.end():]) if fm else ("", text)

def setext_lines(text: str) -> set:
    """Line indices that are legitimate setext underlines rather than banner separators."""
    lines = text.split("\n")
    keep = set()
    for i, line in enumerate(lines):
        if line[:1] in (" ", "\t") or not SETEXT.fullmatch(line):
            continue                                         # indented => code, not a heading
        prev = lines[i - 1] if i else ""
        if prev.strip() and not prev.startswith("    ") and prev.strip()[:1] not in "-=":
            keep.add(i)                                      # text above, underline below
    return keep


def clean(text: str, *, strip_bom: bool = True) -> str:
    """Mechanical passes only. U+2013/U+2014 are never touched: whether a dash joins a range,
    a clause, or a quotation decides its replacement, so every occurrence goes through review."""
    # A byte-0 BOM is stripped by default. With strip_bom=False it is taken off anyway and
    # re-attached at the end: leaving it in place would hide the first line from every
    # ^-anchored rule (and let INVISIBLE delete it as an ordinary U+FEFF).
    keep_bom = not strip_bom and text.startswith("\ufeff")
    if strip_bom:
        text = text.replace("\ufeff", "", 1)              # byte-0 BOM only; U+FEFF elsewhere stays
    elif keep_bom:
        text = text[1:]
    crlf = "\r\n" in text and text.count("\r\n") >= text.count("\n") - text.count("\r\n")
    if "\r" in text:
        text = text.replace("\r\n", "\n").replace("\r", "\n")

    head, body = split_frontmatter(text)                  # frontmatter never sees the line rules
    body = INVISIBLE.sub("", body)
    body = BULLET_LEAD.sub(r"\1- ", body)
    body = body.replace("\u2022", "-")                    # non-leading bullets, incl. "a• b"
    body = NBSP.sub(" ", body)
    body = body.translate(SMART)
    # Hold setext underlines out of the line rules; SEPARATOR would otherwise eat them silently.
    masked = {}
    lines = body.split("\n")
    for i in setext_lines(body):
        masked[token := f"\x00SETEXT{i}\x00"] = lines[i]
        lines[i] = token
    body = "\n".join(lines)
    # Frames first, so a stripped opener can expose another frame on the same line.
    prev = None
    while prev != body:
        prev = body
        body = INTERJECT.sub(lambda m: m.group(1).upper(), body)
        body = CLAUSE.sub(lambda m: m.group(1).upper(), body)
        body = SUBORDINATE.sub(lambda m: m.group(1).upper(), body)
        body = GESTURE_INLINE.sub(lambda m: m.group(1) + m.group(2).upper(), body)
    for _, pat in LINE_RULES:
        body = pat.sub("", body)
    for token, line in masked.items():                    # put setext underlines back, verbatim
        body = body.replace(token, line)
    body = re.sub(r"[ \t]+$", "", body, flags=re.M)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    out = head + body + "\n" if body else head.strip() + ("\n" if head else "")
    if keep_bom:
        out = "\ufeff" + out
    return out.replace("\n", "\r\n") if crlf else out


def assert_no_artifacts(text: str) -> None:
    if text.startswith("\ufeff"):
        text = text[1:]                                   # a kept byte-0 BOM is intentional
    head, body = split_frontmatter(text)
    keep = setext_lines(body)                             # these look like SEPARATOR, but are headings
    lines = body.split("\n")
    masked = "\n".join("" if i in keep else line for i, line in enumerate(lines))
    for name, pat in (("INVISIBLE", INVISIBLE), ("NBSP", NBSP), ("BULLET", BULLET_LEAD),
                      ("INTERJECT", INTERJECT), ("CLAUSE", CLAUSE), ("SUBORDINATE", SUBORDINATE),
                      ("GESTURE_INLINE", GESTURE_INLINE)) + LINE_RULES:
        if (m := pat.search(masked)):
            cats = " ".join(f"U+{ord(c):04X}({unicodedata.name(c, '?')})"
                            for c in m.group(0) if unicodedata.category(c) in ("Cf", "Zs"))
            raise AssertionError(f"{name} residual {m.group(0)!r} {cats}")
    if "\u2022" in body:
        raise AssertionError("residual bullet U+2022")
    for ch in SMART:
        if chr(ch) in head:
            raise AssertionError(f"frontmatter carries U+{ch:04X}; repair by hand, not by rule")


# The command line lives in cli.py (`python -m antitextai`). This module stays import-only,
# so it can be vendored into another project as a single file.

__all__ = ["clean", "assert_no_artifacts", "split_frontmatter", "setext_lines"]
