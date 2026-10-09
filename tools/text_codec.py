"""Text & codec tools: Base64, URL, Hash, JSON, UUID, Password, Timestamp,
Regex, Word Count, Minifier, Markdown, Cron, Encoding."""

import base64
import hashlib
import html
import json
import math
import re
import secrets
import string
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import quote, quote_plus, unquote, unquote_plus

import customtkinter as ctk

from tools import BaseTool
from ui.widgets import (
    ERROR, MUTED, SUCCESS, WARN, ToolLayout, copy_box, get_text, set_text,
)


def _copy(box, status):
    copy_box(box, status)


# --------------------------------------------------------------------------
# Shared panel: input box -> action buttons -> output box -> status
# --------------------------------------------------------------------------
class _Panel(BaseTool):
    category = "text"
    needs_input = True
    input_label = "Input"
    input_height = 140
    output_label = "Output"
    output_height = 170
    actions = ()          # (label, fn(tool) -> str)
    hint = None

    def _extra(self, lay):
        """Hook for tools that need extra controls above the input."""

    def build(self, parent):
        lay = ToolLayout(parent)
        self.layout = lay
        self._extra(lay)
        if self.needs_input:
            self.inp = lay.box(self.input_label, height=self.input_height, weight=1)
        self.out = lay.box(self.output_label, height=self.output_height,
                           readonly=True, weight=2)
        items = [(label, (lambda f=fn: self.run(f))) for label, fn in self.actions]
        items += [("Copy", self.copy_output), ("Clear", self.clear)]
        lay.buttons(items)
        self.status = lay.status()

    def run(self, fn):
        try:
            result = fn(self)
            set_text(self.out, "" if result is None else str(result))
            self.status.set("Done.", SUCCESS)
        except Exception as e:
            self.status.set(f"Error: {e}", ERROR)

    def inp_text(self):
        return get_text(self.inp) if self.needs_input else ""

    def copy_output(self):
        _copy(self.out, self.status)

    def clear(self):
        if self.needs_input:
            set_text(self.inp, "")
        set_text(self.out, "")
        self.status.set("Cleared.")


# --------------------------------------------------------------------------
# 1. Base64
# --------------------------------------------------------------------------
class Base64Tool(_Panel):
    id = "base64"
    name = "Base64"
    icon = "🔤"
    description = "Encode text to Base64 and decode Base64 back to text."
    keywords = ["base64", "b64", "encode", "decode", "binary"]

    actions = [
        ("Encode", lambda t: base64.b64encode(t.inp_text().encode()).decode()),
        ("Decode", lambda t: base64.b64decode(
            re.sub(r"\s+", "", t.inp_text())).decode("utf-8", "replace")),
    ]


# --------------------------------------------------------------------------
# 2. URL codec
# --------------------------------------------------------------------------
class UrlCodecTool(_Panel):
    id = "url_codec"
    name = "URL Encode"
    icon = "🔗"
    description = "Percent-encode text for URLs, or decode a URL back."
    keywords = ["url", "uri", "percent", "encode", "decode", "query", "escape"]

    actions = [
        ("URL Encode", lambda t: quote(t.inp_text(), safe="")),
        ("URL Encode (+)", lambda t: quote_plus(t.inp_text())),
        ("URL Decode", lambda t: unquote(t.inp_text())),
        ("URL Decode (+)", lambda t: unquote_plus(t.inp_text())),
    ]


# --------------------------------------------------------------------------
# 3. Hash
# --------------------------------------------------------------------------
def _hasher(algo):
    def fn(t):
        data = t.inp_text().encode("utf-8", "surrogateescape")
        digest = hashlib.new(algo, data).hexdigest()
        return f"{algo.upper()}  {len(digest) * 4} bit\n\n{digest}"
    return fn


class HashTool(_Panel):
    id = "hash"
    name = "Hash Generator"
    icon = "#️⃣"
    description = "MD5, SHA-1, SHA-256 and SHA-512 checksums of any text."
    keywords = ["hash", "md5", "sha", "sha256", "checksum", "digest", "fingerprint"]
    output_height = 200

    actions = [
        ("MD5", _hasher("md5")),
        ("SHA-1", _hasher("sha1")),
        ("SHA-256", _hasher("sha256")),
        ("SHA-512", _hasher("sha512")),
        ("All", lambda t: "\n\n".join(
            f"{a.upper()}\n{_hasher(a)(t).splitlines()[-1]}"
            for a in ("md5", "sha1", "sha256", "sha512"))),
    ]


# --------------------------------------------------------------------------
# 4. JSON
# --------------------------------------------------------------------------
class JsonTool(_Panel):
    id = "json_tool"
    name = "JSON Formatter"
    icon = "🧾"
    description = "Format, minify and validate JSON documents."
    keywords = ["json", "format", "pretty", "minify", "validate", "beautify"]

    actions = [
        ("Format", lambda t: json.dumps(json.loads(t.inp_text()),
                                        indent=2, ensure_ascii=False)),
        ("Minify", lambda t: json.dumps(json.loads(t.inp_text()),
                                        separators=(",", ":"), ensure_ascii=False)),
        ("Validate", lambda t: _validate_json(t.inp_text())),
    ]


def _validate_json(text):
    obj = json.loads(text)
    size = len(text.encode())
    kind = type(obj).__name__
    count = (f" ({len(obj)} items)" if isinstance(obj, (list, dict)) else "")
    return f"Valid JSON ✓\nType: {kind}{count}\nSize: {size} bytes"


# --------------------------------------------------------------------------
# 5. UUID
# --------------------------------------------------------------------------
class UuidTool(_Panel):
    id = "uuid"
    name = "UUID Generator"
    icon = "🆔"
    description = "Generate random UUID v4 identifiers."
    keywords = ["uuid", "guid", "id", "unique", "identifier", "random"]
    needs_input = False
    input_label = None

    actions = [
        ("Generate", lambda t: "\n".join(str(uuid.uuid4())
                                         for _ in range(t._count()))),
        ("Generate ×10", lambda t: "\n".join(str(uuid.uuid4()) for _ in range(10))),
        ("UUIDv1 (time-based)", lambda t: str(uuid.uuid1())),
    ]

    def _extra(self, lay):
        row = lay.row()
        ctk.CTkLabel(row, text="Count:", font=ctk.CTkFont(size=12),
                     text_color=MUTED).pack(side="left", padx=(0, 8))
        self.count_entry = ctk.CTkEntry(row, width=70, height=30,
                                        border_width=1)
        self.count_entry.insert(0, "5")
        self.count_entry.pack(side="left")

    def _count(self):
        try:
            return max(1, min(500, int(self.count_entry.get().strip())))
        except Exception:
            return 1


# --------------------------------------------------------------------------
# 6. Password
# --------------------------------------------------------------------------
def _generate_password(t):
    try:
        length = int(t.len_entry.get().strip() or "18")
    except Exception:
        length = 18
    length = max(6, min(128, length))

    pool = string.ascii_letters
    if t.cb_digits.var.get():
        pool += string.digits
    if t.cb_symbols.var.get():
        pool += "!@#$%^&*()-_=+[]{};:,.?/"
    if t.cb_clean.var.get():
        for ch in "0O1lI":
            pool = pool.replace(ch, "")

    chars = [secrets.choice(pool) for _ in range(length)]
    if t.cb_digits.var.get() and not any(c in string.digits for c in chars):
        chars[0] = secrets.choice(string.digits)
    if t.cb_symbols.var.get() and not any(not c.isalnum() for c in chars):
        chars[1] = secrets.choice("!@#$%^&*")
    password = "".join(chars)

    bits = round(length * math.log2(max(2, len(set(pool)))))
    strength = ("weak" if bits < 45 else "fair" if bits < 70 else
                "strong" if bits < 100 else "very strong")
    return (f"{password}\n\n"
            f"Length: {length}   Pool: {len(set(pool))} unique chars\n"
            f"Entropy: ~{bits} bits  ({strength})")


class PasswordTool(_Panel):
    id = "password"
    name = "Password Generator"
    icon = "🔐"
    description = "Create strong random passwords with configurable rules."
    keywords = ["password", "passphrase", "random", "generate", "strong", "secure"]
    needs_input = False

    actions = [("Generate", _generate_password)]

    def _extra(self, lay):
        self.len_entry = lay.entry("Length", default="18", width=110)
        self.len_entry.configure(width=110)
        self.cb_digits = lay.checkbox("Include numbers", default=True)
        self.cb_symbols = lay.checkbox("Include symbols", default=True)
        self.cb_clean = lay.checkbox("Avoid ambiguous chars (0 O 1 l I)",
                                     default=True)


# --------------------------------------------------------------------------
# 7. Timestamp
# --------------------------------------------------------------------------
class TimestampTool(_Panel):
    id = "timestamp"
    name = "Timestamp"
    icon = "⏱"
    description = "Convert Unix timestamps to dates and back."
    keywords = ["timestamp", "unix", "epoch", "date", "time", "convert"]
    input_label = "Input (unix timestamp or date string)"
    hint = "Supports: 1700000000, 1700000000000, 2024-05-01 14:30:00"

    actions = [
        ("Now (Unix)", lambda t: str(int(time.time()))),
        ("Now (ISO)", lambda t: datetime.now().isoformat(
            sep=" ", timespec="seconds")),
        ("Unix → Date", lambda t: _unix_to_date(t.inp_text())),
        ("Date → Unix", lambda t: _date_to_unix(t.inp_text())),
        ("UTC now", lambda t: datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC")),
    ]

    def _extra(self, lay):
        if self.hint:
            lay.note(self.hint)


def _unix_to_date(text):
    raw = text.strip()
    if not raw:
        raise ValueError("enter a timestamp")
    value = float(raw)
    if value > 1e12:                      # milliseconds
        value /= 1000.0
    local = datetime.fromtimestamp(value)
    utc = datetime.fromtimestamp(value, tz=timezone.utc)
    return (f"Local : {local.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"UTC   : {utc.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"ISO   : {local.isoformat(timespec='seconds')}\n"
            f"Week  : {local.strftime('%A')}")


def _date_to_unix(text):
    raw = text.strip()
    if not raw:
        raise ValueError("enter a date")
    dt = None
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y %H:%M:%S",
                    "%m/%d/%Y", "%d %b %Y %H:%M:%S", "%d %b %Y", "%B %d, %Y"):
            try:
                dt = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
    if dt is None:
        raise ValueError(f"could not parse “{raw}”")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (f"Unix  : {int(dt.timestamp())}\n"
            f"Millis: {int(dt.timestamp() * 1000)}\n"
            f"UTC   : {dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")


# --------------------------------------------------------------------------
# 8. Regex tester
# --------------------------------------------------------------------------
class RegexTool(BaseTool):
    id = "regex"
    name = "Regex Tester"
    category = "text"
    icon = "🔎"
    description = "Test regular expressions: find all matches and substitute."
    keywords = ["regex", "regexp", "pattern", "match", "replace", "search"]

    def build(self, parent):
        lay = ToolLayout(parent)
        self.layout = lay
        self.pattern = lay.entry("Pattern", placeholder=r"e.g. \b\w+@\w+\.\w+\b")
        self.replace = lay.entry("Replace with (Substitute only)",
                                 placeholder="e.g. ***")
        self.test = lay.box("Test string", height=130, weight=1)
        self.out = lay.box("Output", height=150, readonly=True, weight=2)
        lay.buttons([
            ("Find All", self.find_all),
            ("Substitute", self.substitute),
            ("Validate", self.validate),
            ("Copy", lambda: _copy(self.out, self.status)),
            ("Clear", self.clear),
        ])
        self.status = lay.status()

    def _pattern(self):
        p = self.pattern.get().strip()
        if not p:
            raise ValueError("pattern is empty")
        return p

    def find_all(self):
        try:
            rx = re.compile(self._pattern())
            text = get_text(self.test)
            hits = list(rx.finditer(text))
            if not hits:
                set_text(self.out, "No matches.")
                self.status.set("No matches.", WARN)
                return
            lines = [f"{len(hits)} match{'es' if len(hits) != 1 else ''}:"]
            for i, m in enumerate(hits[:400], 1):
                shown = m.group(0).replace("\n", "\\n")
                lines.append(f"{i:>4}. {shown!r}   [{m.start()}–{m.end()}]")
            if len(hits) > 400:
                lines.append(f"… {len(hits) - 400} more")
            set_text(self.out, "\n".join(lines))
            self.status.set(f"{len(hits)} match(es).", SUCCESS)
        except re.error as e:
            set_text(self.out, "")
            self.status.set(f"Invalid pattern: {e}", ERROR)

    def substitute(self):
        try:
            rx = re.compile(self._pattern())
            repl = self.replace.get()
            new, n = rx.subn(repl, get_text(self.test))
            set_text(self.out, new)
            self.status.set(f"{n} replacement(s).", SUCCESS)
        except re.error as e:
            self.status.set(f"Invalid pattern: {e}", ERROR)

    def validate(self):
        try:
            rx = re.compile(self._pattern())
            set_text(self.out,
                     f"Pattern is valid ✓\nFlags: {rx.flags}\n"
                     f"Groups: {rx.groups}")
            self.status.set("Pattern is valid.", SUCCESS)
        except re.error as e:
            set_text(self.out, "")
            self.status.set(f"Invalid pattern: {e}", ERROR)

    def clear(self):
        set_text(self.test, "")
        set_text(self.out, "")
        self.status.set("Cleared.")


# --------------------------------------------------------------------------
# 9. Word counter
# --------------------------------------------------------------------------
def _word_stats(t):
    text = t.inp_text()
    words = re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE)
    lines = text.count("\n") + (1 if text else 0)
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    letters = sum(1 for c in text if c.isalpha())
    digits = sum(1 for c in text if c.isdigit())
    spaces = text.count(" ")
    avg = (sum(len(w) for w in words) / len(words)) if words else 0
    longest = max((len(w) for w in words), default=0)

    top = Counter(w.lower() for w in words).most_common(20)
    stop = {"the", "and", "of", "to", "in", "a", "is", "it", "that", "for"}
    top = [(w, c) for w, c in top if w not in stop][:8]

    out = [
        f"Words          : {len(words)}",
        f"Characters     : {len(text)}",
        f"  no spaces    : {len(text) - spaces}",
        f"Lines          : {lines}",
        f"Paragraphs     : {len(paragraphs)}",
        f"Sentences      : {len(sentences)}",
        f"Letters        : {letters}",
        f"Digits         : {digits}",
        f"Spaces         : {spaces}",
        f"Avg word length: {avg:.1f}",
        f"Longest word   : {longest}",
        f"Reading time   : ~{max(1, round(len(words) / 200))} min @200wpm",
    ]
    if top:
        out.append("\nTop words:")
        out += [f"  {w:<16} {c}" for w, c in top]
    return "\n".join(out)


class WordCountTool(_Panel):
    id = "word_count"
    name = "Word Counter"
    icon = "📝"
    description = "Words, characters, lines, sentences and top terms."
    keywords = ["word", "count", "character", "readability", "essay", "length"]
    input_label = "Text"
    output_label = "Statistics"

    actions = [("Count", _word_stats)]


# --------------------------------------------------------------------------
# 10. Minifier
# --------------------------------------------------------------------------
def _minify_html(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"(?s)>(\s+)<", r"><", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _minify_css(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{};:,>])\s*", r"\1", text)
    return text.replace(";}", "}").strip()


def _minify_js(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"(^|[^:])//[^\n]*", r"\1", text, flags=re.M)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{}();:,=+\-*/<>])\s*", r"\1", text)
    return text.strip()


def _minify_ws(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


class MinifierTool(_Panel):
    id = "minifier"
    name = "Code Minifier"
    icon = "🗜"
    description = "Shrink HTML, CSS, JS, JSON or plain whitespace."
    keywords = ["minify", "compress", "shrink", "html", "css", "js", "clean"]

    actions = [
        ("HTML", lambda t: _minify_html(t.inp_text())),
        ("CSS", lambda t: _minify_css(t.inp_text())),
        ("JS", lambda t: _minify_js(t.inp_text())),
        ("JSON", lambda t: json.dumps(json.loads(t.inp_text()),
                                      separators=(",", ":"), ensure_ascii=False)),
        ("Whitespace", lambda t: _minify_ws(t.inp_text())),
        ("Compare", lambda t: _minify_report(t.inp_text())),
    ]


def _minify_report(text):
    variants = {
        "HTML": _minify_html(text),
        "CSS": _minify_css(text),
        "JS": _minify_js(text),
        "Whitespace": _minify_ws(text),
    }
    before = len(text.encode())
    lines = [f"Original: {before} bytes", ""]
    for name, out in variants.items():
        after = len(out.encode())
        saved = (1 - after / before) * 100 if before else 0
        lines.append(f"{name:<12} {after:>8} bytes   ({saved:+.1f}%)")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# 11. Markdown
# --------------------------------------------------------------------------
def _md_inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
                  lambda m: f'<img alt="{m.group(1)}" src="{m.group(2)}">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                  lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<![\w])_([^_\n]+)_(?![\w])", r"<em>\1</em>", text)
    return text


def _md_to_html(md):
    lines = md.splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            buf = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(buf))}"
                       f"</code></pre>")
            continue

        if not line.strip():
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{_md_inline(m.group(2).strip())}</h{level}>")
            i += 1
            continue

        if re.match(r"^\s*([-*_])\s*\1\s*\1[\s\-_]*$", line):
            out.append("<hr>")
            i += 1
            continue

        if line.lstrip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].strip())
                i += 1
            out.append(f"<blockquote><p>{_md_inline(' '.join(buf))}</p>"
                       f"</blockquote>")
            continue

        if re.match(r"^\s*([-*+]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            items = []
            while i < len(lines):
                m2 = re.match(r"^\s*([-*+]|\d+\.)\s+(.*)$", lines[i])
                if not m2:
                    break
                items.append(_md_inline(m2.group(2).strip()))
                i += 1
            tag = "ol" if ordered else "ul"
            joined = "".join(f"<li>{it}</li>" for it in items)
            out.append(f"<{tag}>{joined}</{tag}>")
            continue

        buf = []
        while (i < len(lines) and lines[i].strip()
               and not re.match(r"^(#{1,6}\s|\s*([-*+]|\d+\.)\s|>\s|```)",
                                lines[i])):
            buf.append(lines[i].rstrip())
            i += 1
        out.append(f"<p>{_md_inline(' '.join(buf))}</p>")

    return "\n".join(out)


def _md_strip(text):
    text = re.sub(r"```.*?```", lambda m: m.group(0).strip("`"), text, flags=re.S)
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.M)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^\s{0,3}>\s?", "", text, flags=re.M)
    text = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", text, flags=re.M)
    return text.strip()


class MarkdownTool(_Panel):
    id = "markdown"
    name = "Markdown → HTML"
    icon = "📐"
    description = "Convert Markdown to clean HTML or strip its formatting."
    keywords = ["markdown", "md", "html", "convert", "docs", "readme"]
    input_label = "Markdown"
    output_label = "HTML"

    actions = [
        ("MD → HTML", lambda t: _md_to_html(t.inp_text())),
        ("Strip Markdown", lambda t: _md_strip(t.inp_text())),
    ]


# --------------------------------------------------------------------------
# 12. Cron explainer
# --------------------------------------------------------------------------
_CRON_PRESETS = [
    ("Every minute", "* * * * *"),
    ("Every 5 min", "*/5 * * * *"),
    ("Hourly", "0 * * * *"),
    ("Daily 09:00", "0 9 * * *"),
    ("Weekdays 09:00", "0 9 * * 1-5"),
    ("Monthly (1st)", "0 0 1 * *"),
]

_MONTHS = ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"]
_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
         "Saturday"]


def _cron_field(field, lo, hi, names=None):
    values = set()
    for part in field.split(","):
        part = part.strip()
        step = 1
        if "/" in part:
            part, step_s = part.split("/", 1)
            step = int(step_s)
            if step < 1:
                raise ValueError("step must be >= 1")
        if part in ("*", ""):
            start, end = lo, hi
        elif "-" in part:
            a, b = part.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(part)
        if start > end:                      # wrap-around range e.g. 5-1
            for v in range(start, hi + 1):
                values.add(v)
            for v in range(lo, end + 1):
                values.add(v)
        else:
            for v in range(start, end + 1, step):
                values.add(v)
    for v in values:
        if v < lo or v > hi:
            raise ValueError(f"value {v} out of range {lo}-{hi}")
    if names:
        return [names[v % len(names)] for v in sorted(values)]
    return sorted(values)


def _describe(values, names=None, unit=""):
    if values is None:
        return "every"
    if not values:
        return "never"
    vals = [names[v % len(names)] if names else v for v in values]
    if len(vals) == 1:
        return f"at {vals[0]}{unit}"
    if len(vals) > 12:
        return f"{len(vals)} values ({vals[0]} … {vals[-1]})"
    return "at " + ", ".join(str(v) for v in vals)


def _explain_cron(expr):
    fields = expr.split()
    if len(fields) == 6:
        fields = fields[1:]            # skip seconds field
    if len(fields) != 5:
        raise ValueError("expected 5 fields: min hour dom month dow")

    minute = _cron_field(fields[0], 0, 59)
    hour = _cron_field(fields[1], 0, 23)
    dom = _cron_field(fields[2], 1, 31)
    month = _cron_field(fields[3], 1, 12, _MONTHS)
    dow = _cron_field(fields[4], 0, 7, _DAYS)

    every_dom = fields[2] in ("*", "?")
    every_month = fields[3] == "*"
    every_dow = fields[4] in ("*", "?")

    lines = [
        f"Minutes     : {_describe(minute)}",
        f"Hours       : {_describe(hour)}",
        f"Day of month: {'every day' if every_dom else _describe(dom)}",
        f"Month       : {'every month' if every_month else _describe(month)}",
        f"Day of week : {'every day' if every_dow else _describe(dow)}",
    ]

    if fields == ["*"] * 5:
        summary = "Every minute of every hour of every day."
    elif len(minute) > 1 and hour and every_dom and every_month and every_dow:
        summary = f"Every hour at minute(s) {', '.join(map(str, minute))}."
    elif minute == [0] and len(hour) > 1 and every_dom and every_month and every_dow:
        summary = ("Every day at "
                   + ", ".join(f"{h:02d}:00" for h in hour) + ".")
    elif len(minute) == 1 and len(hour) == 1 and every_dom and every_month \
            and every_dow:
        summary = f"Every day at {hour[0]:02d}:{minute[0]:02d}."
    else:
        summary = "See the field breakdown below."
    return summary + "\n\n" + "\n".join(lines)


class CronTool(_Panel):
    id = "cron"
    name = "Cron Explainer"
    icon = "⏰"
    description = "Turn a cron expression into plain English."
    keywords = ["cron", "schedule", "crontab", "expression", "job", "timer"]
    input_label = "Cron expression (min hour day month weekday)"
    output_label = "Meaning"
    output_height = 200

    actions = [
        ("Explain", lambda t: _explain_cron(t.inp_text().strip())),
        ("Every 5 min", lambda t: _preset(t, "*/5 * * * *")),
        ("Daily 09:00", lambda t: _preset(t, "0 9 * * *")),
        ("Weekdays 09:00", lambda t: _preset(t, "0 9 * * 1-5")),
        ("First of month", lambda t: _preset(t, "0 0 1 * *")),
    ]


def _preset(tool, expr):
    set_text(tool.inp, expr)
    return _explain_cron(expr)


# --------------------------------------------------------------------------
# 13. Encoding (hex / binary / rot13 / unicode / html)
# --------------------------------------------------------------------------
class EncodingTool(_Panel):
    id = "encoding"
    name = "Encoding Toolbox"
    icon = "🔡"
    description = "Hex, binary, ROT13, Unicode escapes and HTML entities."
    keywords = ["hex", "binary", "rot13", "unicode", "escape", "html", "ascii"]

    actions = [
        ("→ Hex", lambda t: t.inp_text().encode("utf-8").hex()),
        ("← Hex", lambda t: bytes.fromhex(
            re.sub(r"[^0-9a-fA-F]", "", t.inp_text())).decode("utf-8", "replace")),
        ("→ Binary", lambda t: " ".join(
            f"{b:08b}" for b in t.inp_text().encode("utf-8"))),
        ("← Binary", lambda t: _from_binary(t.inp_text())),
        ("ROT13", lambda t: t.inp_text().translate(str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"))),
        ("→ \\u escapes", lambda t: "".join(
            f"\\u{ord(c):04x}" if ord(c) > 127 else c
            for c in t.inp_text())),
        ("← \\u escapes", lambda t: re.sub(
            r"\\u([0-9a-fA-F]{4})|\\U([0-9a-fA-F]{8})",
            lambda m: chr(int(m.group(1) or m.group(2), 16)), t.inp_text())),
        ("Escape HTML", lambda t: html.escape(t.inp_text(), quote=True)),
        ("Unescape HTML", lambda t: html.unescape(t.inp_text())),
    ]


def _from_binary(text):
    bits = re.sub(r"[^01]", "", text)
    if not bits:
        raise ValueError("no binary digits found")
    if len(bits) % 8:
        bits = bits.zfill((len(bits) + 7) // 8 * 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)) \
        .decode("utf-8", "replace")
