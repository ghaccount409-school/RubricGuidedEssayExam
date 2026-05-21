"""
Generate requirements-test-traceability.docx and .pptx using only the Python stdlib.
Run: python docs/generate_traceability_office_stdlib.py

For richer formatting, install python-docx and python-pptx and run generate_traceability_office.py instead.
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from importlib import util as importlib_util
from xml.sax.saxutils import escape

DOCS = Path(__file__).resolve().parent


def _load_traceability():
    path = DOCS / "traceability_data.py"
    spec = importlib_util.spec_from_file_location("traceability_data", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    mod = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ROWS_MAIN, mod.ROWS_UNIT


ROWS_MAIN, ROWS_UNIT = _load_traceability()


def _w_p(text: str) -> str:
    return (
        f'<w:p><w:r><w:rPr/><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'
    )


def _w_heading(text: str, level: int) -> str:
    # Word heading styles are optional; use bold large-ish via w:b
    return (
        f'<w:p><w:pPr><w:pStyle w:val="Heading{level}"/></w:pPr>'
        f'<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'
    )


def build_document_xml() -> str:
    parts: list[str] = []
    parts.append(_w_heading("Requirements-to-Tests Traceability", 1))
    parts.append(_w_p("RubricGuidedEssayExam — SRS v1.1 mapping to pytest."))
    parts.append(
        _w_p("Repository: https://github.com/ALGeek01/RubricGuidedEssayExam")
    )
    parts.append(
        _w_p("Tests: MOCK_LLM=1; isolated SQLite (tests/conftest.py).")
    )
    parts.append(_w_heading("Test inventory", 2))
    parts.append(_w_p("conftest.py — DB + MOCK_LLM + TestClient + reset"))
    parts.append(_w_p("general/test_unit.py — unit"))
    parts.append(_w_p("general/test_api.py — integration"))
    parts.append(_w_p("security/test_http.py — security"))
    parts.append(_w_heading("SRS requirement → tests (with explanations)", 2))

    col_w = ("2200", "2600", "1800", "5200")  # dxa — total ~11800 (wide table)
    tbl_rows = []
    headers = ("Requirement", "Test(s)", "Coverage note", "Explanation")
    tbl_rows.append(
        "<w:tr>"
        + "".join(
            f'<w:tc><w:tcPr><w:tcW w:w="{col_w[i]}" w:type="dxa"/></w:tcPr>'
            f'<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>{escape(h)}</w:t></w:r></w:p></w:tc>'
            for i, h in enumerate(headers)
        )
        + "</w:tr>"
    )
    for req, tst, note, expl in ROWS_MAIN:
        cells = (req, tst, note, expl)
        tbl_rows.append(
            "<w:tr>"
            + "".join(
                f'<w:tc><w:tcPr><w:tcW w:w="{col_w[i]}" w:type="dxa"/></w:tcPr>'
                f'<w:p><w:r><w:t xml:space="preserve">{escape(c)}</w:t></w:r></w:p></w:tc>'
                for i, c in enumerate(cells)
            )
            + "</w:tr>"
        )
    table = (
        '<w:tbl><w:tblPr><w:tblW w:w="11800" w:type="dxa"/>'
        '<w:tblBorders><w:top w:val="single" w:sz="4"/><w:left w:val="single" w:sz="4"/>'
        '<w:bottom w:val="single" w:sz="4"/><w:right w:val="single" w:sz="4"/>'
        '<w:insideH w:val="single" w:sz="4"/><w:insideV w:val="single" w:sz="4"/>'
        "</w:tblBorders></w:tblPr>"
        + "".join(tbl_rows)
        + "</w:tbl>"
    )
    parts.append(table)

    parts.append(_w_heading("Unit tests vs SRS (with explanations)", 2))
    uc_w = ("2800", "2400", "5200")
    ut_rows = [
        "<w:tr>"
        + "".join(
            f'<w:tc><w:tcPr><w:tcW w:w="{uc_w[i]}" w:type="dxa"/></w:tcPr>'
            f'<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>{escape(h)}</w:t></w:r></w:p></w:tc>'
            for i, h in enumerate(("Test", "SRS relationship", "Explanation"))
        )
        + "</w:tr>"
    ]
    for test_name, srs_rel, expl in ROWS_UNIT:
        ut_rows.append(
            "<w:tr>"
            + "".join(
                f'<w:tc><w:tcPr><w:tcW w:w="{uc_w[i]}" w:type="dxa"/></w:tcPr>'
                f'<w:p><w:r><w:t xml:space="preserve">{escape(c)}</w:t></w:r></w:p></w:tc>'
                for i, c in enumerate((test_name, srs_rel, expl))
            )
            + "</w:tr>"
        )
    utable = (
        '<w:tbl><w:tblPr><w:tblW w:w="10400" w:type="dxa"/>'
        '<w:tblBorders><w:top w:val="single" w:sz="4"/><w:left w:val="single" w:sz="4"/>'
        '<w:bottom w:val="single" w:sz="4"/><w:right w:val="single" w:sz="4"/>'
        '<w:insideH w:val="single" w:sz="4"/><w:insideV w:val="single" w:sz="4"/>'
        "</w:tblBorders></w:tblPr>"
        + "".join(ut_rows)
        + "</w:tbl>"
    )
    parts.append(utable)

    parts.append(_w_heading("Summary", 2))
    parts.append(
        _w_p(
            "Covered: basic exam flow, two questions, 404s, professor smoke, "
            "no traceback on errors, duplicate answer rejected."
        )
    )
    parts.append(
        _w_p(
            "Gaps: FR-GEN-1 sandbox, FR-SEC-*, timers, schema grading, follow-ups, "
            "DB retention, final schemes, disputes, export, most NFRs."
        )
    )

    body = "".join(parts)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<w:body>{body}<w:sectPr><w:pgSz w:w="15840" w:h="12240" w:orient="landscape"/><w:pgMar w:top="1008" w:right="1008" w:bottom="1008" w:left="1008"/></w:sectPr></w:body>
</w:document>'''


CONTENT_TYPES_DOCX = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

RELS_ROOT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:lang w:val="en-US"/></w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:uiPriority w:val="9"/><w:qFormat/><w:pPr><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:uiPriority w:val="9"/><w:qFormat/><w:pPr><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>
</w:styles>"""


def write_docx(path: Path) -> None:
    doc_xml = build_document_xml()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES_DOCX)
        z.writestr("_rels/.rels", RELS_ROOT)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/document.xml", doc_xml.encode("utf-8"))
        z.writestr("word/styles.xml", STYLES_XML.encode("utf-8"))


# --- Minimal PPTX (single title + bullet slide + mapping slide) ---
# Namespaces
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _pptx_content_types() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
<Override PartName="/ppt/slides/slide2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
<Override PartName="/ppt/slides/slide3.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""


def _pptx_rels_root() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def _pptx_presentation() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="{P}" xmlns:r="{R}" saveSubsetFonts="1">
<p:sldMasterIdLst><p:sldMasterId r:id="rId1"/></p:sldMasterIdLst>
<p:sldIdLst>
<p:sldId id="256" r:id="rId2"/><p:sldId id="257" r:id="rId3"/><p:sldId id="258" r:id="rId4"/>
</p:sldIdLst>
<p:sldSz cx="9144000" cy="6858000"/>
</p:presentation>"""


def _pptx_presentation_rels() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide2.xml"/>
<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide3.xml"/>
</Relationships>"""


def _pptx_slide_master() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}">
<p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg><p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
</p:spTree></p:cSld>
<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
</p:sldMaster>"""


def _pptx_slide_master_rels() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""


def _pptx_slide_layout() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:p="{P}" xmlns:a="{A}" type="obj" preserve="1">
<p:cSld name="Title and Content"><p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="457200" y="274638"/><a:ext cx="8229600" cy="1143000"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" dirty="0"/><a:t>Title</a:t></a:r></a:p></p:txBody></p:sp>
<p:sp><p:nvSpPr><p:cNvPr id="3" name="Content Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph idx="1"/></p:nvPr></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="457200" y="1600200"/><a:ext cx="8229600" cy="4525963"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr lvl="0"/><a:r><a:rPr lang="en-US" dirty="0"/><a:t>Body</a:t></a:r></a:p></p:txBody></p:sp>
</p:spTree></p:cSld></p:sldLayout>"""


def _pptx_slide_layout_rels() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""


def _pptx_theme() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="{A}" name="Office Theme">
<a:themeElements>
<a:clrScheme name="Office">
<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
<a:dk2><a:srgbClr val="1F497D"/></a:dk2>
<a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
<a:accent1><a:srgbClr val="4F81BD"/></a:accent1>
<a:accent2><a:srgbClr val="C0504D"/></a:accent2>
<a:accent3><a:srgbClr val="9BBB59"/></a:accent3>
<a:accent4><a:srgbClr val="8064A2"/></a:accent4>
<a:accent5><a:srgbClr val="4BACC6"/></a:accent5>
<a:accent6><a:srgbClr val="F79646"/></a:accent6>
<a:hlink><a:srgbClr val="0000FF"/></a:hlink>
<a:folHlink><a:srgbClr val="800080"/></a:folHlink>
</a:clrScheme>
<a:fontScheme name="Office">
<a:majorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
<a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>
</a:fontScheme>
<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
<a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
</a:fmtScheme>
</a:themeElements>
</a:theme>"""


def _pptx_slide(title: str, bullets: list[str], layout_rid: str = "rId1") -> str:
    body_paras = ""
    for b in bullets:
        body_paras += f'<a:p><a:pPr lvl="0"/><a:r><a:rPr lang="en-US"/><a:t>{escape(b)}</a:t></a:r></a:p>'
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}">
<p:cSld><p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="457200" y="274638"/><a:ext cx="8229600" cy="1143000"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US"/><a:t>{escape(title)}</a:t></a:r></a:p></p:txBody></p:sp>
<p:sp><p:nvSpPr><p:cNvPr id="3" name="Content Placeholder 2"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="457200" y="1600200"/><a:ext cx="8229600" cy="4525963"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/>{body_paras}</p:txBody></p:sp>
</p:spTree></p:cSld></p:sld>"""


def _pptx_slide_rels() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""


def _pptx_core() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>Requirements Test Traceability</dc:title>
<dc:creator>RubricGuidedEssayExam docs</dc:creator>
</cp:coreProperties>"""


def _pptx_app() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
<TotalTime>0</TotalTime><Words>0</Words><Application>Python stdlib generator</Application></Properties>"""


def write_pptx(path: Path) -> None:
    s1 = _pptx_slide(
        "Requirements ↔ Test Traceability",
        [
            "RubricGuidedEssayExam",
            "SRS v1.1 → pytest mapping",
            "github.com/ALGeek01/RubricGuidedEssayExam",
        ],
    )
    s2 = _pptx_slide(
        "Covered in tests",
        [
            "Exam start → question → answer → results (MOCK_LLM)",
            "Two-question flow",
            "404 missing exam / professor detail",
            "Professor dashboard + detail (smoke)",
            "Reject duplicate POST /answer (400)",
            "Invalid education level / blank student id",
            "404 HTML without Python traceback",
        ],
    )
    s3 = _pptx_slide(
        "Major gaps vs SRS",
        [
            "FR-GEN-1 LLM Python + sandbox",
            "FR-SEC-1 / FR-SEC-2",
            "FR-STU-3/4/5 length, autosave, timers",
            "FR-GRADE schema, FR-FU, FR-DB retention",
            "FR-FINAL schemes, FR-DISP disputes, FR-REVIEW-3 export",
            "NFR-PERF, REL, AUDIT, WCAG",
        ],
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _pptx_content_types())
        z.writestr("_rels/.rels", _pptx_rels_root())
        z.writestr("ppt/presentation.xml", _pptx_presentation())
        z.writestr("ppt/_rels/presentation.xml.rels", _pptx_presentation_rels())
        z.writestr("ppt/slideMasters/slideMaster1.xml", _pptx_slide_master())
        z.writestr(
            "ppt/slideMasters/_rels/slideMaster1.xml.rels",
            _pptx_slide_master_rels(),
        )
        z.writestr("ppt/slideLayouts/slideLayout1.xml", _pptx_slide_layout())
        z.writestr(
            "ppt/slideLayouts/_rels/slideLayout1.xml.rels",
            _pptx_slide_layout_rels(),
        )
        z.writestr("ppt/theme/theme1.xml", _pptx_theme())
        z.writestr("ppt/slides/slide1.xml", s1.encode("utf-8"))
        z.writestr("ppt/slides/_rels/slide1.xml.rels", _pptx_slide_rels())
        z.writestr("ppt/slides/slide2.xml", s2.encode("utf-8"))
        z.writestr("ppt/slides/_rels/slide2.xml.rels", _pptx_slide_rels())
        z.writestr("ppt/slides/slide3.xml", s3.encode("utf-8"))
        z.writestr("ppt/slides/_rels/slide3.xml.rels", _pptx_slide_rels())
        z.writestr("docProps/core.xml", _pptx_core())
        z.writestr("docProps/app.xml", _pptx_app())


def main() -> None:
    docx_path = DOCS / "requirements-test-traceability.docx"
    pptx_path = DOCS / "requirements-test-traceability.pptx"
    try:
        write_docx(docx_path)
        print(f"Wrote {docx_path}")
    except PermissionError:
        alt = DOCS / "requirements-test-traceability (generated).docx"
        write_docx(alt)
        print(
            f"Could not overwrite {docx_path} (file may be open in Word). Wrote {alt} instead."
        )
    try:
        write_pptx(pptx_path)
        print(f"Wrote {pptx_path}")
    except PermissionError:
        altp = DOCS / "requirements-test-traceability (generated).pptx"
        write_pptx(altp)
        print(
            f"Could not overwrite {pptx_path} (file may be open). Wrote {altp} instead."
        )


if __name__ == "__main__":
    main()
