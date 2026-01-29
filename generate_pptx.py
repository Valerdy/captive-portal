#!/usr/bin/env python3
"""Generate a comprehensive PowerPoint presentation for the Captive Portal project."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# Colors
DARK_BLUE = RGBColor(0x1A, 0x36, 0x5D)
MEDIUM_BLUE = RGBColor(0x1E, 0x40, 0xAF)
LIGHT_BLUE = RGBColor(0x25, 0x63, 0xEB)
ACCENT_BLUE = RGBColor(0xDB, 0xEA, 0xFE)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x33, 0x33, 0x33)
GRAY = RGBColor(0x64, 0x74, 0x8B)
LIGHT_GRAY = RGBColor(0xF1, 0xF5, 0xF9)
GREEN = RGBColor(0x10, 0xB9, 0x81)
ORANGE = RGBColor(0xF5, 0x9E, 0x0B)
RED = RGBColor(0xEF, 0x44, 0x44)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

W = prs.slide_width
H = prs.slide_height


def add_bg(slide, color=WHITE):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_shape(slide, left, top, width, height, color, border_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)
    else:
        shape.line.fill.background()
    return shape


def add_rect(slide, left, top, width, height, color):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def set_text(shape, text, size=14, bold=False, color=BLACK, align=PP_ALIGN.LEFT):
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.alignment = align
    return tf


def add_para(tf, text, size=14, bold=False, color=BLACK, align=PP_ALIGN.LEFT, space_before=Pt(4), bullet=False):
    p = tf.add_paragraph()
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.alignment = align
    if space_before:
        p.space_before = space_before
    if bullet:
        p.level = 0
    return p


def title_slide(title, subtitle=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    add_bg(slide, DARK_BLUE)
    # Top bar
    add_rect(slide, 0, 0, W, Inches(0.08), LIGHT_BLUE)
    # Title
    txBox = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(11.333), Inches(2))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER
    if subtitle:
        add_para(tf, subtitle, size=20, color=RGBColor(0xBF, 0xDB, 0xFE), align=PP_ALIGN.CENTER, space_before=Pt(16))
    # Bottom bar
    add_rect(slide, 0, Inches(7.42), W, Inches(0.08), LIGHT_BLUE)
    return slide


def section_slide(number, title):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    add_rect(slide, 0, 0, W, Inches(0.06), LIGHT_BLUE)
    # Number circle
    circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(5.667), Inches(2), Inches(2), Inches(2))
    circ.fill.solid()
    circ.fill.fore_color.rgb = MEDIUM_BLUE
    circ.line.fill.background()
    set_text(circ, str(number), size=48, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    circ.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    # Title
    txBox = slide.shapes.add_textbox(Inches(1), Inches(4.3), Inches(11.333), Inches(1.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = DARK_BLUE
    p.alignment = PP_ALIGN.CENTER
    add_rect(slide, 0, Inches(7.44), W, Inches(0.06), LIGHT_BLUE)
    return slide


def content_slide(title, bullets, subtitle=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    # Header bar
    add_rect(slide, 0, 0, W, Inches(1.1), MEDIUM_BLUE)
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.15), Inches(12), Inches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE
    if subtitle:
        add_para(tf, subtitle, size=16, color=RGBColor(0xBF, 0xDB, 0xFE), space_before=Pt(4))
    # Content
    txBox2 = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.5))
    tf2 = txBox2.text_frame
    tf2.word_wrap = True
    first = True
    for b in bullets:
        if first:
            p = tf2.paragraphs[0]
            first = False
        else:
            p = tf2.add_paragraph()
        if isinstance(b, tuple):
            text, level = b
        else:
            text, level = b, 0
        p.text = text
        p.font.size = Pt(17 if level == 0 else 15)
        p.font.color.rgb = BLACK if level == 0 else GRAY
        p.font.bold = (level == 0 and text.endswith(":")) or (level == 0 and ":" in text and len(text) < 80)
        p.space_before = Pt(10 if level == 0 else 4)
        p.level = level
    # Footer
    add_rect(slide, 0, Inches(7.44), W, Inches(0.06), LIGHT_BLUE)
    return slide


def two_col_slide(title, left_title, left_bullets, right_title, right_bullets):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    add_rect(slide, 0, 0, W, Inches(1.1), MEDIUM_BLUE)
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.15), Inches(12), Inches(0.8))
    set_text(txBox, title, size=28, bold=True, color=WHITE)
    # Left col
    box_l = add_shape(slide, Inches(0.5), Inches(1.4), Inches(5.9), Inches(5.5), LIGHT_GRAY, MEDIUM_BLUE)
    txL = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(5.3), Inches(0.5))
    set_text(txL, left_title, size=20, bold=True, color=MEDIUM_BLUE, align=PP_ALIGN.CENTER)
    txLC = slide.shapes.add_textbox(Inches(0.8), Inches(2.1), Inches(5.3), Inches(4.5))
    tf = txLC.text_frame
    tf.word_wrap = True
    for i, b in enumerate(left_bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = b
        p.font.size = Pt(15)
        p.font.color.rgb = BLACK
        p.space_before = Pt(6)
    # Right col
    box_r = add_shape(slide, Inches(6.9), Inches(1.4), Inches(5.9), Inches(5.5), LIGHT_GRAY, MEDIUM_BLUE)
    txR = slide.shapes.add_textbox(Inches(7.2), Inches(1.5), Inches(5.3), Inches(0.5))
    set_text(txR, right_title, size=20, bold=True, color=MEDIUM_BLUE, align=PP_ALIGN.CENTER)
    txRC = slide.shapes.add_textbox(Inches(7.2), Inches(2.1), Inches(5.3), Inches(4.5))
    tf2 = txRC.text_frame
    tf2.word_wrap = True
    for i, b in enumerate(right_bullets):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.text = b
        p.font.size = Pt(15)
        p.font.color.rgb = BLACK
        p.space_before = Pt(6)
    add_rect(slide, 0, Inches(7.44), W, Inches(0.06), LIGHT_BLUE)
    return slide


def code_slide(title, code_text, note=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    add_rect(slide, 0, 0, W, Inches(1.1), MEDIUM_BLUE)
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.15), Inches(12), Inches(0.8))
    set_text(txBox, title, size=28, bold=True, color=WHITE)
    # Code block
    code_h = Inches(5.0) if note else Inches(5.6)
    box = add_shape(slide, Inches(0.5), Inches(1.4), Inches(12.333), code_h, RGBColor(0x1E, 0x29, 0x3B))
    txC = slide.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), code_h - Inches(0.4))
    tf = txC.text_frame
    tf.word_wrap = True
    for i, line in enumerate(code_text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(13)
        p.font.name = "Consolas"
        p.font.color.rgb = RGBColor(0xE2, 0xE8, 0xF0)
        p.space_before = Pt(2)
    if note:
        note_box = add_shape(slide, Inches(0.5), Inches(6.6), Inches(12.333), Inches(0.7), ACCENT_BLUE, LIGHT_BLUE)
        set_text(note_box, "  " + note, size=13, color=MEDIUM_BLUE)
    add_rect(slide, 0, Inches(7.44), W, Inches(0.06), LIGHT_BLUE)
    return slide


def diagram_slide(title):
    """Network architecture diagram as text boxes."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    add_rect(slide, 0, 0, W, Inches(1.1), MEDIUM_BLUE)
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.15), Inches(12), Inches(0.8))
    set_text(txBox, title, size=28, bold=True, color=WHITE)

    # Internet cloud
    inet = add_shape(slide, Inches(5.5), Inches(1.3), Inches(2.3), Inches(0.8), RGBColor(0xFE, 0xF3, 0xC7), ORANGE)
    set_text(inet, "INTERNET (WAN)", size=14, bold=True, color=BLACK, align=PP_ALIGN.CENTER)

    # MikroTik
    mk = add_shape(slide, Inches(4.5), Inches(2.6), Inches(4.3), Inches(1.2), RGBColor(0xDB, 0xEA, 0xFE), MEDIUM_BLUE)
    tf = mk.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "MikroTik RB951Ui-2HnD"
    p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = DARK_BLUE; p.alignment = PP_ALIGN.CENTER
    add_para(tf, "10.242.18.6  |  Hotspot + RADIUS Client + NAT + DNS", size=11, color=GRAY, align=PP_ALIGN.CENTER)

    # Server
    srv = add_shape(slide, Inches(0.5), Inches(4.5), Inches(5.5), Inches(2.5), RGBColor(0xD1, 0xFA, 0xE5), GREEN)
    tf2 = srv.text_frame; tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "Serveur Backend (Ubuntu 22.04 LTS)"; p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = DARK_BLUE; p.alignment = PP_ALIGN.CENTER
    add_para(tf2, "Django REST + PostgreSQL + FreeRADIUS", size=12, color=GRAY, align=PP_ALIGN.CENTER)
    add_para(tf2, "RADIUS: UDP 1812/1813  |  API: HTTP 8000", size=11, color=GRAY, align=PP_ALIGN.CENTER)
    add_para(tf2, "Agent MikroTik (Node.js): HTTP 3001", size=11, color=GRAY, align=PP_ALIGN.CENTER)
    add_para(tf2, "Redis + Celery + Prometheus + Grafana", size=11, color=GRAY, align=PP_ALIGN.CENTER)

    # Client
    cl = add_shape(slide, Inches(7.5), Inches(4.5), Inches(5.3), Inches(2.5), RGBColor(0xFE, 0xE2, 0xE2), RED)
    tf3 = cl.text_frame; tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "Clients WiFi"; p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = DARK_BLUE; p.alignment = PP_ALIGN.CENTER
    add_para(tf3, "DHCP: 10.242.18.100 - 10.242.18.200", size=12, color=GRAY, align=PP_ALIGN.CENTER)
    add_para(tf3, "Gateway: 10.242.18.6 | DNS: 10.242.18.6", size=11, color=GRAY, align=PP_ALIGN.CENTER)
    add_para(tf3, "Redirection captive vers page de login", size=11, color=GRAY, align=PP_ALIGN.CENTER)
    add_para(tf3, "Authentification via RADIUS (PAP/CHAP)", size=11, color=GRAY, align=PP_ALIGN.CENTER)

    # Arrows as text
    arr1 = slide.shapes.add_textbox(Inches(6.2), Inches(2.15), Inches(1), Inches(0.4))
    set_text(arr1, "▼", size=18, bold=True, color=MEDIUM_BLUE, align=PP_ALIGN.CENTER)

    arr2 = slide.shapes.add_textbox(Inches(2.5), Inches(3.9), Inches(2.5), Inches(0.5))
    set_text(arr2, "◄── RADIUS (1812/1813) ──►", size=11, bold=True, color=GREEN, align=PP_ALIGN.CENTER)

    arr3 = slide.shapes.add_textbox(Inches(8.5), Inches(3.9), Inches(2.5), Inches(0.5))
    set_text(arr3, "◄── WiFi / DHCP ──►", size=11, bold=True, color=RED, align=PP_ALIGN.CENTER)

    add_rect(slide, 0, Inches(7.44), W, Inches(0.06), LIGHT_BLUE)
    return slide


# ═══════════════════════════════════════════════════════════════
# SLIDES
# ═══════════════════════════════════════════════════════════════

# 1. Title
s = title_slide(
    "Portail Captif WiFi - UCAC-ICAM",
    "Récapitulatif Complet des Configurations\nProjet de fin d'études — Janvier 2026"
)
# Add author info
txA = s.shapes.add_textbox(Inches(3), Inches(5.2), Inches(7.333), Inches(1.5))
tf = txA.text_frame; tf.word_wrap = True
add_para(tf, "Auteur : Valerdy", size=16, color=RGBColor(0xBF, 0xDB, 0xFE), align=PP_ALIGN.CENTER, space_before=Pt(0))
add_para(tf, "Encadrement technique avec Claude (Assistant IA)", size=14, color=GRAY, align=PP_ALIGN.CENTER)

# 2. Sommaire
content_slide("Sommaire de la Présentation", [
    "1.  Introduction et objectifs du projet",
    "2.  Architecture réseau globale",
    "3.  MikroTik — Interfaces et adressage IP",
    "4.  MikroTik — DHCP Server",
    "5.  MikroTik — Configuration Hotspot",
    "6.  MikroTik — NAT (Masquerade)",
    "7.  MikroTik — Sécurité, DNS et contrôle d'accès",
    "8.  Machine cliente — Connexion et tests",
    "9.  FreeRADIUS — Rôle et architecture",
    "10. FreeRADIUS — Fichiers de configuration",
    "11. FreeRADIUS — Authentification et communication MikroTik",
    "12. FreeRADIUS — Logs et vérifications",
    "13. PostgreSQL — Base de données et tables RADIUS",
    "14. PostgreSQL — Lien FreeRADIUS ↔ PostgreSQL",
    "15. Flux d'authentification complet",
    "16. Conclusion et résumé final",
])

# 3. Introduction
content_slide("Introduction et Objectifs du Projet", [
    "Contexte :",
    ("Le campus UCAC-ICAM a besoin d'un système WiFi sécurisé avec authentification", 1),
    ("Les étudiants et le personnel doivent s'identifier avant d'accéder à Internet", 1),
    "",
    "Objectif principal :",
    ("Mettre en place un portail captif WiFi avec gestion centralisée des accès", 1),
    ("Authentification RADIUS, gestion des quotas, contrôle de bande passante", 1),
    "",
    "Technologies utilisées :",
    ("MikroTik RB951Ui-2HnD — Routeur hotspot + client RADIUS", 1),
    ("FreeRADIUS 3.0 — Serveur d'authentification AAA", 1),
    ("PostgreSQL 15 — Base de données (tables RADIUS + Django)", 1),
    ("Django REST Framework — Backend API de gestion", 1),
    ("Vue.js 3 — Interface d'administration", 1),
    ("Docker Compose — Orchestration de 11 services", 1),
])

# 4. Section 1 - MikroTik
section_slide(1, "Configuration MikroTik")

# 5. Architecture réseau
diagram_slide("Architecture Réseau Globale")

# 6. MikroTik Interfaces
two_col_slide(
    "MikroTik — Interfaces et Adressage IP",
    "Interfaces",
    [
        "• ether1-WAN : Connexion Internet (WAN)",
        "• ether2-LAN : Réseau local (LAN)",
        "• bridge-LAN : Bridge regroupant les interfaces LAN",
        "",
        "Commandes RouterOS :",
        "/interface ethernet set ether1 name=ether1-WAN",
        "/interface ethernet set ether2 name=ether2-LAN",
        "/interface bridge add name=bridge-LAN",
        "/interface bridge port add bridge=bridge-LAN",
        "    interface=ether2-LAN",
    ],
    "Adressage IP",
    [
        "• Routeur (LAN) : 10.242.18.6/24",
        "  → Passerelle par défaut des clients",
        "  → Serveur DNS local",
        "  → Interface du hotspot",
        "",
        "• Pool DHCP : 10.242.18.100 - .200",
        "  → 101 adresses disponibles",
        "",
        "• Sous-réseau : 10.242.18.0/24",
        "",
        "Commande :",
        "/ip address add address=10.242.18.6/24",
        "    interface=bridge-LAN",
    ]
)

# 7. DHCP Server
content_slide("MikroTik — Serveur DHCP", [
    "Rôle : Attribuer automatiquement une adresse IP à chaque client WiFi connecté",
    "",
    "Configuration du pool DHCP :",
    ("Pool name : dhcp-pool", 1),
    ("Plage d'adresses : 10.242.18.100 à 10.242.18.200 (101 adresses)", 1),
    "",
    "Configuration du serveur DHCP :",
    ("Interface : bridge-LAN", 1),
    ("Réseau : 10.242.18.0/24", 1),
    ("Passerelle (gateway) : 10.242.18.6", 1),
    ("Serveur DNS : 10.242.18.6 (le routeur lui-même)", 1),
    "",
    "Commandes RouterOS :",
    ("/ip pool add name=dhcp-pool ranges=10.242.18.100-10.242.18.200", 1),
    ("/ip dhcp-server add name=dhcp-server interface=bridge-LAN address-pool=dhcp-pool", 1),
    ("/ip dhcp-server network add address=10.242.18.0/24 gateway=10.242.18.6 dns-server=10.242.18.6", 1),
])

# 8. Hotspot
content_slide("MikroTik — Configuration du Hotspot", [
    "Principe du hotspot :",
    ("Tout client connecté au WiFi est redirigé vers une page de login", 1),
    ("L'utilisateur doit s'authentifier pour accéder à Internet", 1),
    ("MikroTik délègue l'authentification au serveur FreeRADIUS", 1),
    "",
    "Profil hotspot créé : ucac-icam-profile",
    ("Adresse hotspot : 10.242.18.6", 1),
    ("Nom DNS : wifi.ucac-icam.cm", 1),
    ("Utilisation RADIUS : oui (use-radius=yes)", 1),
    ("Accounting RADIUS : oui (suivi des sessions)", 1),
    ("Intervalle interim : 5 minutes", 1),
    ("Méthodes de login : HTTP-CHAP et HTTP-PAP", 1),
    "",
    "Activation du hotspot :",
    ("Interface : bridge-LAN  |  Pool : dhcp-pool", 1),
    "",
    "Walled Garden (accès sans authentification) :",
    ("Serveur backend (Django, FreeRADIUS) accessible sans login", 1),
])

# 9. Hotspot code
code_slide("MikroTik — Commandes Hotspot (RouterOS)", """# Créer le profil hotspot
/ip hotspot profile add name="ucac-icam-profile" \\
    hotspot-address=10.242.18.6 \\
    dns-name="wifi.ucac-icam.cm" \\
    html-directory=hotspot \\
    use-radius=yes \\
    radius-accounting=yes \\
    radius-interim-update=5m \\
    login-by=http-chap,http-pap

# Activer le hotspot sur l'interface
/ip hotspot add name=hotspot1 interface=bridge-LAN \\
    profile="ucac-icam-profile" \\
    address-pool=dhcp-pool disabled=no

# Walled Garden (pages accessibles sans authentification)
/ip hotspot walled-garden add dst-host=10.242.18.X action=allow
/ip hotspot walled-garden ip add dst-address=10.242.18.X action=accept""",
    "Le hotspot crée automatiquement des règles firewall, NAT et des queues pour le contrôle de bande passante.")

# 10. Hotspot rules auto
content_slide("MikroTik — Règles Créées Automatiquement par le Hotspot", [
    "Quand le hotspot est activé, MikroTik crée automatiquement :",
    "",
    "Règles NAT (Firewall) :",
    ("Redirection HTTP (port 80) → page de login du hotspot", 1),
    ("Redirection HTTPS (port 443) → page de login sécurisée", 1),
    ("Masquerade pour le trafic des clients authentifiés", 1),
    "",
    "Règles Filter (Firewall) :",
    ("Blocage du trafic des clients non authentifiés", 1),
    ("Autorisation du trafic des clients authentifiés", 1),
    ("Autorisation du trafic vers le Walled Garden", 1),
    "",
    "Queues (Contrôle de bande passante) :",
    ("Queue dynamique créée par client authentifié", 1),
    ("Limites appliquées via l'attribut RADIUS Mikrotik-Rate-Limit", 1),
    ("Exemple : 5M upload / 10M download par utilisateur", 1),
    "",
    "Pages HTML du hotspot :",
    ("login.html, logout.html, status.html, alogin.html — personnalisées UCAC-ICAM", 1),
])

# 11. NAT
content_slide("MikroTik — NAT (Masquerade)", [
    "Qu'est-ce que le NAT Masquerade ?",
    ("Technique qui permet aux clients du réseau local (IP privée) d'accéder à Internet", 1),
    ("Le routeur remplace l'adresse IP source privée par son adresse IP publique (WAN)", 1),
    ("Les réponses sont automatiquement retransmises au bon client", 1),
    "",
    "Configuration :",
    ("Chain : srcnat (trafic sortant)", 1),
    ("Interface de sortie : ether1-WAN", 1),
    ("Action : masquerade", 1),
    "",
    "Commande RouterOS :",
    ("/ip firewall nat add chain=srcnat out-interface=ether1-WAN action=masquerade", 1),
    "",
    "Pourquoi c'est nécessaire ?",
    ("Sans NAT, les clients en 10.242.18.x ne peuvent pas atteindre Internet", 1),
    ("Le masquerade est la forme la plus simple de NAT pour un accès Internet partagé", 1),
    "",
    "Note : Le hotspot ajoute aussi ses propres règles NAT pour la redirection captive",
])

# 12. Sécurité
content_slide("MikroTik — Sécurité et Contrôle d'Accès", [
    "Configuration DNS (blocage de sites) :",
    ("Serveur DNS local activé (allow-remote-requests=yes)", 1),
    ("DNS upstream : 8.8.8.8 et 1.1.1.1 (Google + Cloudflare)", 1),
    ("Cache DNS : 4096 KiB", 1),
    "",
    "Blocage de sites par DNS statique :",
    ("Entrées DNS statiques pointant vers 0.0.0.0", 1),
    ("Support des expressions régulières (wildcard)", 1),
    ("Géré automatiquement depuis le backend Django", 1),
    "",
    "Forçage DNS (empêcher le contournement) :",
    ("Redirection de toutes les requêtes DNS (UDP/TCP 53) vers le routeur", 1),
    ("Blocage optionnel de DNS over TLS (port 853)", 1),
    "",
    "API RouterOS :",
    ("Service API activé sur le port 8728", 1),
    ("Utilisateur dédié pour l'agent Node.js", 1),
    ("Communication sécurisée entre le backend et le routeur", 1),
])

# 13. DNS code
code_slide("MikroTik — Commandes DNS et Sécurité", """# Configurer le serveur DNS local
/ip dns set allow-remote-requests=yes servers=8.8.8.8,1.1.1.1 cache-size=4096KiB

# Bloquer un domaine (redirection vers 0.0.0.0)
/ip dns static add name="facebook.com" address=0.0.0.0 comment="captive-portal-block:1"
/ip dns static add name="www.facebook.com" address=0.0.0.0 comment="captive-portal-block:1"

# Bloquer avec wildcard (regex)
/ip dns static add regexp=".*\\.tiktok\\.com$" address=0.0.0.0 comment="captive-portal-block:2"

# Forcer l'utilisation du DNS local (empêcher contournement)
/ip firewall nat add chain=dstnat protocol=udp dst-port=53 \\
    in-interface=bridge-LAN action=redirect to-ports=53
/ip firewall nat add chain=dstnat protocol=tcp dst-port=53 \\
    in-interface=bridge-LAN action=redirect to-ports=53

# Bloquer DNS over TLS
/ip firewall filter add chain=forward protocol=tcp dst-port=853 \\
    in-interface=bridge-LAN action=drop comment="Block DoT" """)

# 14. Tests hotspot
content_slide("MikroTik — Tests de Fonctionnement du Hotspot", [
    "Test 1 : Redirection captive",
    ("Le client connecté au WiFi est automatiquement redirigé vers la page de login", 1),
    ("URL : http://wifi.ucac-icam.cm/login", 1),
    "",
    "Test 2 : Authentification RADIUS",
    ("L'utilisateur entre ses identifiants sur la page de login", 1),
    ("MikroTik envoie une requête Access-Request au serveur FreeRADIUS", 1),
    ("FreeRADIUS répond Access-Accept ou Access-Reject", 1),
    "",
    "Test 3 : Accès Internet après authentification",
    ("Après login réussi, le client peut naviguer sur Internet", 1),
    ("Les limites de bande passante sont appliquées (ex: 5M/10M)", 1),
    "",
    "Test 4 : Comptabilité des sessions (Accounting)",
    ("MikroTik envoie les données de session (durée, octets) toutes les 5 min", 1),
    ("Les sessions sont enregistrées dans la table radacct", 1),
    "",
    "Test 5 : Blocage DNS",
    ("nslookup facebook.com → 0.0.0.0 (site bloqué)", 1),
])

# 15. Section 2 - Machine Cliente
section_slide(2, "Machine Cliente")

# 16. Machine cliente
two_col_slide(
    "Machine Cliente — Connexion et Tests",
    "Mode de Connexion",
    [
        "• Connexion WiFi au réseau UCAC-ICAM",
        "• Attribution IP automatique via DHCP",
        "",
        "Adresse IP reçue :",
        "  → Plage : 10.242.18.100 à .200",
        "  → Passerelle : 10.242.18.6",
        "  → DNS : 10.242.18.6",
        "",
        "Rôle dans le test :",
        "  → Valider le fonctionnement du hotspot",
        "  → Vérifier la redirection captive",
        "  → Tester l'authentification RADIUS",
        "  → Vérifier le contrôle de bande passante",
    ],
    "Tests Réalisés",
    [
        "1. Test DHCP :",
        "   ipconfig → IP dans 10.242.18.100-200",
        "",
        "2. Test de redirection captive :",
        "   Ouvrir navigateur → page de login",
        "",
        "3. Test d'authentification :",
        "   Login avec credentials → accès Internet",
        "",
        "4. Test de ping :",
        "   ping 10.242.18.6 → réponse OK",
        "   ping 8.8.8.8 → réponse OK (après auth)",
        "",
        "5. Test de blocage DNS :",
        "   nslookup facebook.com → 0.0.0.0",
    ]
)

# 17. Section 3 - FreeRADIUS
section_slide(3, "Configuration FreeRADIUS")

# 18. FreeRADIUS rôle
content_slide("FreeRADIUS — Rôle dans l'Architecture", [
    "Qu'est-ce que FreeRADIUS ?",
    ("Serveur AAA (Authentication, Authorization, Accounting)", 1),
    ("Protocole RADIUS standard (RFC 2865 / RFC 2866)", 1),
    ("Version utilisée : FreeRADIUS 3.0", 1),
    "",
    "Authentication (Authentification) :",
    ("Vérifie l'identité de l'utilisateur (username + password)", 1),
    ("Consulte la table radcheck dans PostgreSQL", 1),
    ("Vérifie aussi le champ statut (actif/désactivé)", 1),
    "",
    "Authorization (Autorisation) :",
    ("Détermine les droits de l'utilisateur (bande passante, durée de session)", 1),
    ("Retourne les attributs depuis radreply et radgroupreply", 1),
    ("Exemple : Mikrotik-Rate-Limit = 5M/10M, Session-Timeout = 28800", 1),
    "",
    "Accounting (Comptabilité) :",
    ("Enregistre les sessions : début, durée, octets transférés", 1),
    ("Table radacct mise à jour à chaque événement (Start, Interim, Stop)", 1),
    ("Permet le suivi des quotas et la facturation", 1),
])

# 19. FreeRADIUS fichiers
content_slide("FreeRADIUS — Fichiers de Configuration Modifiés", [
    "1. /etc/freeradius/3.0/clients.conf",
    ("Définit le MikroTik comme client RADIUS autorisé", 1),
    ("IP : 10.242.18.6  |  Secret partagé  |  nastype : other", 1),
    "",
    "2. /etc/freeradius/3.0/mods-available/sql → mods-enabled/sql",
    ("Driver : rlm_sql_postgresql (PostgreSQL)", 1),
    ("Connexion : localhost:5432 / captive_portal", 1),
    ("Tables : radcheck, radreply, radusergroup, radgroupreply, radacct, radpostauth", 1),
    ("Pool de connexions : min=4, max=32, idle_timeout=60s", 1),
    "",
    "3. /etc/freeradius/3.0/sites-available/default",
    ("Écoute : port 1812 (auth) et 1813 (acct)", 1),
    ("Section authorize : sql → pap (vérification mot de passe)", 1),
    ("Section authenticate : PAP et CHAP supportés", 1),
    ("Section post-auth : log dans radpostauth via sql", 1),
    ("Section accounting : enregistrement dans radacct via sql", 1),
    "",
    "4. /etc/freeradius/3.0/dictionary.mikrotik",
    ("Attributs vendor-specific MikroTik (Vendor ID : 14988)", 1),
    ("Mikrotik-Rate-Limit (ID 8), Mikrotik-Recv-Limit, Mikrotik-Total-Limit...", 1),
])

# 20. FreeRADIUS clients.conf code
code_slide("FreeRADIUS — clients.conf", """# /etc/freeradius/3.0/clients.conf

# Client MikroTik (routeur hotspot)
client mikrotik-hotspot {
    ipaddr = 10.242.18.6
    secret = "votre_secret_radius"
    shortname = mikrotik
    nastype = other

    limit {
        max_connections = 16
        lifetime = 0
        idle_timeout = 30
    }
}

# Client localhost (pour les tests avec radtest)
client localhost {
    ipaddr = 127.0.0.1
    secret = testing123
}""",
    "Le secret RADIUS doit correspondre exactement à celui configuré dans MikroTik (/radius add secret=...)")

# 21. FreeRADIUS SQL config
code_slide("FreeRADIUS — Configuration SQL (mods-enabled/sql)", """# /etc/freeradius/3.0/mods-available/sql
sql {
    driver = "rlm_sql_postgresql"
    dialect = "postgresql"

    server = "localhost"
    port = 5432
    login = "radius_user"
    password = "radius_password"
    radius_db = "captive_portal"

    read_clients = yes

    # Tables RADIUS
    acct_table1 = "radacct"
    authcheck_table = "radcheck"
    groupcheck_table = "radgroupcheck"
    authreply_table = "radreply"
    groupreply_table = "radgroupreply"
    usergroup_table = "radusergroup"
    postauth_table = "radpostauth"

    pool {
        start = 5
        min = 4
        max = 32
        spare = 3
        idle_timeout = 60
    }
}

# Activation : ln -s mods-available/sql mods-enabled/sql""")

# 22. Auth method
content_slide("FreeRADIUS — Méthode d'Authentification", [
    "Flux d'authentification détaillé :",
    "",
    "1. Le MikroTik reçoit les credentials de l'utilisateur",
    ("Via la page de login hotspot (HTTP-CHAP ou HTTP-PAP)", 1),
    "",
    "2. MikroTik envoie un paquet Access-Request au FreeRADIUS",
    ("Contient : User-Name, User-Password, NAS-IP-Address, Calling-Station-Id (MAC)", 1),
    ("Protocole : UDP, port 1812", 1),
    "",
    "3. FreeRADIUS exécute la section authorize",
    ("Requête SQL : SELECT * FROM radcheck WHERE username = ? AND statut = true", 1),
    ("Récupère le mot de passe en clair (Cleartext-Password)", 1),
    "",
    "4. FreeRADIUS exécute la section authenticate",
    ("Comparaison du mot de passe (PAP : clair, CHAP : hash MD5)", 1),
    "",
    "5. Si authentification réussie → Access-Accept",
    ("Attributs retournés : Mikrotik-Rate-Limit, Session-Timeout, Idle-Timeout", 1),
    "",
    "6. Si échec → Access-Reject",
    ("Log dans radpostauth (reply = 'Access-Reject')", 1),
])

# 23. Communication MikroTik
content_slide("FreeRADIUS — Communication avec MikroTik", [
    "Protocole de communication : RADIUS (UDP)",
    "",
    "Ports utilisés :",
    ("1812 — Authentification (Access-Request / Access-Accept / Access-Reject)", 1),
    ("1813 — Accounting (Accounting-Request / Accounting-Response)", 1),
    "",
    "Secret partagé :",
    ("Clé secrète identique configurée sur MikroTik et FreeRADIUS", 1),
    ("Utilisée pour chiffrer/vérifier les échanges RADIUS", 1),
    "",
    "Configuration côté MikroTik :",
    ("/radius add address=<IP_serveur> secret=<secret> service=hotspot timeout=3s", 1),
    "",
    "Configuration côté FreeRADIUS :",
    ("client mikrotik-hotspot { ipaddr=10.242.18.6 ; secret=<secret> }", 1),
    "",
    "Attributs vendor-specific MikroTik (Vendor ID 14988) :",
    ("Mikrotik-Rate-Limit (att. 8) : contrôle de bande passante (ex: 5M/10M)", 1),
    ("Mikrotik-Total-Limit (att. 17) : quota total en octets", 1),
    ("Mikrotik-Recv-Limit / Mikrotik-Xmit-Limit : limites download/upload", 1),
])

# 24. Logs FreeRADIUS
content_slide("FreeRADIUS — Logs et Vérifications", [
    "Test d'authentification avec radtest :",
    ("radtest jean.dupont motdepasse123 localhost 0 testing123", 1),
    ("Résultat attendu : Access-Accept avec Mikrotik-Rate-Limit, Session-Timeout", 1),
    "",
    "Mode debug (pour diagnostic) :",
    ("sudo freeradius -X → lance FreeRADIUS en mode debug", 1),
    ("Affiche chaque étape : authorize, authenticate, post-auth", 1),
    "",
    "Logs dans la base de données :",
    ("Table radpostauth : chaque tentative d'authentification (succès/rejet + date)", 1),
    ("Table radacct : chaque session (début, fin, durée, octets, MAC)", 1),
    "",
    "Vérifications supplémentaires :",
    ("sudo systemctl status freeradius → état du service", 1),
    ("SELECT * FROM radpostauth ORDER BY authdate DESC LIMIT 10 → dernières auth", 1),
    ("SELECT * FROM radacct WHERE acctstoptime IS NULL → sessions actives", 1),
    "",
    "Gestion du service :",
    ("sudo systemctl start/stop/restart freeradius", 1),
    ("sudo systemctl enable freeradius → démarrage automatique", 1),
])

# 25. Section 4 - PostgreSQL
section_slide(4, "Configuration PostgreSQL")

# 26. PostgreSQL overview
content_slide("PostgreSQL — Base de Données et Tables", [
    "Base de données : captive_portal",
    ("Utilisateur : radius_user (accès FreeRADIUS + Django)", 1),
    ("Version : PostgreSQL 15", 1),
    "",
    "Tables RADIUS (utilisées directement par FreeRADIUS) :",
    ("radcheck — Authentification (username, password, statut, quota)", 1),
    ("radreply — Attributs de réponse individuels (Rate-Limit, Timeout)", 1),
    ("radusergroup — Association utilisateur → groupe (profil)", 1),
    ("radgroupcheck — Attributs de vérification par groupe (Simultaneous-Use)", 1),
    ("radgroupreply — Attributs de réponse par groupe (Rate-Limit, Timeout)", 1),
    ("radacct — Comptabilité des sessions (durée, octets, MAC, IP)", 1),
    ("radpostauth — Journal des authentifications (succès/rejet)", 1),
    "",
    "Tables Django (gestion applicative) :",
    ("core_user — Utilisateurs du portail (extends AbstractUser)", 1),
    ("core_profile — Profils de connexion (quotas, bande passante)", 1),
    ("core_promotion — Groupes d'utilisateurs (classes, départements)", 1),
    ("core_session, core_device, core_voucher, core_userquota...", 1),
])

# 27. Tables RADIUS code
code_slide("PostgreSQL — Structure des Tables RADIUS", """-- Table radcheck : Authentification des utilisateurs
CREATE TABLE radcheck (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    attribute VARCHAR(64) NOT NULL,        -- ex: 'Cleartext-Password'
    op VARCHAR(2) DEFAULT ':=',
    value VARCHAR(253) NOT NULL,           -- ex: 'motdepasse123'
    statut BOOLEAN DEFAULT TRUE,           -- Extension: actif/désactivé
    quota BIGINT                           -- Extension: quota en octets
);

-- Table radreply : Attributs retournés après authentification
CREATE TABLE radreply (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    attribute VARCHAR(64) NOT NULL,        -- ex: 'Session-Timeout'
    op VARCHAR(2) DEFAULT '=',
    value VARCHAR(253) NOT NULL            -- ex: '28800'
);

-- Table radacct : Comptabilité des sessions
CREATE TABLE radacct (
    radacctid BIGSERIAL PRIMARY KEY,
    username VARCHAR(64), nasipaddress VARCHAR(15),
    acctstarttime TIMESTAMP, acctstoptime TIMESTAMP,
    acctsessiontime INTEGER,               -- durée en secondes
    acctinputoctets BIGINT,                -- octets reçus
    acctoutputoctets BIGINT,               -- octets envoyés
    callingstationid VARCHAR(50),          -- adresse MAC client
    framedipaddress VARCHAR(15)            -- IP attribuée
);""")

# 28. Lien FreeRADIUS - PostgreSQL
content_slide("PostgreSQL — Lien FreeRADIUS ↔ PostgreSQL", [
    "Comment FreeRADIUS utilise PostgreSQL ?",
    "",
    "Phase Authorize (vérification) :",
    ("SELECT username, attribute, value, op FROM radcheck WHERE username = ?", 1),
    ("Vérifie : statut = true ET mot de passe correct", 1),
    ("Récupère aussi les attributs du groupe via radusergroup + radgroupreply", 1),
    "",
    "Phase Post-Auth (journalisation) :",
    ("INSERT INTO radpostauth (username, pass, reply, authdate) VALUES (...)", 1),
    ("Enregistre chaque tentative d'authentification (succès ou rejet)", 1),
    "",
    "Phase Accounting (comptabilité) :",
    ("Start : INSERT INTO radacct (...) — nouvelle session", 1),
    ("Interim : UPDATE radacct SET acctinputoctets=..., acctupdatetime=... — mise à jour", 1),
    ("Stop : UPDATE radacct SET acctstoptime=..., acctterminatecause=... — fin de session", 1),
    "",
    "Synchronisation Django → RADIUS :",
    ("Quand un admin active un utilisateur, Django crée les entrées dans radcheck + radreply + radusergroup", 1),
    ("Quand un profil est modifié, Django met à jour radgroupreply et radgroupcheck", 1),
    ("Système de retry automatique en cas d'échec de synchronisation", 1),
])

# 29. Exemple données
code_slide("PostgreSQL — Exemple de Données RADIUS", """-- Créer un groupe/profil (Étudiant : 5M upload, 10M download, 8h session)
INSERT INTO radgroupreply (groupname, attribute, op, value) VALUES
    ('profile_1_etudiant', 'Mikrotik-Rate-Limit', ':=', '5M/10M'),
    ('profile_1_etudiant', 'Session-Timeout', ':=', '28800'),
    ('profile_1_etudiant', 'Idle-Timeout', ':=', '600');

INSERT INTO radgroupcheck (groupname, attribute, op, value) VALUES
    ('profile_1_etudiant', 'Simultaneous-Use', ':=', '1');

-- Créer un utilisateur
INSERT INTO radcheck (username, attribute, op, value, statut) VALUES
    ('jean.dupont', 'Cleartext-Password', ':=', 'motdepasse123', true);

-- Associer l'utilisateur au profil
INSERT INTO radusergroup (username, groupname, priority) VALUES
    ('jean.dupont', 'profile_1_etudiant', 5);

-- Vérifier (test)
SELECT rc.username, rc.value as password, rc.statut,
       rug.groupname, rgr.attribute, rgr.value
FROM radcheck rc
JOIN radusergroup rug ON rc.username = rug.username
JOIN radgroupreply rgr ON rug.groupname = rgr.groupname
WHERE rc.username = 'jean.dupont';""")

# 30. Flux complet
content_slide("Flux d'Authentification Complet (Récapitulatif)", [
    "1. Le client WiFi se connecte au réseau → reçoit une IP via DHCP (10.242.18.x)",
    "",
    "2. Le client ouvre un navigateur → redirection automatique vers la page de login",
    ("MikroTik intercepte le trafic HTTP et redirige vers wifi.ucac-icam.cm/login", 1),
    "",
    "3. L'utilisateur entre son nom d'utilisateur et son mot de passe",
    "",
    "4. MikroTik envoie un Access-Request (RADIUS, UDP 1812) à FreeRADIUS",
    ("Contient : User-Name, User-Password, NAS-IP, Calling-Station-Id (MAC)", 1),
    "",
    "5. FreeRADIUS interroge PostgreSQL (table radcheck)",
    ("Vérifie : utilisateur existe, statut=true, mot de passe correct", 1),
    "",
    "6. FreeRADIUS retourne Access-Accept avec les attributs QoS",
    ("Mikrotik-Rate-Limit=5M/10M, Session-Timeout=28800, Idle-Timeout=600", 1),
    "",
    "7. MikroTik autorise le client et applique les restrictions",
    "",
    "8. Accounting : MikroTik envoie les données de session toutes les 5 min",
    ("Stockées dans radacct → synchronisées avec Django → vérification des quotas", 1),
])

# 31. Conclusion
content_slide("Conclusion", [
    "Ce projet implémente un portail captif WiFi complet et professionnel :",
    "",
    "MikroTik :",
    ("Gère le hotspot, le DHCP, le NAT, le DNS et le contrôle d'accès", 1),
    ("Communique avec FreeRADIUS pour l'authentification et l'accounting", 1),
    "",
    "FreeRADIUS :",
    ("Serveur AAA central qui authentifie les utilisateurs via PostgreSQL", 1),
    ("Retourne les attributs QoS (bande passante, durée de session)", 1),
    "",
    "PostgreSQL :",
    ("Stocke les utilisateurs, les profils, les sessions et les quotas", 1),
    ("Partagé entre FreeRADIUS (tables rad*) et Django (tables core_*)", 1),
    "",
    "Django + Vue.js :",
    ("Interface d'administration complète pour gérer utilisateurs, profils et promotions", 1),
    ("Synchronisation automatique avec FreeRADIUS et MikroTik", 1),
    "",
    "Résultat : Un système sécurisé, évolutif et adapté au contexte universitaire UCAC-ICAM",
])

# 32. Résumé final
s_final = title_slide(
    "Résumé Final",
    "Architecture : MikroTik ↔ FreeRADIUS ↔ PostgreSQL ↔ Django"
)
txF = s_final.shapes.add_textbox(Inches(1.5), Inches(4.5), Inches(10.333), Inches(2.5))
tf = txF.text_frame; tf.word_wrap = True
items = [
    "MikroTik : Hotspot + NAT + DHCP + DNS + Client RADIUS",
    "FreeRADIUS : Authentification AAA (PAP/CHAP) via SQL",
    "PostgreSQL : Tables radcheck, radreply, radacct, radusergroup + Django ORM",
    "Django : API REST, gestion des profils/quotas, synchronisation RADIUS",
    "Vue.js : Dashboard d'administration temps réel",
]
for i, item in enumerate(items):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.text = "▸  " + item
    p.font.size = Pt(16)
    p.font.color.rgb = RGBColor(0xBF, 0xDB, 0xFE)
    p.alignment = PP_ALIGN.CENTER
    p.space_before = Pt(8)

# 33. Merci
s_end = title_slide("Merci pour votre attention", "Questions ?")
txE = s_end.shapes.add_textbox(Inches(3), Inches(5), Inches(7.333), Inches(1))
tf = txE.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Portail Captif WiFi — UCAC-ICAM — Janvier 2026"
p.font.size = Pt(14)
p.font.color.rgb = GRAY
p.alignment = PP_ALIGN.CENTER

# Save
output_path = "/home/user/captive-portal/Presentation_Portail_Captif_UCAC_ICAM.pptx"
prs.save(output_path)
print(f"Presentation saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
