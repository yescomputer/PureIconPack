#!/usr/bin/env python3
"""
Single-source icon mapping validator, dead-link cleaner, activity auto-healer,
and offline search-alias generator for Pure Icon Pack.

Absorbs engineering practices from:
- Arcticons (appfilter_auto_updater.py & Checks.java)
- Delta Icon Pack (process_icons.py conflict/dangling checks)
- Lawnicons (GetIconInfo component-label indexing)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
APP_MAIN = ROOT / "app" / "src" / "main"
RES_DIR = APP_MAIN / "res"
ASSETS_DIR = APP_MAIN / "assets"

COMP_RE = re.compile(r"^ComponentInfo\{([^/{}]+)/([^/{}]+)\}$")
COMMENT_RE = re.compile(r"<!--\s*(.*?)\s*-->")
ITEM_TAG_RE = re.compile(
    r'<(item|calendar)\b([^>]*?)/?>'
)
ATTR_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')

# Packages that legitimately expose multiple distinct launcher icons (never auto-merge activities)
MULTI_ICON_PACKAGE_BLACKLIST = {
    "com.android.settings",
    "com.google.android.gms",
    "com.google.android.googlequicksearchbox",
    "com.huawei.hwid",
    "com.miui.securitycenter",
    "com.coloros.shortcuts",
    "com.samsung.android.app.routines",
    "io.makeroid.companion",
}

# Activity class substrings that usually represent secondary/helper entrypoints rather than main launcher icon
SECONDARY_ACTIVITY_SUBSTRINGS = (
    "widget",
    "shortcut",
    "picker",
    "preference",
    "settingsactivity",
    "shareactivity",
    "deeplink",
    "qrcode",
    "scanactivity",
    "payactivity",
    "wxentry",
    "debug",
)

UPSTREAM_APPFILTERS = [
    ("Lawnicons", "https://raw.githubusercontent.com/LawnchairLauncher/lawnicons/develop/app/assets/appfilter.xml"),
    ("Arcticons", "https://raw.githubusercontent.com/Arcticons-Team/Arcticons/main/app/src/main/assets/appfilter.xml"),
    ("Delta", "https://raw.githubusercontent.com/Delta-Icons/android/master/app/src/main/assets/appfilter.xml"),
]


def collect_valid_drawables() -> set[str]:
    valid: set[str] = set()
    for folder in RES_DIR.iterdir():
        if not folder.is_dir():
            continue
        base = folder.name.split("-")[0]
        if base in ("drawable", "mipmap"):
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() in (".png", ".webp", ".xml"):
                    valid.add(f.stem)
    return valid


def normalize_component(raw_comp: str) -> tuple[str, str, str] | None:
    m = COMP_RE.match(raw_comp.strip())
    if not m:
        return None
    pkg, cls = m.group(1).strip(), m.group(2).strip()
    if not pkg or not cls:
        return None
    if cls.startswith("."):
        cls = pkg + cls
    return pkg, cls, f"ComponentInfo{{{pkg}/{cls}}}"


def parse_appfilter_with_comments(path: Path):
    """
    Preserves header directives (<iconback>, <iconmask>, <iconupon>, <scale>, <calendar>)
    and extracts (component, drawable, comment_label) records.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    header_directives: list[str] = []
    calendar_entries: list[tuple[str, str]] = []
    items: list[tuple[str, str, str]] = []  # (norm_comp, drawable, label_comment)

    last_comment = ""
    text = "\n".join(lines)

    # Extract header directives exactly
    root = ET.fromstring(text)
    for el in root:
        if el.tag in ("iconback", "iconmask", "iconupon", "scale"):
            attrs = " ".join(f'{k}="{escape(v)}"' for k, v in el.attrib.items())
            header_directives.append(f"    <{el.tag} {attrs} />")
        elif el.tag == "calendar":
            comp = el.attrib.get("component", "").strip()
            prefix = el.attrib.get("prefix", "").strip()
            if comp and prefix:
                calendar_entries.append((comp, prefix))

    # Line-by-line pass to pair <!-- App Name --> comments with following <item> rows
    for raw_line in lines:
        stripped = raw_line.strip()
        cm = COMMENT_RE.search(stripped)
        if cm:
            comment_body = cm.group(1).strip()
            if (
                comment_body
                and not comment_body.lower().startswith(
                    ("for nova", "just for", "dynamic", "img2=", "merged non-conflicting")
                )
                and "==" not in comment_body
            ):
                last_comment = comment_body
            else:
                last_comment = ""
            continue

        if stripped.startswith("<item ") and 'component="' in stripped and 'drawable="' in stripped:
            attrs = dict(ATTR_RE.findall(stripped))
            comp_raw = attrs.get("component", "")
            drawable = attrs.get("drawable", "").strip()
            norm = normalize_component(comp_raw)
            if norm and drawable:
                items.append((norm[2], drawable, last_comment))
        elif not stripped:
            last_comment = ""

    return header_directives, calendar_entries, items


def query_adb_launcher_components(adb_path: str) -> list[tuple[str, str]]:
    """Returns [(pkg, full_cls)] for connected ADB device(s), if any."""
    try:
        devs = subprocess.check_output([adb_path, "devices"], text=True, timeout=5)
        online = [
            ln.split()[0]
            for ln in devs.splitlines()[1:]
            if ln.strip() and "\tdevice" in ln
        ]
        if not online:
            return []
        serial = online[0]
        out = subprocess.check_output(
            [
                adb_path,
                "-s",
                serial,
                "shell",
                "cmd",
                "package",
                "query-activities",
                "--brief",
                "-a",
                "android.intent.action.MAIN",
                "-c",
                "android.intent.category.LAUNCHER",
            ],
            text=True,
            timeout=10,
        )
        results: list[tuple[str, str]] = []
        for ln in out.splitlines():
            s = ln.strip()
            if "/" in s and not s.startswith(("Activity", "priority")):
                pkg, cls = s.split("/", 1)
                pkg, cls = pkg.strip(), cls.strip()
                if cls.startswith("."):
                    cls = pkg + cls
                if re.match(r"^[a-zA-Z0-9_.$]+$", pkg) and re.match(r"^[a-zA-Z0-9_.$]+$", cls):
                    results.append((pkg, cls))
        return results
    except Exception as e:
        print(f"[warn] ADB query skipped: {e}")
        return []


def fetch_upstream_components_and_labels() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """
    Returns:
      pkg_to_components: {pkg: {ComponentInfo{pkg/cls}, ...}}
      pkg_to_labels: {pkg: {"App Name", ...}}
    """
    pkg_to_components: dict[str, set[str]] = defaultdict(set)
    pkg_to_labels: dict[str, set[str]] = defaultdict(set)

    for source_name, url in UPSTREAM_APPFILTERS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            xml_text = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="replace")
            last_comment = ""
            count = 0
            for raw_line in xml_text.splitlines():
                s = raw_line.strip()
                cm = COMMENT_RE.search(s)
                if cm:
                    c = cm.group(1).strip()
                    if c and len(c) <= 60 and not c.startswith("<"):
                        last_comment = c
                    continue
                if s.startswith("<item ") and 'component="ComponentInfo{' in s:
                    attrs = dict(ATTR_RE.findall(s))
                    norm = normalize_component(attrs.get("component", ""))
                    if not norm:
                        continue
                    pkg, cls, full_comp = norm
                    cls_lower = cls.lower()
                    if any(bad in cls_lower for bad in SECONDARY_ACTIVITY_SUBSTRINGS):
                        continue
                    pkg_to_components[pkg].add(full_comp)
                    name_attr = attrs.get("name", "").strip()
                    if name_attr:
                        pkg_to_labels[pkg].add(name_attr)
                    elif last_comment:
                        pkg_to_labels[pkg].add(last_comment)
                    count += 1
                elif not s:
                    last_comment = ""
            print(f"[upstream] Loaded {count} entries from {source_name}")
        except Exception as e:
            print(f"[warn] Could not fetch {source_name}: {e}")

    return pkg_to_components, pkg_to_labels


def clean_comment_labels(raw: str) -> list[str]:
    if not raw:
        return []
    parts = [p.strip() for p in re.split(r"[/|·]+", raw) if p.strip()]
    seen: list[str] = []
    for p in parts:
        if p not in seen and len(p) <= 50:
            seen.append(p)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sync-adb", action="store_true", help="Heal changed launcher activities from connected ADB device")
    ap.add_argument("--sync-upstream", action="store_true", help="Heal changed launcher activities from Lawnicons/Arcticons/Delta")
    ap.add_argument("--check", action="store_true", help="Validate only; exit non-zero if out of sync or invalid")
    args = ap.parse_args()

    valid_drawables = collect_valid_drawables()
    src_appfilter = ASSETS_DIR / "appfilter.xml"
    header_directives, calendar_entries, raw_items = parse_appfilter_with_comments(src_appfilter)

    seen_components: set[str] = set()
    cleaned_items: list[tuple[str, str, str]] = []
    removed_dangling = 0
    removed_duplicates = 0

    pkg_drawables: dict[str, set[str]] = defaultdict(set)
    drawable_labels: dict[str, list[str]] = defaultdict(list)
    drawable_packages: dict[str, set[str]] = defaultdict(set)

    # Validate calendar entries too
    valid_calendars: list[tuple[str, str]] = []
    seen_cal: set[str] = set()
    for comp, prefix in calendar_entries:
        norm = normalize_component(comp)
        comp_str = norm[2] if norm else comp
        if comp_str not in seen_cal:
            seen_cal.add(comp_str)
            valid_calendars.append((comp_str, prefix))

    for comp, drawable, comment_label in raw_items:
        if drawable not in valid_drawables:
            removed_dangling += 1
            continue
        if comp in seen_components:
            removed_duplicates += 1
            continue
        seen_components.add(comp)
        cleaned_items.append((comp, drawable, comment_label))
        pkg = comp[len("ComponentInfo{") :].split("/", 1)[0]
        pkg_drawables[pkg].add(drawable)
        drawable_packages[drawable].add(pkg)
        for lbl in clean_comment_labels(comment_label):
            if lbl not in drawable_labels[drawable]:
                drawable_labels[drawable].append(lbl)

    # Identify unambiguous 1-package-to-1-drawable mappings eligible for activity healing
    unambiguous_pkg_to_drawable: dict[str, str] = {
        pkg: next(iter(drs))
        for pkg, drs in pkg_drawables.items()
        if len(drs) == 1 and pkg not in MULTI_ICON_PACKAGE_BLACKLIST
    }

    healed_adb = 0
    healed_upstream = 0

    if args.sync_adb:
        sdk = os.environ.get("ANDROID_HOME") or os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk")
        adb_exe = str(Path(sdk) / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb"))
        for pkg, cls in query_adb_launcher_components(adb_exe):
            if pkg in unambiguous_pkg_to_drawable:
                comp = f"ComponentInfo{{{pkg}/{cls}}}"
                if comp not in seen_components and comp not in seen_cal:
                    dr = unambiguous_pkg_to_drawable[pkg]
                    cleaned_items.append((comp, dr, ""))
                    seen_components.add(comp)
                    healed_adb += 1

    if args.sync_upstream:
        up_comps, up_labels = fetch_upstream_components_and_labels()
        for pkg, dr in unambiguous_pkg_to_drawable.items():
            for lbl in sorted(up_labels.get(pkg, ())):
                if lbl not in drawable_labels[dr]:
                    drawable_labels[dr].append(lbl)
            existing_for_pkg = sum(1 for c, _, _ in cleaned_items if c.startswith(f"ComponentInfo{{{pkg}/"))
            # Cap auto-added aliases per package to keep appfilter lean
            for comp in sorted(up_comps.get(pkg, ())):
                if existing_for_pkg >= 6:
                    break
                if comp not in seen_components and comp not in seen_cal:
                    cleaned_items.append((comp, dr, ""))
                    seen_components.add(comp)
                    existing_for_pkg += 1
                    healed_upstream += 1

    # Deterministic sort by package/component while preserving comment labels
    cleaned_items.sort(key=lambda x: x[0].lower())

    print(
        f"Summary: valid_drawables={len(valid_drawables)}, "
        f"final_components={len(cleaned_items)}, "
        f"removed_dangling={removed_dangling}, "
        f"removed_duplicates={removed_duplicates}, "
        f"healed_adb={healed_adb}, "
        f"healed_upstream={healed_upstream}"
    )

    if args.check:
        if removed_dangling > 0 or removed_duplicates > 0:
            print("Check failed: dangling or duplicate entries found.", file=sys.stderr)
            return 1
        print("Check passed: 0 dangling drawables, 0 duplicate components.")
        return 0

    # 1. Write synchronized appfilter.xml (both assets/ and res/xml/)
    af_lines = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>"]
    af_lines.extend(header_directives)
    af_lines.append("")
    for comp, prefix in valid_calendars:
        af_lines.append(f'    <calendar component="{escape(comp)}" prefix="{escape(prefix)}" />')
    af_lines.append("")
    prev_emitted_comment = ""
    for comp, drawable, comment_label in cleaned_items:
        if comment_label:
            safe_comment = comment_label.replace("--", "-").strip()
            if safe_comment and safe_comment != prev_emitted_comment:
                af_lines.append(f"    <!-- {safe_comment} -->")
                prev_emitted_comment = safe_comment
        else:
            prev_emitted_comment = ""
        af_lines.append(f'    <item component="{escape(comp)}" drawable="{escape(drawable)}" />')
    af_lines.append("</resources>")
    af_content = "\n".join(af_lines) + "\n"

    (ASSETS_DIR / "appfilter.xml").write_text(af_content, encoding="utf-8")
    (RES_DIR / "xml" / "appfilter.xml").write_text(af_content, encoding="utf-8")

    # 2. Write synchronized res/xml/appmap.xml
    am_lines = ['<?xml version="1.0" encoding="utf-8"?>', "<appmap>"]
    seen_am: set[tuple[str, str]] = set()
    for comp, drawable, _ in cleaned_items:
        _, cls, _ = normalize_component(comp)  # type: ignore[misc]
        key = (cls, drawable)
        if key not in seen_am:
            seen_am.add(key)
            am_lines.append(f'    <item class="{escape(cls)}" name="{escape(drawable)}" />')
    am_lines.append("</appmap>")
    (RES_DIR / "xml" / "appmap.xml").write_text("\n".join(am_lines) + "\n", encoding="utf-8")

    # 3. Write synchronized res/xml/theme_resources.xml
    tr_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<Theme version="1">',
        '    <Label value="PureIconPack" />',
        '    <ThemePreview image="preview1" />',
        '    <ThemePreviewWork image="preview1" />',
        '    <ThemePreviewMenu image="preview1" />',
        '    <DockMenuAppIcon selector="drawer" />',
    ]
    for comp, drawable, _ in cleaned_items:
        inner = comp[len("ComponentInfo{") : -1]
        tr_lines.append(f'    <AppIcon image="{escape(drawable)}" name="{escape(inner)}" />')
    tr_lines.append("</Theme>")
    (RES_DIR / "xml" / "theme_resources.xml").write_text("\n".join(tr_lines) + "\n", encoding="utf-8")

    # 4. Validate & sync drawable.xml (assets/ and res/xml/) ensuring zero missing drawables
    #    and keeping <category title="All" /> sorted with every browsable icon included.
    dr_tree = ET.parse(ASSETS_DIR / "drawable.xml")
    dr_root = dr_tree.getroot()
    cats: list[tuple[str, list[str]]] = []
    cur_title = ""
    cur_items: list[str] = []
    all_browsable: set[str] = set()

    for el in dr_root:
        if el.tag == "category":
            if cur_title:
                cats.append((cur_title, cur_items))
            cur_title = el.attrib.get("title", "")
            cur_items = []
        elif el.tag == "item":
            dname = el.attrib.get("drawable", "").strip()
            if dname in valid_drawables and dname not in cur_items:
                cur_items.append(dname)
                all_browsable.add(dname)
    if cur_title:
        cats.append((cur_title, cur_items))

    dr_lines = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>", '    <version>1</version>']
    for title, c_items in cats:
        dr_lines.append(f'    <category title="{escape(title)}" />')
        items_out = sorted(all_browsable) if title == "All" else c_items
        for dname in items_out:
            dr_lines.append(f'    <item drawable="{escape(dname)}" />')
    dr_lines.append("</resources>")
    dr_content = "\n".join(dr_lines) + "\n"
    (ASSETS_DIR / "drawable.xml").write_text(dr_content, encoding="utf-8")
    (RES_DIR / "xml" / "drawable.xml").write_text(dr_content, encoding="utf-8")

    # 5. Generate offline multi-language search metadata res/xml/icon_metadata.xml
    meta_lines = ['<?xml version="1.0" encoding="utf-8"?>', "<icons>"]
    for dr in sorted(valid_drawables):
        labels = drawable_labels.get(dr, [])
        pkgs = sorted(drawable_packages.get(dr, ()))
        if not labels and not pkgs:
            continue
        primary = labels[0] if labels else ""
        # Compact keyword string: all distinct human labels + package identifiers
        kw_tokens: list[str] = []
        for lbl in labels[:5]:
            if lbl not in kw_tokens:
                kw_tokens.append(lbl)
        for pkg in pkgs[:6]:
            if pkg not in kw_tokens:
                kw_tokens.append(pkg)
        keywords = " | ".join(kw_tokens)
        meta_lines.append(
            f'    <icon drawable="{escape(dr)}" label="{escape(primary)}" keywords="{escape(keywords)}" />'
        )
    meta_lines.append("</icons>")
    (RES_DIR / "xml" / "icon_metadata.xml").write_text("\n".join(meta_lines) + "\n", encoding="utf-8")

    print(f"Generated icon_metadata.xml for {len(meta_lines) - 3} icons.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
