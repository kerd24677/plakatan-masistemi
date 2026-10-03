"""Koyu tema renk paleti ve genel Qt Style Sheet (QSS)."""

COLORS = {
    "bg": "#121418",
    "bg_elevated": "#1A1D23",
    "bg_card": "#1F232B",
    "border": "#2A2F3A",
    "text": "#E6E8EC",
    "text_muted": "#9AA2AF",
    "primary": "#3D8BFD",
    "primary_hover": "#5C9CFF",
    "success": "#2ECC71",
    "warning": "#F5A623",
    "danger": "#E74C3C",
    "sidebar_bg": "#15171C",
    "sidebar_active": "#232833",
}

STATUS_COLORS = {
    "connected": COLORS["success"],
    "connecting": COLORS["warning"],
    "disconnected": COLORS["text_muted"],
    "error": COLORS["danger"],
}

STATUS_LABELS_TR = {
    "connected": "Bağlı",
    "connecting": "Bağlanıyor",
    "disconnected": "Bağlantı Kesildi",
    "error": "Hata",
}

DARK_QSS = f"""
* {{
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
    color: {COLORS["text"]};
}}
QMainWindow, QWidget#centralWidget {{
    background-color: {COLORS["bg"]};
}}
QWidget {{
    background-color: transparent;
}}
#Sidebar {{
    background-color: {COLORS["sidebar_bg"]};
    border-right: 1px solid {COLORS["border"]};
}}
#SidebarButton {{
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    color: {COLORS["text_muted"]};
    background-color: transparent;
    font-size: 13px;
}}
#SidebarButton:hover {{
    background-color: {COLORS["sidebar_active"]};
    color: {COLORS["text"]};
}}
#SidebarButton:checked {{
    background-color: {COLORS["sidebar_active"]};
    color: {COLORS["primary_hover"]};
    font-weight: 600;
    border-left: 3px solid {COLORS["primary"]};
}}
#AppTitle {{
    color: {COLORS["text"]};
    font-size: 16px;
    font-weight: 700;
    padding: 18px 16px 6px 16px;
}}
#AppSubtitle {{
    color: {COLORS["text_muted"]};
    font-size: 11px;
    padding: 0px 16px 16px 16px;
}}
QFrame#Card {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
}}
QLabel#CardTitle {{
    color: {COLORS["text_muted"]};
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
}}
QLabel#CardValue {{
    color: {COLORS["text"]};
    font-size: 26px;
    font-weight: 700;
}}
QLabel#ScreenTitle {{
    font-size: 20px;
    font-weight: 700;
    color: {COLORS["text"]};
}}
QLabel#ScreenSubtitle {{
    color: {COLORS["text_muted"]};
    font-size: 12px;
}}
QPushButton {{
    background-color: {COLORS["primary"]};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {COLORS["primary_hover"]};
}}
QPushButton:disabled {{
    background-color: {COLORS["border"]};
    color: {COLORS["text_muted"]};
}}
QPushButton#SecondaryButton {{
    background-color: {COLORS["bg_elevated"]};
    border: 1px solid {COLORS["border"]};
    color: {COLORS["text"]};
}}
QPushButton#SecondaryButton:hover {{
    background-color: {COLORS["sidebar_active"]};
}}
QPushButton#DangerButton {{
    background-color: {COLORS["danger"]};
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS["bg_elevated"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 6px 8px;
    color: {COLORS["text"]};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {COLORS["primary"]};
}}
QTableWidget {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    gridline-color: {COLORS["border"]};
    selection-background-color: {COLORS["sidebar_active"]};
}}
QHeaderView::section {{
    background-color: {COLORS["bg_elevated"]};
    color: {COLORS["text_muted"]};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {COLORS["border"]};
    font-weight: 600;
}}
QTabWidget::pane {{
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS["border"]};
    border-radius: 5px;
    min-height: 24px;
}}
QToolTip {{
    background-color: {COLORS["bg_elevated"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["border"]};
}}
"""
