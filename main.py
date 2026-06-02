#!/usr/bin/env python3
"""HOI4 Fleet Composition Cheat Sheet Generator
Reads config/fleet.json and config/references.json, writes cheat_sheet.html.
"""

import json
from collections import defaultdict
from datetime import date

# ── I/O ───────────────────────────────────────────────────────────────────────

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ── math ──────────────────────────────────────────────────────────────────────

def tf_total(ships):
    return sum(ships.values())

def fleet_class_totals(task_forces):
    totals = defaultdict(int)
    for tf in task_forces:
        for cls, cnt in tf["ships"].items():
            totals[cls] += cnt
    return totals

def fleet_total(task_forces):
    return sum(tf_total(tf["ships"]) for tf in task_forces)

def grand_total(theaters):
    return sum(fleet_total(f["task_forces"]) for t in theaters for f in t["fleets"])

# ── helpers ───────────────────────────────────────────────────────────────────

def esc(s):
    return s.replace("&", "&amp;")

def short_role(role):
    return role.title().replace("Group", "Grp")

def pill(cls, cnt, css="ship-pill"):
    return f'<span class="{css}">{cls} ×{cnt}</span>'

# ── task-force / fleet rendering ──────────────────────────────────────────────

def render_tf_row(tf):
    pills = "".join(pill(c, n) for c, n in tf["ships"].items())
    return (
        f'<tr>'
        f'<td class="tf-name">{tf["id"]}<span class="tf-role">{short_role(tf["role"])}</span></td>'
        f'<td class="tf-comp">{pills}</td>'
        f'<td class="tf-total-cell">{tf_total(tf["ships"])}</td>'
        f'</tr>'
    )

def render_class_totals(task_forces, class_order):
    totals = fleet_class_totals(task_forces)
    pills = "".join(pill(c, totals[c], "ct-pill") for c in class_order if c in totals)
    return f'<div class="class-totals">{pills}</div>'

def render_fleet(fleet, theater_name, class_order):
    tfs   = fleet["task_forces"]
    total = fleet_total(tfs)
    parts = fleet["name"].split(" - ", 1)
    name  = parts[0]
    sub   = esc(parts[1]) if len(parts) > 1 else ""
    rows  = "\n            ".join(render_tf_row(tf) for tf in tfs)
    return f"""
    <div class="theater">
      <div class="theater-header">⚓ {esc(theater_name)}</div>
      <div class="theater-body">
        <div class="fleet">
          <div class="fleet-name">
            <span class="fleet-total">{total} ships</span>
            {name}
            <span class="fleet-sub">{sub}</span>
          </div>
          <table class="tf-table">
            {rows}
          </table>
          {render_class_totals(tfs, class_order)}
        </div>
      </div>
    </div>"""

def render_theaters_grid(theaters, class_order):
    columns = defaultdict(list)
    for theater in theaters:
        for fleet in theater["fleets"]:
            col = fleet.get("display_column", 1)
            columns[col].append((theater["name"], fleet))

    col_nums   = sorted(columns.keys())
    last_multi = len(columns[col_nums[-1]]) > 1
    widths     = " ".join(
        "0.72fr" if (i == len(col_nums) - 1 and last_multi) else "1fr"
        for i in range(len(col_nums))
    )

    parts = []
    for col in col_nums:
        entries = columns[col]
        if len(entries) > 1:
            inner = "\n".join(render_fleet(f, t, class_order) for t, f in entries)
            parts.append(f'    <div style="display:flex;flex-direction:column;gap:16px;">{inner}\n    </div>')
        else:
            parts.append(render_fleet(entries[0][1], entries[0][0], class_order))

    body = "\n".join(parts)
    return f'  <div class="theaters-grid" style="grid-template-columns:{widths};">\n{body}\n  </div>'

# ── loadout section ───────────────────────────────────────────────────────────

def render_loadout_card(sc):
    header = f'{sc["type"]} — {sc["class_name"]}'
    mods   = "\n          ".join(
        f'<div class="mod-entry">'
        f'<span class="mod-name">{m["name"]}</span>'
        f'<span class="mod-qty">×{m["qty"]}</span></div>'
        for m in sc["modules"]
    )
    return f'        <div class="loadout-card"><div class="lc-class">{header}</div>\n          {mods}\n        </div>'

def render_loadout_section(ship_classes):
    cards = "\n".join(render_loadout_card(sc) for sc in ship_classes)
    return f"""    <div class="loadout-section">
      <div class="loadout-header">— Ship Module Loadouts —</div>
      <div class="loadout-grid">
{cards}
      </div>
    </div>"""

# ── legend section ────────────────────────────────────────────────────────────

def render_legend_table(entries):
    rows = "\n            ".join(
        f'<tr>'
        f'<td class="leg-abbr">{e["abbr"]}</td>'
        f'<td class="leg-meaning">{e["name"]}&emsp;Ex:&emsp;'
        f'<em style="font-size:15px;color:#5c3d11;">{e["example"]}</em></td>'
        f'</tr>'
        for e in entries
    )
    return f'<table class="legend-table">\n            {rows}\n          </table>'

def render_ship_images(ship_classes):
    imgs = []
    for sc in ship_classes:
        h   = 50 if sc["type"] in ("CLAA", "DD", "DE", "CM") else 48
        src = f'assets/{sc["class_name"]}-Small.png'
        imgs.append(f'<img src="{src}" width="auto" height="{h}"/>&emsp;&emsp;')
    return "".join(imgs)

def render_legend_section(aircraft_types, mission_types, ship_classes):
    return f"""    <div class="legend-section">
      <div class="legend-header">— Aircraft &amp; Mission Reference —</div>
      <div class="legend-grid">
        <div>
          <div class="legend-group-title">Aircraft Types</div>
          {render_legend_table(aircraft_types)}
        </div>
        <div>
          <div class="legend-group-title">Mission Types</div>
          {render_legend_table(mission_types)}
        </div>
      </div>
      <div><br />{render_ship_images(ship_classes)}</div>
    </div>"""

# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
  @import url('https://fonts.googleapis.com/css2?family=Special+Elite&family=Oswald:wght@400;600;700&family=IM+Fell+English:ital@0;1&display=swap');

  *{box-sizing:border-box;margin:0;padding:0;}

  body{
    background:#c8b89a;
    background-image:
      repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.03) 2px,rgba(0,0,0,.03) 4px),
      repeating-linear-gradient(90deg,transparent,transparent 2px,rgba(0,0,0,.02) 2px,rgba(0,0,0,.02) 4px);
    font-family:'Special Elite',monospace;
    color:#1a1208;
    min-height:100vh;
    padding:18px;
  }

  .page{
    max-width:2440px;
    margin:0 auto;
    border:6px double #5c3d11;
    outline:2px solid #8b6533;
    outline-offset:4px;
    background:#e8dfc8;
    padding:22px 28px 28px;
    position:relative;
  }

  .page::before{
    content:'';
    position:absolute;inset:0;
    background:radial-gradient(ellipse at 20% 20%,rgba(180,140,80,.13) 0%,transparent 60%),
               radial-gradient(ellipse at 80% 80%,rgba(100,60,20,.10) 0%,transparent 55%);
    pointer-events:none;
  }

  .header{text-align:center;border-bottom:3px double #5c3d11;padding-bottom:14px;margin-bottom:18px;}
  .header .stars{font-size:16px;letter-spacing:6px;color:#8b3a0f;margin-bottom:4px;}
  .header h1{
    font-family:'Oswald',sans-serif;font-weight:700;
    font-size:46px;letter-spacing:4px;text-transform:uppercase;
    color:#2a1a05;text-shadow:1px 1px 0 #c8a06a;line-height:1.1;
  }
  .header h2{
    font-family:'IM Fell English',serif;font-style:italic;
    font-size:20px;color:#5c3d11;margin-top:3px;letter-spacing:1px;
  }
  .header .divider{color:#8b3a0f;letter-spacing:4px;font-size:14px;margin-top:4px;}

  .theaters-grid{display:grid;gap:16px;margin-bottom:16px;}

  .theater{border:2px solid #5c3d11;background:rgba(255,248,230,.55);}
  .theater-header{
    background:#2a1a05;color:#e8d5a0;
    font-family:'Oswald',sans-serif;font-weight:700;
    font-size:17px;letter-spacing:3px;text-transform:uppercase;
    text-align:center;padding:7px 8px;border-bottom:2px solid #8b6533;
  }
  .theater-body{padding:10px;}

  .fleet{margin-bottom:12px;}
  .fleet:last-child{margin-bottom:0;}
  .fleet-name{
    font-family:'Oswald',sans-serif;font-weight:600;
    font-size:16px;letter-spacing:2px;text-transform:uppercase;
    color:#8b3a0f;border-bottom:1px solid #a07840;
    padding-bottom:4px;margin-bottom:8px;
  }
  .fleet-sub{
    font-size:14px;font-family:'IM Fell English',serif;font-style:italic;
    color:#5c3d11;display:block;letter-spacing:.5px;
  }
  .fleet-total{
    float:right;
    font-family:'Oswald',sans-serif;font-size:15px;font-weight:600;
    background:#2a1a05;color:#e8d5a0;padding:2px 8px;border-radius:2px;
  }

  .tf-table{width:100%;border-collapse:collapse;}
  .tf-table tr{border-bottom:1px dotted #b09060;}
  .tf-table tr:last-child{border-bottom:none;}
  .tf-table td{padding:5px 5px;vertical-align:top;line-height:1.35;}

  .tf-name{
    font-family:'Oswald',sans-serif;font-weight:900;
    font-size:16px;color:#1a1208;white-space:nowrap;width:104px;
  }
  .tf-role{
    font-size:12.5px;color:#5c3d11;font-style:italic;
    display:block;letter-spacing:.3px;line-height:1.25;
  }
  .tf-comp{font-size:13px;color:#2a1a05;line-height:1.6;}
  .ship-pill{
    display:inline-block;
    background:#2a1a05;color:#e8d5a0;
    font-family:'Oswald',sans-serif;font-weight:600;
    font-size:16px;letter-spacing:.7px;
    padding:2px 6px;border-radius:2px;margin:1px 2px 1px 0;white-space:nowrap;
  }
  .tf-total-cell{
    text-align:right;white-space:nowrap;width:36px;
    font-family:'Oswald',sans-serif;font-size:15px;font-weight:600;color:#8b3a0f;
  }

  .class-totals{
    margin-top:7px;padding-top:6px;
    border-top:1px solid #a07840;
    display:flex;flex-wrap:wrap;gap:4px;
  }
  .ct-pill{
    background:#5c3d11;color:#e8d5a0;
    font-family:'Oswald',sans-serif;font-weight:800;font-size:14px;
    padding:2px 6px;border-radius:2px;white-space:nowrap;
  }

  .bottom-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px;}

  .loadout-section{border:2px solid #5c3d11;background:rgba(255,248,230,.55);padding:12px 14px;}
  .loadout-header{
    font-family:'Oswald',sans-serif;font-weight:700;font-size:17px;
    letter-spacing:3px;text-transform:uppercase;color:#2a1a05;
    border-bottom:2px double #5c3d11;padding-bottom:6px;margin-bottom:10px;text-align:center;
  }
  .loadout-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;}
  .loadout-card{border:1px solid #a07840;background:rgba(240,228,200,.7);padding:8px 10px;}
  .lc-class{
    font-family:'Oswald',sans-serif;font-weight:700;font-size:16px;
    color:#8b3a0f;letter-spacing:1px;border-bottom:1px dotted #a07840;
    padding-bottom:3px;margin-bottom:6px;
  }
  .mod-entry{display:flex;justify-content:space-between;gap:4px;padding:1px 0;}
  .mod-name{font-family:'Oswald',sans-serif;font-weight:600;font-size:13px;color:#2a1a05;}
  .mod-qty{font-family:'Oswald',sans-serif;font-weight:700;font-size:13px;color:#8b3a0f;}

  .legend-section{border:2px solid #5c3d11;background:rgba(255,248,230,.55);padding:12px 14px;}
  .legend-header{
    font-family:'Oswald',sans-serif;font-weight:700;font-size:17px;
    letter-spacing:3px;text-transform:uppercase;color:#2a1a05;
    border-bottom:2px double #5c3d11;padding-bottom:6px;margin-bottom:10px;text-align:center;
  }
  .legend-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
  .legend-group-title{
    font-family:'Oswald',sans-serif;font-weight:600;font-size:14px;
    letter-spacing:2px;text-transform:uppercase;color:#5c3d11;
    border-bottom:1px dotted #a07840;margin-bottom:6px;padding-bottom:3px;
  }
  .legend-table{width:100%;border-collapse:collapse;}
  .legend-table tr{border-bottom:1px dotted rgba(92,61,17,.3);}
  .legend-table tr:last-child{border-bottom:none;}
  .legend-table td{padding:4px 5px;vertical-align:top;}
  .leg-abbr{font-family:'Oswald',sans-serif;font-weight:700;color:#8b3a0f;font-size:14px;white-space:nowrap;width:48px;}
  .leg-meaning{color:#1a1208;font-size:16px;line-height:1.4;}

  .footer{
    text-align:center;margin-top:8px;
    border-top:4px double #5c3d11;padding-top:10px;
    font-family:'IM Fell English',serif;font-style:italic;
    font-size:18px;color:#5c3d11;letter-spacing:1px;
  }
"""

# ── assembly ──────────────────────────────────────────────────────────────────

def render_header():
    return """  <div class="header">
    <div class="stars">★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★</div>
    <h1>United States Navy — Fleet Composition — Cheat Sheet</h1>
    <h2>Hearts of Iron IV — Road To '56</h2>
    <div class="divider">— Made By Graham Pinkston, and don't forget, BUY WAR BONDS! —</div>
  </div>"""

def render_footer(total):
    today = date.today().isoformat()
    return f"""  <div class="footer">
    Designed by Graham Pinkston &nbsp;·&nbsp; Coded by Claud.ai &nbsp;·&nbsp; Total Fleet Strength: {total} Ships Across All Theaters &nbsp;·&nbsp; {today}
  </div>"""

def build_html(theaters, ship_classes, aircraft_types, mission_types):
    class_order    = [sc["type"] for sc in ship_classes]
    theaters_grid  = render_theaters_grid(theaters, class_order)
    loadout        = render_loadout_section(ship_classes)
    legend         = render_legend_section(aircraft_types, mission_types, ship_classes)
    total          = grand_total(theaters)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=2560">
<style>{CSS}</style>
</head>
<body>
<div class="page">
{render_header()}
{theaters_grid}
  <div class="bottom-row">
{loadout}
{legend}
  </div>
{render_footer(total)}
</div>
</body>
</html>"""

# ── entry point ───────────────────────────────────────────────────────────────

def main():
    fleet_data = load("config/fleet.json")
    ref_data   = load("config/references.json")

    html = build_html(
        theaters      = fleet_data["theaters"],
        ship_classes  = ref_data["ship_classes"],
        aircraft_types= ref_data["aircraft_types"],
        mission_types = ref_data["mission_types"],
    )

    out = "cheat_sheet.html"
    write(out, html)
    total = grand_total(fleet_data["theaters"])
    print(f"✓ {out} — {total} ships across all theaters")

if __name__ == "__main__":
    main()