"""Tema visual para la interfaz del despacho (garciabermeo.net)."""

from legal_ui.brand import BRAND_NAME

LEXIVOX_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: #f4f6f9;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1220 0%, #111827 100%);
    border-right: 1px solid #1f2937;
}

[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}

[data-testid="stSidebar"] .stButton > button {
    background: #111827;
    border: 1px solid #374151;
    color: #f9fafb !important;
    border-radius: 10px;
    text-align: left;
    width: 100%;
    font-size: 0.82rem;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #1f2937;
    border-color: #4b5563;
}

[data-testid="stSidebar"] [data-testid="stRadio"] {
    background: transparent;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 0.55rem 0.65rem;
    margin-bottom: 0.15rem;
    width: 100%;
    color: #cbd5e1 !important;
    font-size: 0.88rem;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #1f2937;
    border-color: #374151;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],
[data-testid="stSidebar"] [data-testid="stRadio"] div[aria-checked="true"] label {
    background: rgba(59, 130, 246, 0.18) !important;
    border-color: rgba(59, 130, 246, 0.35) !important;
    color: #ffffff !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
    gap: 0.15rem;
}

[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
    display: block;
    background: #111827;
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 0.5rem 0.65rem;
    margin-bottom: 0.35rem;
    text-decoration: none;
    color: #e5e7eb !important;
    font-size: 0.84rem;
}

[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
    background: #1f2937;
    border-color: #4b5563;
}

.lx-brand {
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #f8fafc;
    margin-bottom: 0.15rem;
}

.lx-brand-sub {
    font-size: 0.72rem;
    color: #94a3b8;
    margin-bottom: 1.25rem;
}

.lx-nav-section {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #64748b;
    margin: 1rem 0 0.45rem 0;
}

.lx-nav-item {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.55rem 0.65rem;
    border-radius: 10px;
    color: #cbd5e1;
    font-size: 0.88rem;
    margin-bottom: 0.2rem;
}

.lx-nav-item.active {
    background: rgba(59, 130, 246, 0.18);
    color: #ffffff;
    border: 1px solid rgba(59, 130, 246, 0.35);
}

.lx-header {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}

.lx-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
    letter-spacing: -0.03em;
}

.lx-subtitle {
    color: #64748b;
    font-size: 0.92rem;
    margin-top: 0.35rem;
}

.lx-metric-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 0.75rem;
    margin-bottom: 1rem;
}

.lx-metric {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 0.95rem 1rem;
}

.lx-metric-label {
    font-size: 0.72rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.lx-metric-value {
    font-size: 1.55rem;
    font-weight: 700;
    color: #0f172a;
    margin-top: 0.25rem;
}

.lx-metric-value.warn { color: #dc2626; }
.lx-metric-value.ok { color: #059669; }

.lx-filters {
    display: flex;
    gap: 0.45rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.lx-pill {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    border: 1px solid #dbeafe;
    background: #ffffff;
    color: #334155;
}

.lx-pill.active {
    background: #2563eb;
    color: #ffffff;
    border-color: #2563eb;
}

.lx-panel {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 1rem 1.1rem;
    min-height: 420px;
}

.lx-panel-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.75rem;
}

.lx-case-item {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 0.85rem 0.95rem;
    margin-bottom: 0.55rem;
    cursor: pointer;
    transition: border-color 0.15s ease;
}

.lx-case-item:hover {
    border-color: #93c5fd;
}

.lx-case-item.selected {
    border-color: #2563eb;
    background: #eff6ff;
}

.lx-case-name {
    font-weight: 600;
    color: #0f172a;
    font-size: 0.92rem;
}

.lx-case-meta {
    font-size: 0.76rem;
    color: #64748b;
    margin-top: 0.25rem;
}

.lx-badge {
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
}

.lx-badge.activo { background: #dcfce7; color: #166534; }
.lx-badge.pausado { background: #fef3c7; color: #92400e; }
.lx-badge.cerrado { background: #e2e8f0; color: #334155; }
.lx-badge.archivado { background: #f1f5f9; color: #64748b; }

.lx-empty {
    color: #94a3b8;
    font-size: 0.88rem;
    padding: 2rem 0.5rem;
    text-align: center;
}

.lx-detail-section {
    margin-bottom: 1rem;
}

.lx-detail-section h4 {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    margin-bottom: 0.35rem;
}

.lx-status-bar {
    font-size: 0.72rem;
    color: #64748b;
    margin-top: 1.5rem;
    padding-top: 0.75rem;
    border-top: 1px solid #1f2937;
}

@media (max-width: 1100px) {
    .lx-metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
</style>
"""

STATUS_LABELS = {
    "activo": "Activo",
    "pausado": "Pausado",
    "cerrado": "Cerrado",
    "archivado": "Archivado",
}

TASK_LABELS = {
    "pendiente": "Pendiente",
    "en_curso": "En curso",
    "completada": "Completada",
}

FILTER_OPTIONS = [
    ("todos", "Todos"),
    ("activo", "Activos"),
    ("pausado", "Pausados"),
    ("cerrado", "Cerrados"),
    ("archivado", "Archivados"),
]
