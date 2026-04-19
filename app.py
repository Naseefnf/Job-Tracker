import streamlit as st
import sqlite3
import datetime
import pandas as pd
import matplotlib.pyplot as plt

# --- DATABASE SETUP ---
DB_NAME = "job_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            date_applied TEXT,
            next_appt_date TEXT,
            salary_range TEXT,
            location TEXT,
            contact_name TEXT,
            contact_email TEXT,
            jd_link TEXT,
            resume_link TEXT,
            interview_stage TEXT,
            status TEXT,
            date_updated TEXT,
            is_archived INTEGER DEFAULT 0
        )
    ''')
    
    # SMART MIGRATION: Add 'next_appt_date' if updating from an older version
    cursor.execute("PRAGMA table_info(applications)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'next_appt_date' not in columns:
        cursor.execute("ALTER TABLE applications ADD COLUMN next_appt_date TEXT")
        
    conn.commit()
    conn.close()

def auto_archive_rejected():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    threshold_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    cursor.execute('''
        UPDATE applications SET is_archived = 1 
        WHERE status = 'Rejected' AND date_updated <= ? AND is_archived = 0
    ''', (threshold_date,))
    conn.commit()
    conn.close()

init_db()
auto_archive_rejected()

# --- RESPONSIVE CSS INJECTION ---
st.markdown("""
<style>
    /* Make the main container padding responsive */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 2rem !important;
        }
        /* Make buttons full width on mobile */
        div.stButton > button {
            width: 100% !important;
        }
    }
    /* Ensure data table doesn't break layout on mobile */
    .stDataFrame {
        overflow-x: auto !important;
    }
</style>
""", unsafe_allow_html=True)

# --- STREAMLIT UI ---
st.set_page_config(page_title="Job Tracker", layout="wide", initial_sidebar_state="collapsed")
st.title("💼 Job Application Tracker")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📋 Applications", "✍️ Add / Edit", "📊 Dashboard"])

# --- TAB 1: VIEW APPLICATIONS ---
with tab1:
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM applications WHERE is_archived = 0 ORDER BY date_applied DESC", conn)
    conn.close()
    
    if not df.empty:
        # Reordered columns: Most important first for mobile horizontal scrolling
        display_cols = ['company', 'title', 'status', 'next_appt_date', 'date_applied', 'interview_stage', 'salary_range', 'location']
        st.dataframe(
            df[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "next_appt_date": st.column_config.DateColumn("Next Appt. Date"),
                "date_applied": st.column_config.DateColumn("Applied Date"),
            }
        )
    else:
        st.info("No active applications yet. Go to the 'Add / Edit' tab to add one!")

# --- TAB 2: ADD / EDIT APPLICATION ---
with tab2:
    mode = st.radio("Select Mode", ["Add New Application", "Update Existing Application"], horizontal=True)
    
    def parse_date(date_str):
        if date_str:
            try:
                return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return datetime.date.today()
        return datetime.date.today()

    if mode == "Update Existing Application":
        conn = sqlite3.connect(DB_NAME)
        df_edit = pd.read_sql_query("SELECT id, company, title FROM applications WHERE is_archived=0 ORDER BY date_applied DESC", conn)
        conn.close()
        
        if df_edit.empty:
            st.warning("No applications to edit. Add some first!")
        else:
            app_options = [f"ID {row['id']}: {row['company']} - {row['title']}" for _, row in df_edit.iterrows()]
            selected_app = st.selectbox("Select an application to edit", app_options)
            edit_id = int(selected_app.split(" ")[1].replace(":", ""))
            
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications WHERE id=?", (edit_id,))
            row = cursor.fetchone()
            conn.close()
            
            # row indices: 0:id, 1:company, 2:title, 3:date_applied, 4:next_appt_date, 5:salary, 6:location, 
            # 7:contact_name, 8:contact_email, 9:jd_link, 10:resume_link, 11:stage, 12:status, 13:updated, 14:archived
            
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                e_company = st.text_input("Company*", value=row[1] or "")
                e_title = st.text_input("Job Title*", value=row[2] or "")
                e_date_applied = st.date_input("Date Applied", value=parse_date(row[3]))
                e_next_appt = st.date_input("Next Appointment/Follow-up Date", value=parse_date(row[4]))
                e_salary = st.text_input("Salary Range", value=row[5] or "")
                
            with col2:
                e_location = st.text_input("Location / Remote", value=row[6] or "")
                e_contact_name = st.text_input("Recruiter Name", value=row[7] or "")
                e_contact_email = st.text_input("Recruiter Email", value=row[8] or "")
                e_interview_stage = st.text_input("Interview Stage", value=row[11] or "")
                
            status_options = ["Applied", "Phone Screen", "Technical", "Final Interview", "Offer", "Rejected", "Withdrawn"]
            current_status = row[12] or "Applied"
            default_status_idx = status_options.index(current_status) if current_status in status_options else 0
            e_status = st.selectbox("Status", status_options, index=default_status_idx)
                
            e_jd_link = st.text_input("Job Description Link", value=row[9] or "")
            e_resume_link = st.text_input("Resume/Cover Letter Link", value=row[10] or "")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 Update Application", use_container_width=True):
                    if not e_company or not e_title:
                        st.error("Company and Title are required!")
                    else:
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        today = datetime.date.today().strftime('%Y-%m-%d')
                        cursor.execute('''
                            UPDATE applications SET company=?, title=?, date_applied=?, next_appt_date=?, salary_range=?, location=?,
                            contact_name=?, contact_email=?, jd_link=?, resume_link=?, interview_stage=?, status=?, date_updated=?
                            WHERE id=?
                        ''', (e_company, e_title, str(e_date_applied), str(e_next_appt), e_salary, e_location, 
                              e_contact_name, e_contact_email, e_jd_link, e_resume_link, 
                              e_interview_stage, e_status, today, edit_id))
                        conn.commit()
                        conn.close()
                        st.success("Application updated successfully!")
                        st.rerun()
                        
            with col_btn2:
                if st.button("🗑️ Delete this Application", use_container_width=True, type="secondary"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM applications WHERE id=?", (edit_id,))
                    conn.commit()
                    conn.close()
                    st.warning("Application deleted!")
                    st.rerun()

    elif mode == "Add New Application":
        with st.form("job_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                company = st.text_input("Company*")
                title = st.text_input("Job Title*")
                date_applied = st.date_input("Date Applied", datetime.date.today())
                next_appt = st.date_input("Next Appointment/Follow-up Date", value=None)
                salary = st.text_input("Salary Range")
                
            with col2:
                location = st.text_input("Location / Remote")
                contact_name = st.text_input("Recruiter Name")
                contact_email = st.text_input("Recruiter Email")
                interview_stage = st.text_input("Interview Stage")
                status = st.selectbox("Status", ["Applied", "Phone Screen", "Technical", "Final Interview", "Offer", "Rejected", "Withdrawn"])
                
            jd_link = st.text_input("Job Description Link")
            resume_link = st.text_input("Resume/Cover Letter Link")
            
            submitted = st.form_submit_button("➕ Add Application", use_container_width=True)
            if submitted:
                if not company or not title:
                    st.error("Company and Title are required!")
                else:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    today = datetime.date.today().strftime('%Y-%m-%d')
                    
                    # Handle empty next_appt date
                    next_appt_str = str(next_appt) if next_appt else None
                    
                    cursor.execute('''
                        INSERT INTO applications (company, title, date_applied, next_appt_date, salary_range, location, 
                        contact_name, contact_email, jd_link, resume_link, interview_stage, status, date_updated, is_archived)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    ''', (company, title, str(date_applied), next_appt_str, salary, location, contact_name, contact_email, 
                          jd_link, resume_link, interview_stage, status, today))
                    conn.commit()
                    conn.close()
                    st.success("Application added successfully!")
                    st.rerun()

# --- TAB 3: DASHBOARD ---
with tab3:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    stages = ["Applied", "Phone Screen", "Technical", "Final Interview", "Offer", "Rejected"]
    counts = []
    
    for stage in stages:
        cursor.execute("SELECT COUNT(*) FROM applications WHERE status=? AND is_archived=0", (stage,))
        counts.append(cursor.fetchone()[0])
    conn.close()

    fig, ax = plt.subplots()
    y_pos = range(len(stages))
    colors = ['#6c757d', '#007bff', '#ffc107', '#fd7e14', '#28a745', '#dc3545']
    
    ax.barh(y_pos, counts, color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(stages)
    ax.invert_yaxis()
    ax.set_xlabel('Number of Applications')
    ax.set_title('Job Search Pipeline')
    
    for i, v in enumerate(counts):
        ax.text(v + 0.1, i, str(v), color='black', va='center')

    st.pyplot(fig)
