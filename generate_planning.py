#!/usr/bin/env python3
"""Generate a real project planning Excel with a proper Gantt chart (day-by-day bars)
comparing provisional vs real timeline, with pause periods highlighted."""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import date, timedelta

wb = Workbook()

# ═══════════════════════════════════════════════════════════════
# Colors & Styles
# ═══════════════════════════════════════════════════════════════
DARK_BLUE = "1A365D"
MEDIUM_BLUE = "1E40AF"
LIGHT_BLUE = "DBEAFE"
WHITE = "FFFFFF"
LIGHT_GRAY = "F1F5F9"
GREEN = "10B981"
LIGHT_GREEN = "D1FAE5"
ORANGE = "F59E0B"
LIGHT_ORANGE = "FEF3C7"
RED = "EF4444"
LIGHT_RED = "FEE2E2"
PURPLE = "7C3AED"
LIGHT_PURPLE = "EDE9FE"
TEAL = "14B8A6"
LIGHT_TEAL = "CCFBF1"
GRAY = "64748B"
WEEKEND_COLOR = "F8FAFC"

header_font = Font(name="Calibri", bold=True, color=WHITE, size=11)
header_fill = PatternFill(start_color=MEDIUM_BLUE, end_color=MEDIUM_BLUE, fill_type="solid")
subtitle_font = Font(name="Calibri", bold=True, color=DARK_BLUE, size=11)
normal_font = Font(name="Calibri", size=9)
bold_font = Font(name="Calibri", bold=True, size=9)
small_font = Font(name="Calibri", size=8)
note_font = Font(name="Calibri", size=9, color=GRAY, italic=True)

thin_border = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)
hair_border = Border(
    left=Side(style="hair", color="E2E8F0"),
    right=Side(style="hair", color="E2E8F0"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)

center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left_wrap = Alignment(horizontal="left", vertical="center", wrap_text=True)

# Phase colors for Gantt bars
bar_colors = {
    "P1": "3B82F6",  # blue
    "P2": "F59E0B",  # orange
    "P3": "10B981",  # green
    "P4": "8B5CF6",  # purple
    "P5": "EF4444",  # red
    "P6": "64748B",  # gray
    "PAUSE": "FCA5A5",  # light red
    "PREV": "93C5FD",  # light blue (provisional)
}

row_fills = {
    "P1": LIGHT_BLUE, "P2": LIGHT_ORANGE, "P3": LIGHT_GREEN,
    "P4": LIGHT_PURPLE, "P5": LIGHT_RED, "P6": LIGHT_GRAY,
    "PAUSE": "FEE2E2",
}

# ═══════════════════════════════════════════════════════════════
# Gantt date config — one column per week (Mon)
# ═══════════════════════════════════════════════════════════════
gantt_start = date(2025, 9, 1)
gantt_end = date(2026, 1, 26)
total_weeks = ((gantt_end - gantt_start).days // 7) + 1

# Left columns: A=N°, B=Phase, C=Tâche, D=Début, E=Fin, F=Jours
LEFT_COLS = 6
GANTT_COL_START = LEFT_COLS + 1  # col 7 = G

def week_col(d):
    """Return the column index for a given date."""
    delta = (d - gantt_start).days // 7
    return GANTT_COL_START + max(0, min(delta, total_weeks - 1))


# ═══════════════════════════════════════════════════════════════
# Planning data
# ═══════════════════════════════════════════════════════════════

# Provisional phases (for the second Gantt)
provisional_phases = [
    ("P1", "Analyse et Conception", date(2025, 9, 1), date(2025, 9, 30)),
    ("P2", "Développement Backend", date(2025, 10, 1), date(2025, 11, 20)),
    ("P3", "Développement Frontend", date(2025, 11, 1), date(2025, 12, 15)),
    ("P4", "Intégration MikroTik", date(2025, 12, 1), date(2025, 12, 31)),
    ("P5", "Tests et Validation", date(2026, 1, 2), date(2026, 1, 13)),
    ("P6", "Documentation & Soutenance", date(2026, 1, 10), date(2026, 1, 16)),
]

# Real tasks with sub-tasks
real_tasks = [
    # (id, phase_label, task_name, start, end, code, is_phase_header)
    (1, "Phase 1", "Analyse et Conception", date(2025, 9, 1), date(2025, 10, 20), "P1", True),
    (None, "", "  Analyse des besoins", date(2025, 9, 1), date(2025, 9, 10), "P1", False),
    (None, "", "  Étude de l'existant", date(2025, 9, 11), date(2025, 9, 17), "P1", False),
    (None, "", "  Conception UML", date(2025, 9, 18), date(2025, 9, 25), "P1", False),
    (None, "⚠️ PAUSE 1", "Autres projets académiques", date(2025, 9, 26), date(2025, 10, 12), "PAUSE", True),
    (None, "", "  Maquettes UI/UX", date(2025, 10, 13), date(2025, 10, 20), "P1", False),

    (2, "Phase 2", "Développement Backend", date(2025, 10, 21), date(2025, 12, 16), "P2", True),
    (None, "", "  Setup Django + PostgreSQL + Docker", date(2025, 10, 21), date(2025, 10, 27), "P2", False),
    (None, "", "  Modèles Django (User, Profile...)", date(2025, 10, 28), date(2025, 11, 7), "P2", False),
    (None, "", "  Intégration FreeRADIUS", date(2025, 11, 8), date(2025, 11, 21), "P2", False),
    (None, "⚠️ PAUSE 2", "Examens + projets parallèles", date(2025, 11, 22), date(2025, 12, 1), "PAUSE", True),
    (None, "", "  API REST (ViewSets, Serializers)", date(2025, 12, 2), date(2025, 12, 10), "P2", False),
    (None, "", "  Sync RADIUS", date(2025, 12, 11), date(2025, 12, 16), "P2", False),

    (3, "Phase 3", "Développement Frontend", date(2025, 12, 2), date(2026, 1, 3), "P3", True),
    (None, "", "  Setup Vue.js 3 + Vite", date(2025, 12, 2), date(2025, 12, 5), "P3", False),
    (None, "", "  Pages gestion utilisateurs", date(2025, 12, 6), date(2025, 12, 14), "P3", False),
    (None, "", "  Pages profils + promotions", date(2025, 12, 15), date(2025, 12, 20), "P3", False),
    (None, "⚠️ PAUSE 3", "Fêtes de fin d'année", date(2025, 12, 21), date(2025, 12, 28), "PAUSE", True),
    (None, "", "  Dashboard + statistiques", date(2025, 12, 29), date(2026, 1, 3), "P3", False),

    (4, "Phase 4", "Intégration MikroTik", date(2026, 1, 2), date(2026, 1, 12), "P4", True),
    (None, "", "  Agent Node.js (RouterOS API)", date(2026, 1, 2), date(2026, 1, 6), "P4", False),
    (None, "", "  Hotspot Sync + DNS Blocking", date(2026, 1, 7), date(2026, 1, 10), "P4", False),
    (None, "", "  Pages hotspot personnalisées", date(2026, 1, 11), date(2026, 1, 12), "P4", False),

    (5, "Phase 5", "Tests et Validation", date(2026, 1, 13), date(2026, 1, 16), "P5", True),
    (None, "", "  Tests unitaires + intégration", date(2026, 1, 13), date(2026, 1, 15), "P5", False),
    (None, "", "  Tests utilisateurs (UAT)", date(2026, 1, 15), date(2026, 1, 16), "P5", False),

    (6, "Phase 6", "Documentation & Soutenance", date(2026, 1, 16), date(2026, 1, 20), "P6", True),
    (None, "", "  Rapport technique + PPT", date(2026, 1, 16), date(2026, 1, 19), "P6", False),
    (None, "", "  📌 SOUTENANCE", date(2026, 1, 20), date(2026, 1, 20), "P6", False),
]


# ═══════════════════════════════════════════════════════════════
# SHEET 1 — Diagramme de Gantt Réel
# ═══════════════════════════════════════════════════════════════
ws = wb.active
ws.title = "Gantt Réel"

# Column widths
ws.column_dimensions["A"].width = 4
ws.column_dimensions["B"].width = 16
ws.column_dimensions["C"].width = 30
ws.column_dimensions["D"].width = 10
ws.column_dimensions["E"].width = 10
ws.column_dimensions["F"].width = 6

for i in range(total_weeks):
    ws.column_dimensions[get_column_letter(GANTT_COL_START + i)].width = 4.2

# ─── Row 1: Title ───
ws.merge_cells(f"A1:{get_column_letter(GANTT_COL_START + total_weeks - 1)}1")
ws["A1"] = "DIAGRAMME DE GANTT — PLANNING RÉEL — PORTAIL CAPTIF WIFI UCAC-ICAM"
ws["A1"].font = Font(name="Calibri", bold=True, color=DARK_BLUE, size=14)
ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[1].height = 30

# ─── Row 2: Subtitle ───
ws.merge_cells(f"A2:{get_column_letter(GANTT_COL_START + total_weeks - 1)}2")
ws["A2"] = "Septembre 2025 → Janvier 2026  |  Durée totale : 141 jours  |  Travail effectif : ~106 jours  |  Pauses : ~35 jours"
ws["A2"].font = Font(name="Calibri", color=GRAY, size=10)
ws["A2"].alignment = Alignment(horizontal="center")

# ─── Row 3: Month headers ───
months_info = [
    ("SEPT.", date(2025, 9, 1), date(2025, 9, 30), "DBEAFE"),
    ("OCT.", date(2025, 10, 1), date(2025, 10, 31), "FEF3C7"),
    ("NOV.", date(2025, 11, 1), date(2025, 11, 30), "D1FAE5"),
    ("DÉC.", date(2025, 12, 1), date(2025, 12, 31), "EDE9FE"),
    ("JANV.", date(2026, 1, 1), date(2026, 1, 25), "FEE2E2"),
]

# First fill all month header cells, then merge
for mname, mstart, mend, mcolor in months_info:
    cs = week_col(mstart)
    ce = week_col(mend)
    # Avoid overlap with next month
    fill = PatternFill(start_color=mcolor, end_color=mcolor, fill_type="solid")
    for c in range(cs, ce + 1):
        cell = ws.cell(row=3, column=c)
        cell.fill = fill
        cell.border = thin_border
    ws.cell(row=3, column=cs, value=mname)
    ws.cell(row=3, column=cs).font = Font(name="Calibri", bold=True, color=DARK_BLUE, size=9)
    ws.cell(row=3, column=cs).alignment = center

# Merge month cells (adjust to avoid overlaps)
prev_end = None
for mname, mstart, mend, mcolor in months_info:
    cs = week_col(mstart)
    ce = week_col(mend)
    if prev_end is not None and cs <= prev_end:
        cs = prev_end + 1
    if cs < ce:
        ws.merge_cells(start_row=3, start_column=cs, end_row=3, end_column=ce)
    prev_end = ce

# Left side row 3
for c in range(1, LEFT_COLS + 1):
    ws.cell(row=3, column=c).fill = header_fill
    ws.cell(row=3, column=c).border = thin_border

# ─── Row 4: Week start dates ───
for i in range(total_weeks):
    d = gantt_start + timedelta(weeks=i)
    col = GANTT_COL_START + i
    cell = ws.cell(row=4, column=col, value=f"S{i+1}\n{d.day}/{d.month}")
    cell.font = Font(name="Calibri", size=7, color=GRAY)
    cell.alignment = center
    cell.border = thin_border
    cell.fill = PatternFill(start_color=LIGHT_GRAY, end_color=LIGHT_GRAY, fill_type="solid")

ws.row_dimensions[4].height = 25

# ─── Row 4 left side: headers ───
left_headers = ["N°", "Phase", "Tâche", "Début", "Fin", "J"]
for i, h in enumerate(left_headers, 1):
    cell = ws.cell(row=4, column=i, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = center
    cell.border = thin_border

# ─── Task rows ───
row = 5
task_num = 0

for tid, phase, task, start, end, code, is_header in real_tasks:
    days = (end - start).days + 1

    if tid is not None:
        task_num = tid

    # Left columns
    ws.cell(row=row, column=1, value=tid if tid else "").alignment = center
    ws.cell(row=row, column=2, value=phase).alignment = left_wrap
    ws.cell(row=row, column=3, value=task).alignment = left_wrap
    ws.cell(row=row, column=4, value=start.strftime("%d/%m")).alignment = center
    ws.cell(row=row, column=5, value=end.strftime("%d/%m")).alignment = center
    ws.cell(row=row, column=6, value=days).alignment = center

    # Fonts
    if code == "PAUSE":
        ws.cell(row=row, column=2).font = Font(name="Calibri", bold=True, color=RED, size=9)
        ws.cell(row=row, column=3).font = Font(name="Calibri", bold=True, color=RED, size=9)
        row_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    elif is_header:
        ws.cell(row=row, column=2).font = Font(name="Calibri", bold=True, color=DARK_BLUE, size=9)
        ws.cell(row=row, column=3).font = Font(name="Calibri", bold=True, color=DARK_BLUE, size=9)
        row_fill = PatternFill(start_color=row_fills[code], end_color=row_fills[code], fill_type="solid")
    else:
        ws.cell(row=row, column=2).font = normal_font
        ws.cell(row=row, column=3).font = normal_font
        row_fill = None

    ws.cell(row=row, column=4).font = small_font
    ws.cell(row=row, column=5).font = small_font
    ws.cell(row=row, column=6).font = small_font

    # Apply row fill to left columns
    for c in range(1, LEFT_COLS + 1):
        ws.cell(row=row, column=c).border = thin_border
        if row_fill:
            ws.cell(row=row, column=c).fill = row_fill

    # ─── Gantt bar ───
    bar_fill = PatternFill(start_color=bar_colors[code], end_color=bar_colors[code], fill_type="solid")
    bar_start_w = max(0, (start - gantt_start).days // 7)
    bar_end_w = min(total_weeks - 1, (end - gantt_start).days // 7)

    for w in range(total_weeks):
        col = GANTT_COL_START + w
        if bar_start_w <= w <= bar_end_w:
            ws.cell(row=row, column=col).fill = bar_fill
            ws.cell(row=row, column=col).border = thin_border
        else:
            ws.cell(row=row, column=col).border = hair_border

    # Row height
    ws.row_dimensions[row].height = 20 if not is_header else 22

    row += 1

data_end_row = row - 1

# ─── Separator ───
row += 1

# ─── Provisional Gantt (for comparison) ───
ws.cell(row=row, column=1, value="").border = thin_border
ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=LEFT_COLS)
ws.cell(row=row, column=2, value="PLANNING PRÉVISIONNEL (comparaison)")
ws.cell(row=row, column=2).font = Font(name="Calibri", bold=True, color=WHITE, size=11)
ws.cell(row=row, column=2).alignment = center
for c in range(1, LEFT_COLS + 1):
    ws.cell(row=row, column=c).fill = PatternFill(start_color=DARK_BLUE, end_color=DARK_BLUE, fill_type="solid")
    ws.cell(row=row, column=c).border = thin_border
for w in range(total_weeks):
    col = GANTT_COL_START + w
    ws.cell(row=row, column=col).fill = PatternFill(start_color=DARK_BLUE, end_color=DARK_BLUE, fill_type="solid")
    ws.cell(row=row, column=col).border = thin_border

row += 1

for code, name, pstart, pend in provisional_phases:
    days = (pend - pstart).days + 1
    ws.cell(row=row, column=1, value="").alignment = center
    ws.cell(row=row, column=2, value=code)
    ws.cell(row=row, column=2).font = bold_font
    ws.cell(row=row, column=2).alignment = center
    ws.cell(row=row, column=3, value=name).alignment = left_wrap
    ws.cell(row=row, column=3).font = normal_font
    ws.cell(row=row, column=4, value=pstart.strftime("%d/%m")).alignment = center
    ws.cell(row=row, column=4).font = small_font
    ws.cell(row=row, column=5, value=pend.strftime("%d/%m")).alignment = center
    ws.cell(row=row, column=5).font = small_font
    ws.cell(row=row, column=6, value=days).alignment = center
    ws.cell(row=row, column=6).font = small_font

    prev_fill = PatternFill(start_color=bar_colors["PREV"], end_color=bar_colors["PREV"], fill_type="solid")
    phase_bar_fill = PatternFill(start_color=bar_colors[code], end_color=bar_colors[code], fill_type="solid")
    bar_s = max(0, (pstart - gantt_start).days // 7)
    bar_e = min(total_weeks - 1, (pend - gantt_start).days // 7)

    for c in range(1, LEFT_COLS + 1):
        ws.cell(row=row, column=c).border = thin_border

    for w in range(total_weeks):
        col = GANTT_COL_START + w
        if bar_s <= w <= bar_e:
            ws.cell(row=row, column=col).fill = phase_bar_fill
            ws.cell(row=row, column=col).border = thin_border
        else:
            ws.cell(row=row, column=col).border = hair_border

    ws.row_dimensions[row].height = 20
    row += 1

# ─── Legend ───
row += 1
ws.merge_cells(f"A{row}:F{row}")
ws.cell(row=row, column=1, value="LÉGENDE").font = subtitle_font

legend_items = [
    ("Phase 1 — Analyse et Conception", "P1"),
    ("Phase 2 — Développement Backend", "P2"),
    ("Phase 3 — Développement Frontend", "P3"),
    ("Phase 4 — Intégration MikroTik", "P4"),
    ("Phase 5 — Tests et Validation", "P5"),
    ("Phase 6 — Documentation & Soutenance", "P6"),
    ("⚠️ PAUSE — Autres projets / Examens / Congés", "PAUSE"),
]

for label, code in legend_items:
    row += 1
    c1 = ws.cell(row=row, column=1, value="")
    c1.fill = PatternFill(start_color=bar_colors[code], end_color=bar_colors[code], fill_type="solid")
    c1.border = thin_border
    ws.merge_cells(f"B{row}:F{row}")
    ws.cell(row=row, column=2, value=label).font = normal_font
    ws.cell(row=row, column=2).alignment = left_wrap

# ═══════════════════════════════════════════════════════════════
# SHEET 2 — Analyse des Écarts
# ═══════════════════════════════════════════════════════════════
ws2 = wb.create_sheet("Analyse des Écarts")

ws2.column_dimensions["A"].width = 5
ws2.column_dimensions["B"].width = 32
ws2.column_dimensions["C"].width = 13
ws2.column_dimensions["D"].width = 13
ws2.column_dimensions["E"].width = 13
ws2.column_dimensions["F"].width = 13
ws2.column_dimensions["G"].width = 10
ws2.column_dimensions["H"].width = 10
ws2.column_dimensions["I"].width = 55

ws2.merge_cells("A1:I1")
ws2["A1"] = "ANALYSE DES ÉCARTS — PLANNING PRÉVISIONNEL vs RÉEL"
ws2["A1"].font = Font(name="Calibri", bold=True, color=DARK_BLUE, size=14)
ws2["A1"].alignment = Alignment(horizontal="center")

ws2.merge_cells("A2:I2")
ws2["A2"] = "Portail Captif WiFi UCAC-ICAM  |  Sept. 2025 — Jan. 2026"
ws2["A2"].font = Font(name="Calibri", color=GRAY, size=10)
ws2["A2"].alignment = Alignment(horizontal="center")

row2 = 4
h2 = ["N°", "Phase", "Début\nPrévu", "Fin\nPrévue", "Début\nRéel", "Fin\nRéelle", "Retard\n(jours)", "Écart", "Cause de l'écart"]
for i, h in enumerate(h2, 1):
    cell = ws2.cell(row=row2, column=i, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = center
    cell.border = thin_border

real_phases = [
    ("Phase 1: Analyse et Conception",
     date(2025, 9, 1), date(2025, 9, 30), date(2025, 9, 1), date(2025, 10, 20),
     "Pause de ~2,5 sem. (26/09–12/10) pour travail sur d'autres projets académiques non liés au portail captif."),
    ("Phase 2: Développement Backend",
     date(2025, 10, 1), date(2025, 11, 20), date(2025, 10, 21), date(2025, 12, 16),
     "Début décalé de 3 sem. + pause examens (22/11–01/12). Examens semestriels et projets parallèles obligatoires."),
    ("Phase 3: Développement Frontend",
     date(2025, 11, 1), date(2025, 12, 15), date(2025, 12, 2), date(2026, 1, 3),
     "Début décalé (backend pas terminé) + pause Noël (21–28/12). Travail en parallèle avec fin du backend."),
    ("Phase 4: Intégration MikroTik",
     date(2025, 12, 1), date(2025, 12, 31), date(2026, 1, 2), date(2026, 1, 12),
     "Phase compressée (11j au lieu de 31j) grâce à l'expérience acquise et l'assistance IA."),
    ("Phase 5: Tests et Validation",
     date(2026, 1, 2), date(2026, 1, 13), date(2026, 1, 13), date(2026, 1, 16),
     "Phase réduite (4j au lieu de 10). Tests écrits en parallèle du développement."),
    ("Phase 6: Documentation & Soutenance",
     date(2026, 1, 10), date(2026, 1, 16), date(2026, 1, 16), date(2026, 1, 20),
     "Décalage de 4 jours. Soutenance reportée au 20 janvier."),
]

for idx, (phase, ps, pe, rs, re, cause) in enumerate(real_phases, 1):
    row2 += 1
    retard = (re - pe).days
    ecart = f"+{retard}j" if retard > 0 else f"{retard}j" if retard < 0 else "0j"

    ws2.cell(row=row2, column=1, value=idx).alignment = center
    ws2.cell(row=row2, column=2, value=phase).alignment = left_wrap
    ws2.cell(row=row2, column=3, value=ps.strftime("%d/%m/%y")).alignment = center
    ws2.cell(row=row2, column=4, value=pe.strftime("%d/%m/%y")).alignment = center
    ws2.cell(row=row2, column=5, value=rs.strftime("%d/%m/%y")).alignment = center
    ws2.cell(row=row2, column=6, value=re.strftime("%d/%m/%y")).alignment = center
    ws2.cell(row=row2, column=7, value=retard).alignment = center
    ws2.cell(row=row2, column=8, value=ecart).alignment = center
    ws2.cell(row=row2, column=9, value=cause).alignment = left_wrap

    if retard > 10:
        color = RED
    elif retard > 0:
        color = ORANGE
    else:
        color = GREEN
    ws2.cell(row=row2, column=7).font = Font(name="Calibri", bold=True, color=color, size=10)
    ws2.cell(row=row2, column=8).font = Font(name="Calibri", bold=True, color=color, size=10)

    fill_color = row_fills.get(f"P{idx}", LIGHT_GRAY)
    rfill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
    for c in range(1, 10):
        ws2.cell(row=row2, column=c).border = thin_border
        if c not in (7, 8):
            ws2.cell(row=row2, column=c).font = normal_font
        ws2.cell(row=row2, column=c).fill = rfill
    ws2.cell(row=row2, column=2).font = bold_font
    ws2.row_dimensions[row2].height = 50

# ─── Summary ───
row2 += 2
ws2.merge_cells(f"A{row2}:I{row2}")
ws2.cell(row=row2, column=1, value="SYNTHÈSE").font = subtitle_font

summaries = [
    ("📅 Durée prévue : 1er sept → 16 jan = 137 jours", LIGHT_BLUE),
    ("📅 Durée réelle : 1er sept → 20 jan = 141 jours (+4 jours)", LIGHT_ORANGE),
    ("⏸️ Pauses totales : ~35 jours en 3 interruptions", "FEE2E2"),
    ("✅ Travail effectif : ~106 jours — Projet livré malgré les contraintes", LIGHT_GREEN),
]

for text, color in summaries:
    row2 += 1
    ws2.merge_cells(f"A{row2}:I{row2}")
    ws2.cell(row=row2, column=1, value=text).font = bold_font
    ws2.cell(row=row2, column=1).fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
    ws2.cell(row=row2, column=1).border = thin_border

row2 += 2
ws2.merge_cells(f"A{row2}:I{row2}")
ws2.cell(row=row2, column=1, value="CAUSES PRINCIPALES DES ÉCARTS").font = subtitle_font

causes = [
    ("1. Projets académiques (sept–oct)",
     "Travail obligatoire sur d'autres projets imposés par le cursus, non liés au portail captif."),
    ("2. Examens semestriels (nov–déc)",
     "Période d'examens et projets évalués nécessitant une pause dans le développement."),
    ("3. Congés de Noël (déc)",
     "Pause pour les fêtes de fin d'année, période non travaillée."),
    ("4. Stratégie de rattrapage",
     "Phases 4-5-6 compressées. Travail en parallèle (backend+frontend) et assistance IA (Claude) ont permis de livrer à temps malgré ~5 semaines de pause."),
]

for title, desc in causes:
    row2 += 1
    ws2.merge_cells(f"A{row2}:C{row2}")
    ws2.cell(row=row2, column=1, value=title).font = bold_font
    ws2.cell(row=row2, column=1).border = thin_border
    ws2.merge_cells(f"D{row2}:I{row2}")
    ws2.cell(row=row2, column=4, value=desc).font = note_font
    ws2.cell(row=row2, column=4).alignment = left_wrap
    ws2.cell(row=row2, column=4).border = thin_border
    ws2.row_dimensions[row2].height = 35

# ─── Print & freeze ───
for sheet in [ws, ws2]:
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = 9
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0

ws.freeze_panes = "G5"

# Save
output = "/home/user/captive-portal/Planning_Reel_Portail_Captif_UCAC_ICAM.xlsx"
wb.save(output)
print(f"Planning saved to: {output}")
