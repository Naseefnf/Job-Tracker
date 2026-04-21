import streamlit as st
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Job Tracker",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Global */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #0f1117;
            color: #e8eaf0;
        }
        [data-testid="stAppViewContainer"] > .main {
            padding-top: 1rem;
        }
        /* Header */
        .app-header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 0.6rem 0 1.2rem 0;
            border-bottom: 1px solid #2a2d3a;
            margin-bottom: 1.2rem;
        }
        .app-header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: #e8eaf0;
            margin: 0;
            letter-spacing: -0.02em;
        }
        .app-header .badge {
            font-size: 0.72rem;
            background: #1e3a5f;
            color: #60a5fa;
            border: 1px solid #2563eb44;
            border-radius: 20px;
            padding: 2px 10px;
            font-weight: 600;
        }
        /* Tabs */
        [data-testid="stTabs"] [role="tablist"] {
            gap: 4px;
            border-bottom: 1px solid #2a2d3a;
        }
        [data-testid="stTabs"] [role="tab"] {
            background: transparent;
            color: #8b90a0;
            border: none;
            border-bottom: 2px solid transparent;
            border-radius: 0;
            padding: 8px 16px;
            font-size: 0.85rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            color: #60a5fa;
            border-bottom-color: #3b82f6;
            background: transparent;
        }
        /* Buttons */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem;
            transition: all 0.18s;
            border: none;
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
        }
        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(59,130,246,0.35);
        }
        /* Forms */
        [data-testid="stForm"] {
            background: #181b27;
            border: 1px solid #2a2d3a;
            border-radius: 12px;
            padding: 1.2rem;
        }
        /* Inputs */
        .stTextInput input, .stSelectbox select,
        .stDateInput input, .stTextArea textarea {
            background: #0f1117 !important;
            border: 1px solid #2a2d3a !important;
            border-radius: 8px !important;
            color: #e8eaf0 !important;
        }
        .stTextInput input:focus, .stSelectbox select:focus,
        .stDateInput input:focus, .stTextArea textarea:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 2px rgba(59,130,246,0.18) !important;
        }
        /* Metric cards */
        [data-testid="metric-container"] {
            background: #181b27;
            border: 1px solid #2a2d3a;
            border-radius: 12px;
            padding: 1rem;
        }
        /* DataFrame */
        [data-testid="stDataFrame"] {
            border: 1px solid #2a2d3a;
            border-radius: 10px;
            overflow-x: auto;
        }
        /* Radio */
        [data-testid="stRadio"] > div {
            gap: 8px;
        }
        /* Section label */
        .section-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: #8b90a0;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.5rem;
        }
        /* Status chips in form */
        .stSelectbox [data-baseweb="select"] > div {
            background: #0f1117 !important;
            border-color: #2a2d3a !important;
        }
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            [data-testid="stAppViewContainer"] > .main {
                padding: 0.5rem 0.6rem !important;
            }
            .app-header h1 { font-size: 1.2rem; }
            .stButton > button { width: 100% !important; }
            [data-testid="stDataFrame"] { font-size: 0.78rem; }
            [data-testid="stTabs"] [role="tab"] {
                padding: 6px 10px;
                font-size: 0.78rem;
            }
            .block-container { padding: 0.5rem !important; }
        }
        /* Scrollable dataframe wrapper */
        .dataframe-wrapper {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        /* Delete button danger styling */
        .danger-btn button {
            background: #1f0a0a !important;
            color: #f87171 !important;
            border: 1px solid #7f1d1d !important;
        }
        .danger-btn button:hover {
            background: #7f1d1d !important;
            color: white !important;
        }
        /* Info box */
        .info-pill {
            display: inline-block;
            background: #0c1a2e;
            border: 1px solid #1e3a5f;
            color: #60a5fa;
            border-radius: 20px;
            padding: 3px 12px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 0.8rem;
        }
        /* Chart background */
        .chart-container {
            background: #181b27;
            border: 1px solid #2a2d3a;
            border-radius: 12px;
            padding: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Constants ──────────────────────────────────────────────────────────────────
DB_PATH = "job_tracker.db"
STATUSES = ["Applied", "Phone Screen", "Technical", "Final Interview", "Offer", "Rejected"]
STAGES   = ["None", "Applied", "Phone Screen", "Technical", "Final Interview", "Offer", "Rejected"]
STAGE_COLORS = {
    "Applied":         "#6c757d",
    "Phone Screen":    "#007bff",
    "Technical":       "#ffc107",
    "Final Interview": "#fd7e14",
    "Offer":           "#28a745",
    "Rejected":        "#dc3545",
}

# ── Database helpers ───────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            company          TEXT NOT NULL,
            title            TEXT NOT NULL,
            date_applied     TEXT,
            next_appt_date   TEXT,
            salary_range     TEXT,
            location         TEXT,
            contact_name     TEXT,
            contact_email    TEXT,
            jd_link          TEXT,
            resume_link      TEXT,
            interview_stage  TEXT,
            status           TEXT,
            date_updated     TEXT,
            is_archived      INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    # Migration: add next_appt_date if missing
    cols = [r[1] for r in conn.execute("PRAGMA table_info(applications)").fetchall()]
    if "next_appt_date" not in cols:
        conn.execute("ALTER TABLE applications ADD COLUMN next_appt_date TEXT")
        conn.commit()

def auto_archive(conn):
    cutoff = (date.today() - timedelta(days=30)).isoformat()
    conn.execute(
        """
        UPDATE applications
        SET is_archived = 1
        WHERE status = 'Rejected'
          AND date_updated <= ?
          AND is_archived = 0
        """,
        (cutoff,),
    )
    conn.commit()

def fetch_active(conn) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT * FROM applications WHERE is_archived = 0 ORDER BY id DESC",
        conn,
    )
    return df

def fetch_one(conn, app_id: int) -> dict:
    row = conn.execute(
        "SELECT * FROM applications WHERE id = ?", (app_id,)
    ).fetchone()
    return dict(row) if row else {}

def insert_app(conn, data: dict):
    conn.execute(
        """
        INSERT INTO applications
          (company, title, date_applied, next_appt_date, salary_range, location,
           contact_name, contact_email, jd_link, resume_link,
           interview_stage, status, date_updated, is_archived)
        VALUES
          (:company, :title, :date_applied, :next_appt_date, :salary_range, :location,
           :contact_name, :contact_email, :jd_link, :resume_link,
           :interview_stage, :status, :date_updated, 0)
        """,
        data,
    )
    conn.commit()

def update_app(conn, data: dict):
    conn.execute(
        """
        UPDATE applications SET
            company         = :company,
            title           = :title,
            date_applied    = :date_applied,
            next_appt_date  = :next_appt_date,
            salary_range    = :salary_range,
            location        = :location,
            contact_name    = :contact_name,
            contact_email   = :contact_email,
            jd_link         = :jd_link,
            resume_link     = :resume_link,
            interview_stage = :interview_stage,
            status          = :status,
            date_updated    = :date_updated
        WHERE id = :id
        """,
        data,
    )
    conn.commit()

def delete_app(conn, app_id: int):
    conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    conn.commit()

# ── Utilities ──────────────────────────────────────────────────────────────────
def parse_date(value) -> date | None:
    if value is None or str(value).strip() in ("", "None", "NaT", "nan"):
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None

def safe_index(lst, val, default=0):
    try:
        return lst.index(val)
    except (ValueError, TypeError):
        return default

# ── Bootstrap ──────────────────────────────────────────────────────────────────
conn = get_conn()
init_db(conn)
auto_archive(conn)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="app-header">
        <span style="font-size:1.8rem">💼</span>
        <h1>Job Application Tracker</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Applications", "✍️ Add / Edit", "📊 Dashboard"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – Applications view
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    df_all = fetch_active(conn)

    if df_all.empty:
        st.info("No active applications yet. Head to **Add / Edit** to add your first one!")
    else:
        # Metrics row
        total   = len(df_all)
        offers  = int((df_all["status"] == "Offer").sum())
        pending = int(df_all["status"].isin(["Phone Screen", "Technical", "Final Interview"]).sum())
        upcoming = 0
        if "next_appt_date" in df_all.columns:
            today_str = date.today().isoformat()
            upcoming = int(
                df_all["next_appt_date"]
                .dropna()
                .apply(lambda x: x >= today_str if isinstance(x, str) and x else False)
                .sum()
            )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Active", total)
        c2.metric("Offers", offers)
        c3.metric("In Progress", pending)
        c4.metric("Upcoming Appointments", upcoming)

        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)

        # Column display order
        display_cols = [
            c for c in [
                "company", "title", "status", "next_appt_date",
                "date_applied", "interview_stage", "salary_range", "location",
            ]
            if c in df_all.columns
        ]

        col_cfg = {
            "date_applied":   st.column_config.DateColumn("Applied",     format="MMM D, YYYY"),
            "next_appt_date": st.column_config.DateColumn("Next Appt",   format="MMM D, YYYY"),
            "company":        st.column_config.TextColumn("Company"),
            "title":          st.column_config.TextColumn("Role"),
            "status":         st.column_config.TextColumn("Status"),
            "interview_stage":st.column_config.TextColumn("Stage"),
            "salary_range":   st.column_config.TextColumn("Salary"),
            "location":       st.column_config.TextColumn("Location"),
        }

        st.dataframe(
            df_all[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config=col_cfg,
        )

        st.caption(f"Showing {total} active application(s). Rejected entries older than 30 days are auto-archived.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – Add / Edit
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    mode = st.radio(
        "Mode",
        ["➕ Add New Application", "✏️ Update Existing Application"],
        horizontal=True,
        label_visibility="collapsed",
    )

    # ── ADD MODE ──────────────────────────────────────────────────────────────
    if mode == "➕ Add New Application":
        st.markdown("<div class='info-pill'>New Application</div>", unsafe_allow_html=True)

        with st.form("add_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                company       = st.text_input("Company *", placeholder="e.g. Google")
                title         = st.text_input("Job Title *", placeholder="e.g. ML Engineer")
                date_applied  = st.date_input("Date Applied", value=date.today())
                next_appt_date= st.date_input("Next Appointment Date", value=None)
                salary_range  = st.text_input("Salary Range", placeholder="e.g. ₹12–18 LPA")
                location      = st.text_input("Location", placeholder="e.g. Bengaluru / Remote")
            with col_b:
                contact_name  = st.text_input("Contact Name", placeholder="Recruiter name")
                contact_email = st.text_input("Contact Email", placeholder="recruiter@company.com")
                jd_link       = st.text_input("Job Description Link", placeholder="https://...")
                resume_link   = st.text_input("Resume Link", placeholder="https://drive.google.com/...")
                status        = st.selectbox("Status", STATUSES)
                interview_stage = st.selectbox("Interview Stage", STAGES)

            submitted = st.form_submit_button("💾 Save Application", type="primary", use_container_width=True)

        if submitted:
            if not company.strip() or not title.strip():
                st.error("Company and Job Title are required fields.")
            else:
                insert_app(conn, {
                    "company":         company.strip(),
                    "title":           title.strip(),
                    "date_applied":    date_applied.isoformat() if date_applied else None,
                    "next_appt_date":  next_appt_date.isoformat() if next_appt_date else None,
                    "salary_range":    salary_range.strip() or None,
                    "location":        location.strip() or None,
                    "contact_name":    contact_name.strip() or None,
                    "contact_email":   contact_email.strip() or None,
                    "jd_link":         jd_link.strip() or None,
                    "resume_link":     resume_link.strip() or None,
                    "interview_stage": interview_stage if interview_stage != "None" else None,
                    "status":          status,
                    "date_updated":    date.today().isoformat(),
                })
                st.success(f"✅ Application for **{company}** saved successfully!")
                st.rerun()

    # ── EDIT MODE ─────────────────────────────────────────────────────────────
    else:
        df_active = fetch_active(conn)

        if df_active.empty:
            st.info("No active applications to edit.")
        else:
            options = [
                f"{row['id']}: {row['company']} — {row['title']}"
                for _, row in df_active.iterrows()
            ]
            selected = st.selectbox("Select Application", options)
            app_id   = int(selected.split(":")[0])
            rec      = fetch_one(conn, app_id)

            if rec:
                st.markdown("<div class='info-pill'>Editing Application</div>", unsafe_allow_html=True)

                with st.form("edit_form"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        company        = st.text_input("Company *",      value=rec.get("company", ""))
                        title          = st.text_input("Job Title *",     value=rec.get("title", ""))
                        date_applied   = st.date_input("Date Applied",    value=parse_date(rec.get("date_applied")))
                        next_appt_date = st.date_input("Next Appointment Date", value=parse_date(rec.get("next_appt_date")))
                        salary_range   = st.text_input("Salary Range",    value=rec.get("salary_range") or "")
                        location       = st.text_input("Location",        value=rec.get("location") or "")
                    with col_b:
                        contact_name   = st.text_input("Contact Name",    value=rec.get("contact_name") or "")
                        contact_email  = st.text_input("Contact Email",   value=rec.get("contact_email") or "")
                        jd_link        = st.text_input("JD Link",         value=rec.get("jd_link") or "")
                        resume_link    = st.text_input("Resume Link",     value=rec.get("resume_link") or "")
                        status         = st.selectbox(
                            "Status", STATUSES,
                            index=safe_index(STATUSES, rec.get("status"), 0),
                        )
                        interview_stage = st.selectbox(
                            "Interview Stage", STAGES,
                            index=safe_index(STAGES, rec.get("interview_stage"), 0),
                        )

                    update_btn = st.form_submit_button("💾 Update Application", type="primary", use_container_width=True)

                if update_btn:
                    if not company.strip() or not title.strip():
                        st.error("Company and Job Title are required fields.")
                    else:
                        update_app(conn, {
                            "id":             app_id,
                            "company":        company.strip(),
                            "title":          title.strip(),
                            "date_applied":   date_applied.isoformat() if date_applied else None,
                            "next_appt_date": next_appt_date.isoformat() if next_appt_date else None,
                            "salary_range":   salary_range.strip() or None,
                            "location":       location.strip() or None,
                            "contact_name":   contact_name.strip() or None,
                            "contact_email":  contact_email.strip() or None,
                            "jd_link":        jd_link.strip() or None,
                            "resume_link":    resume_link.strip() or None,
                            "interview_stage":interview_stage if interview_stage != "None" else None,
                            "status":         status,
                            "date_updated":   date.today().isoformat(),
                        })
                        st.success("✅ Application updated!")
                        st.rerun()

                # Delete – outside form to avoid accidental triggers
                st.markdown("<div style='margin-top:0.6rem'></div>", unsafe_allow_html=True)
                st.markdown("<div class='danger-btn'>", unsafe_allow_html=True)
                if st.button("🗑️ Delete this Application", use_container_width=True):
                    delete_app(conn, app_id)
                    st.success("Application deleted.")
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – Dashboard
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    df_dash = fetch_active(conn)

    pipeline_order = ["Applied", "Phone Screen", "Technical", "Final Interview", "Offer", "Rejected"]
    hex_colors     = ["#6c757d", "#007bff", "#ffc107", "#fd7e14", "#28a745", "#dc3545"]

    if df_dash.empty:
        st.info("No data yet. Add some applications to see your pipeline dashboard.")
    else:
        counts_raw = df_dash["status"].value_counts().to_dict()
        counts     = {s: counts_raw.get(s, 0) for s in pipeline_order}

        # Metrics summary row
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Applications", len(df_dash))
        col2.metric("Offer Rate", f"{round(counts.get('Offer',0)/max(len(df_dash),1)*100, 1)}%")
        col3.metric("Response Rate",
            f"{round((len(df_dash) - counts.get('Applied',0)) / max(len(df_dash),1)*100, 1)}%"
        )

        st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)

        # ── Funnel chart ──────────────────────────────────────────────────────
        stages = [s for s in pipeline_order if counts[s] > 0 or s in pipeline_order]
        values = [counts[s] for s in stages]
        colors = [hex_colors[pipeline_order.index(s)] for s in stages]

        fig, ax = plt.subplots(figsize=(9, 4.2))
        fig.patch.set_facecolor("#181b27")
        ax.set_facecolor("#181b27")

        bars = ax.barh(stages, values, color=colors, height=0.62, zorder=3)

        # Grid lines
        ax.xaxis.grid(True, color="#2a2d3a", linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "bottom", "left"]].set_visible(False)
        ax.tick_params(colors="#8b90a0", labelsize=10)
        ax.xaxis.label.set_color("#8b90a0")

        # Count labels
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(
                    bar.get_width() + 0.15,
                    bar.get_y() + bar.get_height() / 2,
                    str(val),
                    va="center",
                    ha="left",
                    color="#e8eaf0",
                    fontsize=11,
                    fontweight="bold",
                )

        ax.invert_yaxis()
        ax.set_xlabel("Number of Applications", color="#8b90a0", fontsize=9)
        ax.set_title("Application Pipeline Funnel", color="#e8eaf0", fontsize=13, fontweight="700", pad=14)
        ax.tick_params(axis="y", colors="#e8eaf0", labelsize=10)
        ax.set_xlim(0, max(values) * 1.22 if max(values) > 0 else 5)

        plt.tight_layout(pad=1.2)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        # ── Status breakdown table ─────────────────────────────────────────────
        st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)
        breakdown = pd.DataFrame({
            "Status": stages,
            "Count":  values,
            "Share":  [f"{round(v/max(sum(values),1)*100, 1)}%" for v in values],
        })
        st.dataframe(
            breakdown[breakdown["Count"] > 0],
            use_container_width=True,
            hide_index=True,
        )
