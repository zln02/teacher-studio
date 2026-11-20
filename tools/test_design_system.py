# SPDX-License-Identifier: Apache-2.0
"""Unit tests: the shared design system (shared/design/system.py, styles.py, palettes.json), the 「밤티 검사」 (ai_look.py) and the
content-driven layout choosers. No network, no browser.

    python3 tools/test_design_system.py
"""
import itertools
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "shared" / "design", ROOT / "shared" / "fonts", ROOT / "shared" / "shell", ROOT / "skills" / "teacher-game" / "scripts",
          ROOT / "skills" / "teacher-studio" / "scripts"):
    sys.path.insert(0, str(p))
import ai_look  # noqa: E402
import color_check  # noqa: E402
import design  # noqa: E402
import oklch  # noqa: E402
import styles  # noqa: E402
import system as ds  # noqa: E402


class Type(unittest.TestCase):
    def test_scale_is_monotonic_and_has_a_floor(self):
        for canvas, sc in ds.SCALE.items():
            vals = [sc[k] for k in ("caption", "label", "body", "lead", "h2", "h1", "display")]
            self.assertEqual(vals, sorted(vals), canvas)
            self.assertGreaterEqual(sc["caption"], ds.FLOOR[canvas])

    def test_optical_compensation(self):
        self.assertLess(ds.tracking(132), ds.tracking(60))   # bigger = tighter
        self.assertLess(ds.tracking(60), ds.tracking(28))
        self.assertEqual(ds.tracking(18), 0.0)
        self.assertLess(ds.leading(132), ds.leading(36))     # bigger = closer lines
        self.assertLess(ds.weight(132), ds.weight(36))       # bigger = lighter
        self.assertLessEqual(max(ds.weight(s) for s in (24, 36, 56, 96, 132)), ds.MAX_WEIGHT)

    def test_type_css_carries_the_detailing(self):
        css = ds.type_css()
        for needle in ("font-synthesis:none", "word-break:keep-all", "line-break:strict", "text-spacing-trim", "tabular-nums", "text-wrap:balance"):
            self.assertIn(needle, css)

    def test_studio_face_is_embedded_and_renamed(self):
        import embed
        self.assertTrue(embed.BASE["TS Sans"].exists())
        self.assertEqual(embed.families_used('<p style="font-family:\'TS Sans\'">가</p>'), ["TS Sans"])
        self.assertEqual(embed.families_used("<p>가</p>"), ["Noto Sans KR"])
        lic = (ROOT / "shared" / "fonts" / "OFL-Pretendard.txt").read_text(encoding="utf-8")
        self.assertIn("Reserved Font Name Pretendard", lic)
        self.assertIn("SIL OPEN FONT LICENSE", lic)
        self.assertNotIn('font-family:"Pretendard"', embed.font_face_css("TS Sans", b"x"))  # the reserved name is never the @font-face name


class SpaceGridMotion(unittest.TestCase):
    def test_spacing_is_the_8pt_rhythm(self):
        self.assertTrue(all(v % 4 == 0 for v in ds.SPACE))
        self.assertEqual(list(ds.SPACE), sorted(ds.SPACE))

    def test_every_style_names_a_grid_and_at_most_two_ornaments(self):
        for sid, st in styles.STYLES.items():
            self.assertIn(st["grid"], ds.GRIDS, sid)
            self.assertLessEqual(len(st["orn"]), 2, sid)
            for o in st["orn"]:
                self.assertIn(o, ds.ORNAMENTS, sid)
            self.assertLessEqual(st["type"]["w"], ds.MAX_WEIGHT, sid)

    def test_styles_differ_in_structure_not_only_colour(self):
        def sig(st):
            return (st["grid"], (st["type"]["w"], st["type"]["label"]), st["rad"], tuple(sorted(st["orn"])), st["bg"])
        for (a, sa), (b, sb) in itertools.combinations(styles.STYLES.items(), 2):
            diff = sum(1 for x, y in zip(sig(sa), sig(sb)) if x != y)
            self.assertGreaterEqual(diff, 3, f"{a} vs {b}: only {diff} of 5 structural traits differ")

    def test_motion_tokens(self):
        d = ds.MOTION["dur"]
        self.assertEqual(sorted(d.values()), [d[k] for k in ("instant", "fast", "base", "slow", "scene")])
        self.assertIn("--ds-t-base:240ms", ds.css_vars("stage"))


class Colour(unittest.TestCase):
    def all_palettes(self):
        out = {f"style:{k}": v["pal"] for k, v in styles.STYLES.items()}
        out.update({f"palette:{k}": v for k, v in design.load()["palettes"].items()})
        return out

    def test_contrast(self):
        for name, p in self.all_palettes().items():
            self.assertEqual(design.palette_issues(name, p), [], name)

    def test_no_fluorescent_colour(self):
        for name, p in self.all_palettes().items():
            for k in ("primary", "accent", "cardBorder", "good", "bad"):
                self.assertFalse(ds.is_neon(p[k]), f"{name}.{k} = {p[k]}")
        self.assertTrue(ds.is_neon("#00e5ff"))
        self.assertTrue(ds.is_neon("#ff2bd6"))
        self.assertFalse(ds.is_neon("#8fc4d6"))   # the deck's mist blue
        self.assertFalse(ds.is_neon("#d9a85c"))   # the deck's brass

    def test_right_and_wrong_survive_colour_blind_simulation(self):
        for name, p in self.all_palettes().items():
            self.assertEqual(color_check.check_tokens({"colors": p}), [], name)

    def test_no_style_is_the_ai_house_look(self):
        for sid, st in styles.STYLES.items():
            self.assertFalse(ai_look.is_house(st["pal"]["bg1"], [st["pal"]["primary"]], st["font"]), sid)
            self.assertFalse(ai_look.is_cream(st["pal"]["bg1"]), sid)

    def test_ramp_and_palette_builder(self):
        r = ds.ramp("#2f5bea")
        ls = [oklch.hex_to_oklch(r[k])[0] for k in ds.RAMP_STEPS]
        self.assertEqual(ls, sorted(ls, reverse=True))
        self.assertEqual(len(r), 11)
        p = ds.palette("dark", 250, (0.8, 0.07, 215), (0.77, 0.1, 75))
        self.assertEqual(design.palette_issues("built", p), [])
        g = oklch.hex_to_oklch(ds.neutral_ramp(250)[500])
        self.assertGreater(g[1], 0.003)   # greys are tinted, never pure grey

    def test_tokens_carry_the_system(self):
        t = design.generate("과학", 5, "긴장감", "class")
        self.assertEqual(t["fonts"]["display"], "TS Sans")
        self.assertEqual(t["system"]["maxWeight"], 800)
        self.assertEqual(design.validate_tokens(t), [])


NEON_PAGE = """<html><head><style>:root{--bg:#05070f;--primary:#00e5ff;--accent:#ff2bd6}
body{background:#05070f;font-family:'Black Han Sans','Jua','Do Hyeon','Gaegu',sans-serif;line-height:1.1}
h1{font-weight:900;-webkit-text-stroke:3px #00e5ff;text-shadow:0 0 22px #ff2bd6,0 0 56px #00e5ff}
.card{font-weight:900;box-shadow:0 0 26px var(--accent);padding:7px 13px;margin:5px;gap:9px}
.btn{font-weight:900;box-shadow:0 0 30px #00e5ff;padding:11px 19px;margin:3px 7px}
.a{background:linear-gradient(90deg,#ff2bd6,#00e5ff)}.b{background:linear-gradient(#39ff9c,#ff2bd6)}
.c{padding:5px 9px 13px 15px;margin:7px;gap:11px}.d{padding:6px 10px;margin:14px 18px;gap:22px}</style></head><body><h1>🚀✨🎉🔥 퀴즈</h1></body></html>"""
CLEAN_PAGE = """<html><head><style>/* design system polish (web) */:root{--bg:#f4f6f8;--primary:#1a2026;--accent:#a38043}
body{background:#f4f6f8;font-family:'TS Sans','Noto Sans KR',sans-serif;line-height:1.55}
h1{font-weight:700;letter-spacing:-.04em}.card{padding:16px 24px;margin:0 0 24px;gap:8px;box-shadow:0 18px 40px -22px rgba(0,0,0,.55)}</style></head>
<body><h1>빛의 반사</h1></body></html>"""


class Bamti(unittest.TestCase):
    def test_neon_page_fails_every_criterion(self):
        codes = {c for c, _ in ai_look.bamti(NEON_PAGE)}
        for c in ("glow", "hollow", "gradient", "neon", "emoji", "weight", "grid", "fonts"):
            self.assertIn(c, codes)
        g = ai_look.pro_gate(NEON_PAGE)
        self.assertEqual((g["pass"], g["of"]), (0, 5))
        self.assertTrue(all(lv == "WARN" for lv, _ in ai_look.bamti_results(NEON_PAGE)))   # WARN by default, never FAIL

    def test_clean_page_passes(self):
        self.assertEqual(ai_look.bamti(CLEAN_PAGE), [])
        self.assertEqual(ai_look.pro_gate(CLEAN_PAGE)["pass"], 5)
        self.assertEqual(ai_look.bamti_results(CLEAN_PAGE)[0][0], "PASS")

    def test_user_design_is_never_judged(self):
        own = NEON_PAGE.replace("<body>", '<body data-user-design="1">')
        self.assertEqual(ai_look.bamti(own), [])
        self.assertEqual(ai_look.bamti_results(own), [])
        self.assertEqual(ai_look.bamti(NEON_PAGE.replace("<body>", '<body><script>var T={"userPalette": true}</script>')), [])

    def test_neutral_shadow_is_not_a_glow(self):
        self.assertEqual(ai_look.count_glow(".a{box-shadow:0 0 24px rgba(0,0,0,.4)}.b{box-shadow:0 0 0 4px #ff2bd6}.c{box-shadow:0 18px 40px -22px rgba(0,0,0,.5)}"), 0)
        self.assertEqual(ai_look.count_glow(".a{text-shadow:0 0 22px #ff2bd6,0 0 56px #00e5ff}.b{filter:drop-shadow(0 0 8px #0ff)}"), 3)

    def test_rules_before_the_polish_layer_do_not_count(self):
        page = "<style>.old{box-shadow:0 0 30px #00e5ff;text-shadow:0 0 30px #00e5ff;filter:none}.o2{box-shadow:0 0 30px #ff2bd6}" + ds.polish_css("game") + ".x{padding:8px}</style>"
        self.assertNotIn("glow", {c for c, _ in ai_look.bamti(page)})

    def test_polish_layers_and_shell_kit_are_clean(self):
        import shell
        for target in ("game", "deck", "shell", "web", "print"):
            css = ds.polish_css(target)
            self.assertEqual(ai_look.count_glow(css), 0, target)
            self.assertEqual(ai_look.count_hollow(css), 0, target)
        self.assertEqual(ai_look.count_glow(shell.css()), 0)
        for sid in styles.STYLES:
            self.assertEqual(ai_look.count_gradient_soup("x{background:%s}" % shell.pattern(shell.tokens(sid))), 0, sid)


class Variety(unittest.TestCase):
    def test_game_layout_follows_the_content(self):
        import layout_auto as L
        short = {"items": [{"q": "빛의 속력은?", "choices": ["가", "나", "다", "라"]}] * 4}
        long_ = {"items": [{"q": "빛의 속력은?", "choices": ["아주 아주 긴 보기 문장이에요 정말로", "나", "다", "라"]}] * 4}
        ox = {"items": [{"q": "빛은 직진한다."}] * 4}
        w = styles.STYLES["pastel-cute"]["layout"]
        self.assertGreater(L.layout_weights(w, L.content_features(short)).get("bento", 0), 0)
        self.assertEqual({k for k in L.layout_weights(w, L.content_features(long_))} & {"bento", "news", "poster"}, set())
        wox = L.layout_weights(w, L.content_features(ox))
        self.assertGreater(wox["poster"], L.layout_weights(w, L.content_features(short))["poster"])

    def test_same_game_request_other_seed_other_skeleton(self):
        import layout_auto as L
        spec = {"mechanic": "quiz", "title": "태양계 퀴즈", "items": [{"q": "가장 큰 행성은?", "choices": ["목성", "토성", "지구", "화성"]}] * 6, "design": {}}
        seen = set()
        for sd in range(12):
            spec["design"]["seed"] = sd
            seen.add(L.compose(spec, None, "space", "minimal-premium")["layout"])
        self.assertGreaterEqual(len(seen), 3, seen)

    def test_webapp_layout_follows_content_and_seed(self):
        import build_webapp as W
        one = {"title": "속력 실험실", "about": "속력 x 시간", "parts": [{"type": "custom", "html": "<p>x</p>"}]}
        three = {"title": "단위", "parts": [{"type": "custom", "html": "<p>x</p>"}, {"type": "custom", "html": "<p>y</p>"}, {"type": "helper", "intents": [{"keys": ["a"], "answer": "b"}]}]}
        lays, heads = set(), set()
        for sd in range(1, 25):
            lay, head = W.pick_layout({**one, "seed": sd})
            self.assertIn(lay, W.LAYOUTS[1])
            lays.add(lay)
            heads.add(head)
            self.assertIn(W.pick_layout({**three, "seed": sd})[0], W.LAYOUTS[3])
        self.assertGreaterEqual(len(lays), 2)
        self.assertGreaterEqual(len(heads), 2)
        self.assertEqual(W.pick_layout({**one, "layout": "focus", "head": "hero"}), ("focus", "hero"))   # the spec can name it
        self.assertEqual(W.pick_layout(one), W.pick_layout(dict(one)))                                    # same request -> same page


class Rules(unittest.TestCase):
    def test_rules_file_is_linked_from_every_weapon(self):
        rules = (ROOT / "shared" / "design" / "DESIGN-RULES.md").read_text(encoding="utf-8")
        for needle in ("TS Sans", "8pt", "밤티", "5/5", "tabular", "user's design wins"):
            self.assertIn(needle, rules)
        for sk in ("teacher-game", "teacher-slides", "teacher-studio", "teacher-docs", "teacher-class-tools", "teacher-data", "teacher-motion"):
            self.assertIn("DESIGN-RULES.md", (ROOT / "skills" / sk / "SKILL.md").read_text(encoding="utf-8"), sk)
        for sid, st in styles.STYLES.items():
            self.assertIn(st["name"], rules, sid)

    def test_palettes_json_is_valid_json_with_the_studio_face(self):
        d = json.loads((ROOT / "shared" / "design" / "palettes.json").read_text(encoding="utf-8"))
        self.assertTrue(all(p["display"] in ("TS Sans", "Noto Serif KR") for p in d["fonts"]["pairs"]))


if __name__ == "__main__":
    unittest.main()
