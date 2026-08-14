#!/usr/bin/env python3
"""Capture screenshots and diagnostic layout geometry from a running web app.

Usage:
    python capture_web.py URL --out DIR [--viewports 390x844,1440x900] [--dpr 2]
                          [--full-page] [--wait-for SELECTOR] [--settle 400]
                          [--wait-until domcontentloaded|load|networkidle|commit]
                          [--probe "SEL_A,SEL_B"] [--json metrics/layout.json]
                          [--state "hover:.btn,focus:.input"] [--dark]

Capabilities:
1. Screenshots at one or more viewports.
2. A DOM geometry probe returning box rectangles, padding asymmetry, centring,
   overflow/clipping flags, a 44px hit-target guideline, and a diagnostic contrast
   estimate against the first simple non-transparent ancestor background colour.

The probe supplements visual inspection. It does not fully composite gradients,
images, shadows, filters or translucent ancestor stacks, so its contrast value is an
estimate rather than rendered-pixel ground truth.

Setup:
    pip install playwright
    playwright install chromium
"""
from __future__ import annotations

import argparse
import json
import os
import sys

PROBE_JS = r"""
(selectors) => {
  const lum = (r,g,b) => {
    const f = v => { v/=255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
    return 0.2126*f(r) + 0.7152*f(g) + 0.0722*f(b);
  };
  const parse = c => {
    const m = (c||'').match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(s => parseFloat(s.trim()));
    return { r:p[0], g:p[1], b:p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const resolvedBg = el => {
    let node = el;
    while (node && node !== document.documentElement) {
      const c = parse(getComputedStyle(node).backgroundColor);
      if (c && c.a > 0.05) return c;
      node = node.parentElement;
    }
    const c = parse(getComputedStyle(document.body).backgroundColor);
    return c && c.a > 0.05 ? c : { r:255, g:255, b:255, a:1 };
  };
  const ratio = (a,b) => {
    const l1 = lum(a.r,a.g,a.b), l2 = lum(b.r,b.g,b.b);
    const hi = Math.max(l1,l2), lo = Math.min(l1,l2);
    return +(((hi+0.05)/(lo+0.05)).toFixed(2));
  };
  const px = v => +(parseFloat(v)||0).toFixed(2);

  return selectors.map(sel => {
    const el = document.querySelector(sel);
    if (!el) return { selector: sel, found: false };
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const parent = el.parentElement;
    const pr = parent ? parent.getBoundingClientRect() : null;

    const padL = px(cs.paddingLeft), padR = px(cs.paddingRight);
    const padT = px(cs.paddingTop),  padB = px(cs.paddingBottom);
    const fg = parse(cs.color) || {r:0,g:0,b:0,a:1};
    const bg = resolvedBg(el);
    const contrastEstimate = ratio(fg, bg);

    let centring = null;
    if (pr) {
      const elMid = r.left + r.width/2, parentMid = pr.left + pr.width/2;
      const elMidY = r.top + r.height/2, parentMidY = pr.top + pr.height/2;
      centring = {
        horizontal_offset_from_parent_centre_px: +(elMid - parentMid).toFixed(2),
        vertical_offset_from_parent_centre_px: +(elMidY - parentMidY).toFixed(2),
        space_left_px: +(r.left - pr.left).toFixed(2),
        space_right_px: +(pr.right - r.right).toFixed(2),
        space_top_px: +(r.top - pr.top).toFixed(2),
        space_bottom_px: +(pr.bottom - r.bottom).toFixed(2)
      };
    }

    return {
      selector: sel,
      found: true,
      tag: el.tagName.toLowerCase(),
      text: (el.textContent||'').trim().slice(0,60),
      box: { x:+r.x.toFixed(2), y:+r.y.toFixed(2), w:+r.width.toFixed(2), h:+r.height.toFixed(2) },
      visible: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity > 0.01,
      padding: { left:padL, right:padR, top:padT, bottom:padB,
                 horizontal_asymmetry_px:+(padL-padR).toFixed(2),
                 vertical_asymmetry_px:+(padT-padB).toFixed(2) },
      margin: { left:px(cs.marginLeft), right:px(cs.marginRight),
                top:px(cs.marginTop), bottom:px(cs.marginBottom) },
      centring_in_parent: centring,
      font: { size_px: px(cs.fontSize), weight: cs.fontWeight, family: cs.fontFamily.split(',')[0].replace(/["']/g,'') },
      colour: { foreground: cs.color,
                resolved_background_estimate: `rgb(${bg.r}, ${bg.g}, ${bg.b})`,
                contrast_ratio_estimate: contrastEstimate,
                wcag_aa_normal_text_estimate: contrastEstimate >= 4.5,
                caveat: "Estimate from computed foreground and first simple non-transparent ancestor background; confirm complex compositing visually or with a dedicated accessibility tool." },
      overflow: { scroll_w: el.scrollWidth, client_w: el.clientWidth,
                  scroll_h: el.scrollHeight, client_h: el.clientHeight,
                  horizontally_overflowing: el.scrollWidth > el.clientWidth + 1,
                  vertically_overflowing: el.scrollHeight > el.clientHeight + 1,
                  text_truncated: el.scrollWidth > el.clientWidth + 1 && cs.overflow !== 'visible' },
      hit_target_44px_guideline: r.width >= 44 && r.height >= 44,
      offscreen: r.right < 0 || r.bottom < 0 || r.left > innerWidth || r.top > innerHeight,
      clipped_by_viewport: r.left < 0 || r.top < 0 || r.right > innerWidth || r.bottom > innerHeight
    };
  });
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Web capture + diagnostic layout probe")
    ap.add_argument("url")
    ap.add_argument("--out", default=".visual/capture")
    ap.add_argument("--viewports", default="390x844,1440x900")
    ap.add_argument("--dpr", type=float, default=2.0)
    ap.add_argument("--full-page", action="store_true")
    ap.add_argument("--wait-for", help="CSS selector to await before capturing")
    ap.add_argument("--settle", type=int, default=400, help="extra ms to let animations finish")
    ap.add_argument(
        "--wait-until",
        default="domcontentloaded",
        choices=["domcontentloaded", "load", "networkidle", "commit"],
        help="navigation readiness event; networkidle is optional for apps that truly settle",
    )
    ap.add_argument("--probe", help="comma-separated selectors to measure")
    ap.add_argument("--state", help="e.g. 'hover:.btn,focus:input' — each state starts from a fresh page")
    ap.add_argument("--dark", action="store_true", help="emulate prefers-color-scheme: dark")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright not installed. Run:\n  pip install playwright\n  playwright install chromium")

    os.makedirs(args.out, exist_ok=True)
    viewports = []
    for spec in args.viewports.split(","):
        w, h = spec.lower().split("x")
        viewports.append((int(w), int(h)))
    selectors = [s.strip() for s in args.probe.split(",")] if args.probe else []

    report = {
        "url": args.url,
        "device_scale_factor": args.dpr,
        "wait_until": args.wait_until,
        "interaction_states_isolated": True,
        "captures": [],
    }

    def ready(page) -> None:
        page.goto(args.url, wait_until=args.wait_until)
        if args.wait_for:
            page.wait_for_selector(args.wait_for, timeout=15000)
        page.wait_for_timeout(args.settle)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except PlaywrightError as exc:
            sys.exit(
                "Playwright is installed but Chromium could not launch. Run:\n"
                "  playwright install chromium\n\n"
                f"Playwright error: {exc}"
            )

        for w, h in viewports:
            ctx = browser.new_context(
                viewport={"width": w, "height": h},
                device_scale_factor=args.dpr,
                color_scheme="dark" if args.dark else "light",
            )
            page = ctx.new_page()
            errors: list[str] = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))

            ready(page)
            shot = os.path.join(args.out, f"{w}x{h}.png")
            page.screenshot(path=shot, full_page=args.full_page)

            entry = {
                "viewport": f"{w}x{h}",
                "screenshot": shot,
                "page_title": page.title(),
                "document_height": page.evaluate("document.documentElement.scrollHeight"),
                "horizontal_scroll_present": page.evaluate(
                    "document.documentElement.scrollWidth > window.innerWidth + 1"
                ),
                "console_errors": errors[:10],
            }
            if selectors:
                entry["elements"] = page.evaluate(PROBE_JS, selectors)
                missing = [e["selector"] for e in entry["elements"] if not e["found"]]
                if missing:
                    entry["selectors_not_found"] = missing

            # Each interaction state gets a fresh page so hover/focus/active state cannot
            # leak into the next capture.
            for spec in (args.state.split(",") if args.state else []):
                state, sel = spec.split(":", 1)
                state = state.strip()
                sel = sel.strip()
                state_page = ctx.new_page()
                try:
                    ready(state_page)
                    el = state_page.locator(sel).first
                    if state == "hover":
                        el.hover()
                    elif state == "focus":
                        el.focus()
                    elif state == "active":
                        box = el.bounding_box()
                        if not box:
                            raise RuntimeError("target has no visible bounding box")
                        state_page.mouse.move(box["x"] + 2, box["y"] + 2)
                        state_page.mouse.down()
                    else:
                        raise ValueError(f"unsupported state '{state}'")
                    state_page.wait_for_timeout(250)
                    state_shot = os.path.join(args.out, f"{w}x{h}_{state}.png")
                    state_page.screenshot(path=state_shot, full_page=args.full_page)
                    entry.setdefault("state_captures", []).append(
                        {"state": state, "selector": sel, "screenshot": state_shot}
                    )
                    if state == "active":
                        state_page.mouse.up()
                except Exception as exc:  # state capture is best-effort
                    entry.setdefault("state_capture_errors", []).append(f"{spec}: {exc}")
                finally:
                    state_page.close()

            report["captures"].append(entry)
            ctx.close()
        browser.close()

    if args.json_out:
        os.makedirs(os.path.dirname(args.json_out) or ".", exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
