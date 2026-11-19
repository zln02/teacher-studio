# SPDX-License-Identifier: Apache-2.0
"""Tests for shared/design/oklch.py, color_check.py, color_from.py and design.py --palette-from.

Run:  py -m unittest shared/tools/test_color.py -v      (stdlib only; the JPEG test is skipped without Pillow)
Nothing here touches ~/.teacher-studio (prefs paths are redirected to a temp folder).
"""
import importlib.util
import json
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

DESIGN = Path(__file__).resolve().parent.parent / "design"
sys.path.insert(0, str(DESIGN))
import color_check as cc  # noqa: E402
import color_from as cf  # noqa: E402
import design  # noqa: E402
import oklch as ok  # noqa: E402


def make_png(path: Path, w: int = 48, h: int = 48) -> Path:
    """A small PNG made here: white margin (background), top half blue #1e5bb8, bottom half orange #f28c28, one transparent column."""
    rows = b""
    for y in range(h):
        rows += b"\x00"
        for x in range(w):
            if x < 8:
                px = (255, 255, 255, 255)
            elif x == 8:
                px = (255, 0, 0, 0)  # transparent: must be ignored
            else:
                px = (0x1E, 0x5B, 0xB8, 255) if y < h // 2 else (0xF2, 0x8C, 0x28, 255)
            rows += bytes(px)

    def chunk(t: bytes, d: bytes) -> bytes:
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))

    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
    return path


def theme_xml(accent1: str = "C00000", accent2: str = "00B050") -> str:
    ns = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
    items = {"dk1": "000000", "lt1": "FFFFFF", "dk2": "44546A", "lt2": "E7E6E6", "accent1": accent1, "accent2": accent2, "accent3": "A5A5A5",
             "accent4": "FFC000", "accent5": "5B9BD5", "accent6": "70AD47", "hlink": "0563C1", "folHlink": "954F72"}
    body = "".join(f'<a:{k}><a:srgbClr val="{v}"/></a:{k}>' for k, v in items.items())
    return f'<?xml version="1.0"?><a:theme {ns} name="T"><a:themeElements><a:clrScheme name="T">{body}</a:clrScheme></a:themeElements></a:theme>'


def make_office(path: Path, folder: str, **kw) -> Path:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr(f"{folder}/theme/theme1.xml", theme_xml(**kw))
    return path


class OklchTests(unittest.TestCase):
    def test_red_known_value(self):
        L, C, h = ok.hex_to_oklch("#ff0000")
        self.assertAlmostEqual(L, 0.628, places=3)
        self.assertAlmostEqual(C, 0.258, places=3)
        self.assertAlmostEqual(h, 29.2, delta=0.1)

    def test_white_black_grey(self):
        self.assertAlmostEqual(ok.hex_to_oklab("#ffffff")[0], 1.0, places=3)
        self.assertAlmostEqual(ok.hex_to_oklab("#000000")[0], 0.0, places=3)
        self.assertLess(ok.hex_to_oklch("#808080")[1], 0.002)

    def test_roundtrip(self):
        for c in ("#ff0000", "#00ff00", "#0000ff", "#12abef", "#f28c28", "#777777", "#fefefe", "#010203"):
            L, C, h = ok.hex_to_oklch(c)
            self.assertEqual(ok.oklch_to_hex(L, C, h), c)

    def test_gamut_clamp_keeps_lightness_and_hue(self):
        self.assertFalse(ok.in_gamut(0.5, 0.4, 150))
        L, C, h = ok.clamp_chroma(0.5, 0.4, 150)
        self.assertTrue(ok.in_gamut(L, C, h))
        self.assertLess(C, 0.4)
        self.assertEqual((L, h), (0.5, 150))
        L2, _, h2 = ok.hex_to_oklch(ok.oklch_to_hex(0.5, 0.4, 150))
        self.assertAlmostEqual(L2, 0.5, delta=0.01)
        self.assertAlmostEqual(h2, 150, delta=1.5)

    def test_harmonies(self):
        seed = "#2b6cff"
        h0 = ok.hex_to_oklch(seed)[2]
        tri = ok.harmony(seed, "triad")
        self.assertEqual(len(tri), 3)
        self.assertEqual(tri[0], seed)
        self.assertAlmostEqual(ok.hue_distance(ok.hex_to_oklch(tri[1])[2], h0), 120, delta=6)
        comp = ok.harmony(seed, "complementary")
        self.assertAlmostEqual(ok.hue_distance(ok.hex_to_oklch(comp[1])[2], h0), 180, delta=6)
        ana = ok.harmony(seed, "analogous")
        self.assertEqual(len(ana), 3)
        with self.assertRaises(ValueError):
            ok.harmony(seed, "nope")

    def test_ramp_equal_perceived_steps(self):
        r = ok.ramp("#7a8cff", 5, 0.3, 0.9)
        ls = [ok.hex_to_oklch(c)[0] for c in r]
        steps = [b - a for a, b in zip(ls, ls[1:])]
        self.assertTrue(all(abs(s - 0.15) < 0.015 for s in steps), steps)
        ts = ok.tints_shades("#7a8cff", 2, 0.08)
        self.assertGreater(ok.hex_to_oklch(ts["tints"][0])[0], ok.hex_to_oklch("#7a8cff")[0])
        self.assertLess(ok.hex_to_oklch(ts["shades"][1])[0], ok.hex_to_oklch(ts["shades"][0])[0])

    def test_fit_contrast_lightness_only(self):
        orange = "#ff9900"
        self.assertLess(ok.contrast(orange, "#ffffff"), 4.5)
        fixed = ok.fit_contrast(orange, "#ffffff", 4.5)
        self.assertGreaterEqual(ok.contrast(fixed, "#ffffff"), 4.5)
        self.assertAlmostEqual(ok.hue_distance(ok.hex_to_oklch(fixed)[2], ok.hex_to_oklch(orange)[2]), 0, delta=3)
        self.assertEqual(ok.fit_contrast("#000000", "#ffffff", 4.5), "#000000")

    def test_contrast_matches_design(self):
        for a, b in (("#123456", "#fedcba"), ("#000", "#fff")):
            self.assertAlmostEqual(ok.contrast(a if len(a) == 7 else "#000000", b if len(b) == 7 else "#ffffff"),
                                   design.contrast(a if len(a) == 7 else "#000000", b if len(b) == 7 else "#ffffff"), places=6)


class ColorCheckTests(unittest.TestCase):
    def test_matrices_keep_white(self):
        for k in cc.MACHADO:
            self.assertEqual(cc.simulate("#ffffff", k), "#ffffff", k)

    def test_protan_darkens_red(self):
        self.assertLess(ok.hex_to_oklab(cc.simulate("#ff0000", "protan"))[0], ok.hex_to_oklab("#ff0000")[0] - 0.1)

    def test_red_green_pair_flagged(self):
        f = cc.check_pairs({"good": "#0f8a4a", "bad": "#c4163a"})
        self.assertEqual(len(f), 1)
        self.assertIn(f[0]["kind"], ("protan", "deutan"))
        self.assertLess(f[0]["de"], cc.MIN_DE)
        line = cc.warn_lines(f)[0]
        self.assertIn("빨강·초록만으로 구분하고 있어요. 모양이나 글자", line)

    def test_blue_orange_pair_ok(self):
        self.assertEqual(cc.check_pairs({"a": "#1e5bb8", "b": "#f2a900"}), [])

    def test_tokens_and_html(self):
        tk = {"colors": {"good": "#0f8a4a", "bad": "#c4163a"}}
        self.assertEqual(len(cc.check_tokens(tk)), 1)
        html = '<style>:root{--good:#0f8a4a;--bad:#c4163a}</style>'
        self.assertEqual(cc.html_results(html)[0][0], "WARN")
        ok_html = '<style>:root{--good:#1e5bb8;--bad:#f2a900}</style>'
        self.assertEqual(cc.html_results(ok_html)[0][0], "PASS")
        self.assertEqual(cc.html_results("<p>nothing</p>"), [])
        chart = '{"colors":["#0f8a4a","#c4163a","#2b6cff"]}'
        self.assertTrue(any(lv == "WARN" for lv, _ in cc.html_results(chart)))

    def test_generated_palette_is_cb_safe(self):
        r = cf.tokens_from_seeds("#1e5bb8", "#f28c28")
        self.assertEqual(cc.check_pairs({"good": r["good"], "bad": r["bad"]}), [])
        r = cf.tokens_from_seeds("#1e5bb8", "#f28c28", dark=True)
        self.assertEqual(cc.check_pairs({"good": r["good"], "bad": r["bad"]}), [])


class ColorFromTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.dir = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def assertTokensOk(self, pal):
        c = pal["colors"]
        self.assertEqual(set(c), set(cf.KEYS))
        self.assertEqual(design.palette_issues("t", c), [])
        for fg, bg in (("text", "bg1"), ("text", "bg2"), ("cardText", "card"), ("btnText", "primary")):
            self.assertGreaterEqual(ok.contrast(c[fg], c[bg]), 4.5, (fg, bg))

    def test_png_decoder_and_seeds(self):
        p = make_png(self.dir / "logo.png")
        w, h, px = cf.decode_png(p.read_bytes())
        self.assertEqual((w, h, len(px)), (48, 48, 48 * 48))
        self.assertEqual(px[0], (255, 255, 255, 255))
        pal = cf.extract(p)
        self.assertEqual(pal["source"]["type"], "image")
        self.assertEqual({pal["seeds"]["primary"], pal["seeds"]["accent"]}, {"#1e5bb8", "#f28c28"})  # white margin and transparent column skipped
        self.assertTokensOk(pal)
        self.assertNotIn("#ff0000", [s["hex"] for s in pal["swatches"]])

    def test_png_dark_mode(self):
        pal = cf.extract(make_png(self.dir / "logo.png"), dark=True)
        self.assertEqual(pal["mode"], "dark")
        self.assertLess(ok.luminance(pal["colors"]["bg1"]), 0.1)
        self.assertTokensOk(pal)

    def test_all_white_image_is_a_clear_error(self):
        # a 4x4 all-white PNG: nothing but background
        raw = b"".join(b"\x00" + b"\xff\xff\xff" * 4 for _ in range(4))
        chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))  # noqa: E731
        f = self.dir / "white.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
        with self.assertRaises(cf.ColorFromError):
            cf.extract(f)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow not installed")
    def test_jpeg_via_pillow(self):
        from PIL import Image
        im = Image.new("RGB", (40, 40), (255, 255, 255))
        for x in range(10, 40):
            for y in range(40):
                im.putpixel((x, y), (0x1E, 0x5B, 0xB8) if y < 20 else (0xF2, 0x8C, 0x28))
        f = self.dir / "photo.jpg"
        im.save(f, quality=95)
        pal = cf.extract(f)
        self.assertLess(ok.delta_e(pal["seeds"]["primary"], "#f28c28") if ok.delta_e(pal["seeds"]["primary"], "#f28c28") < ok.delta_e(pal["seeds"]["primary"], "#1e5bb8")
                        else ok.delta_e(pal["seeds"]["primary"], "#1e5bb8"), 0.08)
        self.assertTokensOk(pal)

    def test_pptx_theme(self):
        p = make_office(self.dir / "deck.pptx", "ppt", accent1="C00000", accent2="1F4E9C")
        pal = cf.extract(p)
        self.assertEqual(pal["source"]["type"], "office-theme")
        self.assertEqual(pal["office"]["accent1"], "#c00000")
        self.assertEqual(pal["seeds"], {"primary": "#c00000", "accent": "#1f4e9c"})
        # lightness-only fit: the hue of the final primary stays the theme's red
        self.assertAlmostEqual(ok.hue_distance(ok.hex_to_oklch(pal["colors"]["primary"])[2], ok.hex_to_oklch("#c00000")[2]), 0, delta=3)
        self.assertTokensOk(pal)

    def test_potx_docx_xlsx(self):
        for ext, folder in ((".potx", "ppt"), (".docx", "word"), (".xlsx", "xl")):
            pal = cf.extract(make_office(self.dir / f"t{ext}", folder, accent1="2E7D32", accent2="FF6F00"))
            self.assertEqual(pal["seeds"]["primary"], "#2e7d32", ext)
            self.assertTokensOk(pal)

    def test_office_without_theme_message(self):
        f = self.dir / "empty.pptx"
        with zipfile.ZipFile(f, "w") as z:
            z.writestr("[Content_Types].xml", "<Types/>")
        with self.assertRaises(cf.ColorFromError):
            cf.extract(f)

    def test_hwpx_colour_attributes(self):
        f = self.dir / "doc.hwpx"
        header = ('<hh:head xmlns:hh="x"><hh:charPr id="0" textColor="#000000"/><hh:charPr id="1" textColor="#1F6FB2"/><hh:charPr id="2" textColor="#1F6FB2"/>'
                  '<hh:fillBrush><hc:winBrush faceColor="#FFFFFF" hatchColor="#000000"/></hh:fillBrush><hh:fillBrush><hc:winBrush faceColor="#E8A33D"/></hh:fillBrush></hh:head>')
        with zipfile.ZipFile(f, "w") as z:
            z.writestr("mimetype", "application/hwp+zip")
            z.writestr("Contents/header.xml", header)
        pal = cf.extract(f)
        self.assertEqual(pal["source"]["type"], "hwpx")
        self.assertEqual(pal["seeds"]["primary"], "#1f6fb2")
        self.assertTokensOk(pal)

    def test_css_frequencies_and_variable_names(self):
        f = self.dir / "site.css"
        f.write_text(":root{--brand:#7b2cbf;--bg:#ffffff} a{color:#7b2cbf} b{color:#ff9e00} i{color:#ff9e00} u{color:#ff9e00} p{color:rgb(255,158,0)} body{color:#222}", encoding="utf-8")
        pal = cf.extract(f)
        self.assertEqual(pal["seeds"]["primary"], "#7b2cbf")  # the --brand variable wins over the more frequent orange
        self.assertEqual(pal["seeds"]["accent"], "#ff9e00")
        self.assertTokensOk(pal)

    def test_greyscale_logo_note(self):
        f = self.dir / "gray.css"
        f.write_text("a{color:#444444} b{color:#444444} c{color:#888888}", encoding="utf-8")
        pal = cf.extract(f)
        self.assertTrue(pal["notes"])
        self.assertTokensOk(pal)

    def test_old_formats_and_unknown(self):
        for name in ("a.hwp", "a.ppt", "a.xyz"):
            f = self.dir / name
            f.write_bytes(b"x")
            with self.assertRaises(cf.ColorFromError):
                cf.extract(f)

    def test_fit_palette_repairs_low_contrast(self):
        bad = {"primary": "#ffee00", "bg1": "#ffffff", "bg2": "#f0f0f0", "text": "#bbbbbb", "card": "#ffffff", "cardText": "#cccccc"}
        fixed = cf.fit_palette(bad)
        self.assertEqual(design.palette_issues("t", fixed), [])
        self.assertEqual(fixed["primary"] == bad["primary"], False)  # a yellow primary on white had to be darkened
        with self.assertRaises(cf.ColorFromError):
            cf.fit_palette({"primary": "red"})

    def test_cli_out_and_exit_codes(self):
        p = make_png(self.dir / "logo.png")
        out = self.dir / "pal.json"
        old = sys.argv
        sys.argv = ["color_from.py", str(p), "--out", str(out)]
        try:
            self.assertEqual(cf.main(), 0)
        finally:
            sys.argv = old
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["kind"], "user-palette")
        sys.argv = ["color_from.py", str(self.dir / "missing.png")]
        try:
            self.assertEqual(cf.main(), 1)
        finally:
            sys.argv = old

    def test_save_default_to_temp_prefs(self):
        pal = cf.extract(make_png(self.dir / "logo.png"))
        prefs = self.dir / "prefs.json"
        prefs.write_text(json.dumps({"level": "초등학교", "taste": ["밝게"]}, ensure_ascii=False), encoding="utf-8")
        cf._prefs_module = lambda: None  # fall back to the plain JSON writer
        cf.prefs_path = lambda: prefs
        try:
            cf.save_default(pal)
        finally:
            del cf._prefs_module, cf.prefs_path
            importlib.reload(cf)
        data = json.loads(prefs.read_text(encoding="utf-8"))
        self.assertEqual(data["level"], "초등학교")  # other prefs are kept
        self.assertEqual(data["taste"], ["밝게"])
        self.assertEqual(data["palette"]["colors"], pal["colors"])


class PrefsModuleTests(unittest.TestCase):
    def test_prefs_palette_roundtrip_keeps_taste(self):
        p = Path(__file__).resolve().parents[2] / "skills" / "teacher-studio" / "scripts" / "prefs.py"
        spec = importlib.util.spec_from_file_location("ts_prefs_test", p)
        prefs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prefs)
        with tempfile.TemporaryDirectory() as td:
            prefs.PATH = Path(td) / "prefs.json"
            prefs.add_taste(["밝게"])
            prefs.save({"level": "중학교", "subject": "과학", "device": "board"})
            cols = cf.tokens_from_seeds("#1e5bb8", "#f28c28")
            prefs.save_palette({"palette": "user-logo", "mode": "light", "colors": cols, "source": {"file": "logo.png"}})
            self.assertEqual(prefs.load_palette()["colors"], cols)
            prefs.add_taste(["글씨 크게"])  # later writes must not drop the palette
            prefs.save({"level": "고등학교"})
            self.assertEqual(prefs.load_palette()["colors"], cols)
            self.assertEqual(prefs.load()["level"], "고등학교")
            self.assertIn("밝게", prefs.load_taste())
            prefs.clear_palette()
            self.assertEqual(prefs.load_palette(), {})
            self.assertIn("밝게", prefs.load_taste())
            with self.assertRaises(ValueError):
                prefs.save_palette({"colors": {"primary": "red"}})


class DesignIntegrationTests(unittest.TestCase):
    def test_default_output_unchanged(self):
        t = design.generate("과학", 5, "긴장감", "class")
        self.assertNotIn("userPalette", t)
        self.assertEqual(t["colors"], {k: design.load()["palettes"][t["palette"]][k] for k in t["colors"]})
        self.assertEqual(t, design.generate("과학", 5, "긴장감", "class", palette_from=None))

    def test_palette_from_file_and_dict(self):
        with tempfile.TemporaryDirectory() as td:
            pal = cf.extract(make_office(Path(td) / "d.pptx", "ppt"))
            f = Path(td) / "pal.json"
            f.write_text(json.dumps(pal, ensure_ascii=False), encoding="utf-8")
            base = design.generate("과학", 5, "긴장감", "class")
            t = design.generate("과학", 5, "긴장감", "class", palette_from=str(f))
            self.assertEqual(t["palette"], "user")
            self.assertTrue(t["userPalette"])
            self.assertEqual(t["colors"], pal["colors"])
            self.assertEqual(t["type"], base["type"])  # sizes, motion, fonts untouched
            self.assertEqual((t["motion"], t["fonts"]), (base["motion"], base["fonts"]))
            self.assertEqual(design.validate_tokens(t), [])
            t2 = design.generate("", 5, "", "present", palette_from={"colors": {"primary": "#2e7d32"}})
            self.assertEqual(design.validate_tokens(t2), [])
            self.assertEqual(t2["colors"]["primary"] == "#2e7d32" or ok.contrast(t2["colors"]["primary"], t2["colors"]["bg1"]) >= 3, True)

    def test_palette_from_errors(self):
        with self.assertRaises(ValueError):
            design.generate(palette_from="no-such-file.json")
        with self.assertRaises(ValueError):
            design.generate(palette_from={"colors": {"text": "#000000"}})


if __name__ == "__main__":
    unittest.main()
