"""
Patch the Green Group Project Manual Word document: replace Section 8
(Requirements) with content from RGEE-Requirements-Full.md, preserving
Heading2 / plain / ListBullet formatting cloned from the existing manual.

Usage:
  python scripts/patch_green_manual_requirements.py

Paths are configurable below. Creates a .bak copy of the output docx first.
"""

from __future__ import annotations

import copy
import os
import re
import shutil
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
W = "{%s}" % W_NS


def _qn(tag: str) -> str:
    return "{%s}%s" % (W_NS, tag)


def _para_text(p: ET.Element) -> str:
    parts: list[str] = []
    for t in p.findall(".//w:t", NS):
        if t.text:
            parts.append(t.text)
        if t.tail:
            parts.append(t.tail)
    return "".join(parts).strip()


def _para_style(p: ET.Element) -> str | None:
    ppr = p.find("w:pPr", NS)
    if ppr is None:
        return None
    ps = ppr.find("w:pStyle", NS)
    if ps is None:
        return None
    return ps.get(_qn("val"))


def _strip_md(s: str) -> str:
    """Remove common Markdown markers for Word plain text."""
    s = s.replace("**", "")
    s = s.replace("`", "")
    s = s.replace("\\", "")
    s = re.sub(r"\*{2,}$", "*", s)
    return s.strip()


def _md_heading_to_plain(line: str) -> str | None:
    line = line.strip()
    m = re.match(r"^#{2,4}\s+(.*)$", line)
    if not m:
        return None
    title = m.group(1).strip()
    title = re.sub(r"^7\.", "8.", title, count=1)
    return _strip_md(title)


def _is_table_separator(s: str) -> bool:
    s = s.strip().strip("|")
    if not s:
        return False
    return all(ch in "-: " for ch in s)


def _parse_markdown_table(lines: list[str], start: int) -> tuple[list[tuple[str, str]], int]:
    """From a row starting with |, consume the full table; return (bullets, next_index)."""
    out: list[tuple[str, str]] = []
    i = start
    if i >= len(lines) or not lines[i].strip().startswith("|"):
        return out, i
    header = [c.strip() for c in lines[i].split("|")[1:-1]]
    i += 1
    if i < len(lines) and _is_table_separator(lines[i]):
        i += 1
    while i < len(lines) and lines[i].strip().startswith("|"):
        cells = [c.strip() for c in lines[i].split("|")[1:-1]]
        if len(cells) >= 2:
            left = cells[0]
            rest = " — ".join(_strip_md(c) for c in cells[1:])
            if re.match(r"^[-:\s]+$", left) or left.lower() == "field":
                i += 1
                continue
            if len(header) >= 2 and header[0].lower() == "id" and "requirement" in header[1].lower():
                out.append(("bullet", f"{left} — {_strip_md(rest)}"))
            elif len(header) >= 2 and header[0].lower() == "prefix":
                out.append(("bullet", f"{left}: {_strip_md(rest)}"))
            else:
                out.append(("bullet", f"{_strip_md(left)} — {_strip_md(rest)}"))
        i += 1
    return out, i


def _parse_md_to_blocks(md_path: Path) -> list[tuple[str, str]]:
    """Return list of ('h2'|'p'|'bullet', text) matching manual styles."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    blocks: list[tuple[str, str]] = [("h2", "8. Requirements (As Implemented)")]

    i = 0
    in_canonical = False
    saw_first_h1 = False

    while i < len(lines):
        stripped = lines[i].strip()

        if stripped.startswith("# ") and not saw_first_h1:
            saw_first_h1 = True
            i += 1
            continue

        if stripped.startswith("**Canonical copy"):
            in_canonical = True
            i += 1
            continue
        if in_canonical:
            if stripped.startswith("---"):
                in_canonical = False
            i += 1
            continue

        if stripped == "---":
            i += 1
            continue

        if stripped.startswith("## 7. Requirements"):
            i += 1
            continue

        if stripped.startswith("| Field |"):
            i += 1
            if i < len(lines) and _is_table_separator(lines[i]):
                i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [c.strip() for c in lines[i].split("|")[1:-1]]
                if len(row) >= 2 and row[0] and row[0] != "Field":
                    blocks.append(("bullet", f"{row[0]}: {_strip_md(' | '.join(row[1:]))}"))
                i += 1
            continue

        if stripped.startswith("|"):
            tbl, ni = _parse_markdown_table(lines, i)
            blocks.extend(tbl)
            i = ni
            continue

        ph = _md_heading_to_plain(lines[i])
        if ph:
            if ph.startswith("8. Requirements"):
                i += 1
                continue
            blocks.append(("p", ph))
            i += 1
            continue

        if re.match(r"^\d+\.\s+", stripped):
            blocks.append(("bullet", _strip_md(stripped)))
            i += 1
            continue

        if stripped.startswith("*End of requirements"):
            break

        if not stripped:
            i += 1
            continue

        if stripped.startswith("!"):
            i += 1
            continue

        buf = [_strip_md(stripped)]
        i += 1
        while i < len(lines):
            nx = lines[i].strip()
            if not nx:
                break
            if nx.startswith("#") or nx.startswith("|") or nx.startswith("---"):
                break
            if nx.startswith("**Canonical"):
                break
            buf.append(_strip_md(nx))
            i += 1
        para = " ".join(x for x in buf if x)
        if para:
            blocks.append(("p", para))

    return blocks


def _clear_runs(p: ET.Element) -> None:
    for r in list(p.findall("w:r", NS)):
        p.remove(r)


def _set_simple_text(p: ET.Element, text: str) -> None:
    _clear_runs(p)
    r = ET.SubElement(p, _qn("r"))
    t = ET.SubElement(r, _qn("t"))
    if text.startswith(" ") or text.endswith(" ") or "  " in text:
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text


def _clone_para(template: ET.Element) -> ET.Element:
    return copy.deepcopy(template)


def _find_section_bounds(body: ET.Element) -> tuple[int, int]:
    children = list(body)
    start = end = None
    for i, ch in enumerate(children):
        if ch.tag != _qn("p"):
            continue
        tx = _para_text(ch)
        st = _para_style(ch)
        if st == "Heading2" and tx.startswith("8.") and "Requirement" in tx:
            start = i
            continue
        if start is not None and st == "Heading2" and tx.startswith("9.") and "Security" in tx:
            end = i
            break
    if start is None or end is None:
        raise RuntimeError("Could not find section 8 (Requirements) or section 9 (Security) headings.")
    return start, end


def patch_manual(
    manual_in: Path,
    md_source: Path,
    manual_out: Path,
    work_dir: Path,
) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = work_dir / "doc_unpacked"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir()

    with zipfile.ZipFile(manual_in, "r") as zin:
        zin.extractall(extract_dir)

    doc_xml = extract_dir / "word" / "document.xml"
    tree = ET.parse(doc_xml)
    root = tree.getroot()
    body = root.find("w:body", NS)
    if body is None:
        raise RuntimeError("No w:body in document.xml")

    children = list(body)
    start, end = _find_section_bounds(body)

    tmpl_h2 = children[start]
    tmpl_plain = None
    tmpl_bullet = None
    for j in range(start + 1, min(start + 8, end)):
        if children[j].tag != _qn("p"):
            continue
        st = _para_style(children[j])
        if st is None and tmpl_plain is None and _para_text(children[j]):
            tmpl_plain = children[j]
        if st == "ListBullet":
            tmpl_bullet = children[j]
            break
    if tmpl_plain is None or tmpl_bullet is None:
        raise RuntimeError("Could not clone paragraph templates from manual.")

    for idx in range(end - 1, start - 1, -1):
        body.remove(children[idx])

    blocks = _parse_md_to_blocks(md_source)
    insert_at = start

    for kind, text in blocks:
        if not text:
            continue
        if kind == "h2":
            p = _clone_para(tmpl_h2)
            _set_simple_text(p, text)
        elif kind == "bullet":
            p = _clone_para(tmpl_bullet)
            _set_simple_text(p, text)
        else:
            p = _clone_para(tmpl_plain)
            _set_simple_text(p, text)
        body.insert(insert_at, p)
        insert_at += 1

    tree.write(doc_xml, encoding="utf-8", xml_declaration=True)

    with zipfile.ZipFile(manual_out, "w", zipfile.ZIP_DEFLATED) as zout:
        for f in sorted(extract_dir.rglob("*")):
            if f.is_file():
                arc = f.relative_to(extract_dir).as_posix()
                zout.write(f, arcname=arc)


def main() -> None:
    manual_in = Path(r"C:\Users\nigel\Downloads\Green Group Project Manual.docx")
    md_source = Path(r"C:\Users\nigel\RubricGuidedEssayExam\docs\RGEE-Requirements-Full.md")
    work = Path(r"C:\Users\nigel\AppData\Local\Temp\green_manual_patch_work")
    work_in = work / "_source_manual.docx"
    out_tmp = work / "_patched_manual.docx"

    if not manual_in.is_file():
        raise SystemExit(f"Missing manual: {manual_in}")
    if not md_source.is_file():
        raise SystemExit(f"Missing MD: {md_source}")

    work.mkdir(parents=True, exist_ok=True)
    shutil.copy2(manual_in, work_in)
    bak = manual_in.with_name(manual_in.stem + ".bak-before-requirements-patch" + manual_in.suffix)
    shutil.copy2(manual_in, bak)
    patch_manual(work_in, md_source, out_tmp, work)
    os.replace(out_tmp, manual_in)
    print("Updated:", manual_in)
    print("Backup:", bak)


if __name__ == "__main__":
    main()
