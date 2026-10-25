
import streamlit as st
import pandas as pd
from datetime import datetime
from difflib import SequenceMatcher
import uuid

st.set_page_config(
    page_title="CivicFix | Smart Civic Management",
    page_icon="🏙️",
    layout="wide"
)

# ---------------- CONFIGURATION ----------------

ISSUE_TEAMS = {
    "Pothole": "Road Maintenance",
    "Damaged Footpath": "Footpath Maintenance",
    "Broken Streetlight": "Electrical Team",
    "Overflowing Bin": "Sanitation Team",
}

STATUSES = ["Submitted", "Assigned", "In Progress", "Resolved"]

# ---------------- SESSION STORAGE ----------------

if "reports" not in st.session_state:
    st.session_state.reports = []

reports = st.session_state.reports

# ---------------- HELPER FUNCTIONS ----------------

def classify_issue(text):
    text = text.lower()

    keywords = {
        "Pothole": ["pothole", "road hole", "road damage", "crater"],
        "Damaged Footpath": [
            "footpath", "sidewalk", "pavement", "broken pavement"
        ],
        "Broken Streetlight": [
            "streetlight", "street light", "lamp post", "light not working"
        ],
        "Overflowing Bin": [
            "overflowing bin", "garbage", "trash", "waste", "rubbish"
        ],
    }

    for category, words in keywords.items():
        if any(word in text for word in words):
            return category

    return None

def find_duplicate(category, location, description):
    for report in reports:
        same_category = report["Category"] == category
        same_location = (
            report["Location"].strip().lower()
            == location.strip().lower()
        )
        similarity = SequenceMatcher(
            None,
            report["Description"].lower(),
            description.lower()
        ).ratio()

        if same_category and same_location and similarity >= 0.65:
            return report

    return None

def create_report(category, location, description, photo):
    report_id = "CF-" + uuid.uuid4().hex[:6].upper()

    report = {
        "ID": report_id,
        "Category": category,
        "Location": location.strip(),
        "Description": description.strip(),
        "Team": ISSUE_TEAMS[category],
        "Status": "Submitted",
        "Created": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "Duplicate Count": 0,
        "Photo": photo.getvalue() if photo else None,
    }

    reports.append(report)
    return report

# ---------------- SIDEBAR ----------------

st.sidebar.title("🏙️ CivicFix")
st.sidebar.caption("Smart Civic Issue Management")
st.sidebar.markdown("---")
st.sidebar.write("**Report. Route. Resolve.**")
st.sidebar.info(
    "Help communities report civic issues and track their progress."
)

# ---------------- HEADER ----------------

st.title("🏙️ CivicFix")
st.subheader("A smarter way to resolve local civic problems")
st.write(
    "Classify complaints, flag possible duplicates, assign responsible "
    "teams, and track resolution status."
)

# ---------------- DASHBOARD METRICS ----------------

total = len(reports)
submitted_count = sum(r["Status"] == "Submitted" for r in reports)
progress_count = sum(r["Status"] == "In Progress" for r in reports)
resolved_count = sum(r["Status"] == "Resolved" for r in reports)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Reports", total)
c2.metric("Submitted", submitted_count)
c3.metric("In Progress", progress_count)
c4.metric("Resolved", resolved_count)

st.divider()

# ---------------- MAIN TABS ----------------

report_tab, track_tab, admin_tab = st.tabs(
    ["📝 Report an Issue", "🔍 Track a Report", "🛠️ Admin Dashboard"]
)

# ---------------- REPORT FORM ----------------

with report_tab:
    st.header("Report a Civic Issue")

    with st.form("civic_report_form", clear_on_submit=True):
        description = st.text_area(
            "Describe the problem",
            placeholder=(
                "Example: A large pothole near the main bus stop."
            )
        )

        location = st.text_input(
            "Location",
            placeholder="Street, landmark, or neighbourhood"
        )

        suggested_category = classify_issue(description)

        if suggested_category:
            st.info(f"Suggested classification: {suggested_category}")

        category_options = list(ISSUE_TEAMS.keys())

        if suggested_category:
            default_index = category_options.index(suggested_category)
        else:
            default_index = 0

        category = st.selectbox(
            "Issue category",
            category_options,
            index=default_index
        )

        photo = st.file_uploader(
            "Upload a photo (optional)",
            type=["jpg", "jpeg", "png"]
        )

        submit = st.form_submit_button(
            "Submit Civic Report",
            use_container_width=True
        )

    if submit:
        if not location.strip() or not description.strip():
            st.error("Please provide both a description and a location.")
        else:
            duplicate = find_duplicate(
                category, location, description
            )

            if duplicate:
                duplicate["Duplicate Count"] += 1
                st.warning(
                    f"Possible duplicate detected. Your report has been "
                    f"linked to existing case {duplicate['ID']}."
                )
                st.write(
                    "The existing case remains active, and its duplicate "
                    "count has been updated."
                )
            else:
                new_report = create_report(
                    category, location, description, photo
                )

                st.success(
                    f"Report submitted! Your tracking ID is {new_report['ID']}."
                )
                st.info(
                    f"Responsible team: {new_report['Team']}"
                )

# ---------------- RESIDENT TRACKING ----------------

with track_tab:
    st.header("Track Your Report")

    if reports:
        report_ids = [r["ID"] for r in reports]

        tracking_id = st.selectbox(
            "Select your tracking ID",
            report_ids,
            key="tracking_id"
        )

        report = next(r for r in reports if r["ID"] == tracking_id)

        st.subheader(f"Case {report['ID']}")

        st.write(f"**Issue:** {report['Category']}")
        st.write(f"**Location:** {report['Location']}")
        st.write(f"**Responsible team:** {report['Team']}")
        st.write(f"**Description:** {report['Description']}")
        st.write(f"**Reported on:** {report['Created']}")
        st.write(
            f"**Linked duplicate submissions:** {report['Duplicate Count']}"
        )

        st.markdown("### Resolution progress")

        current_index = STATUSES.index(report["Status"])

        st.progress((current_index + 1) / len(STATUSES))
        st.write(f"**Current status: {report['Status']}**")

        st.caption(
            "Progress shows the current workflow stage, not a measured "
            "percentage of physical work completed."
        )

        if report["Photo"]:
            st.image(report["Photo"], caption="Submitted issue photo")

    else:
        st.info("No reports yet. Submit a civic issue to start tracking.")

# ---------------- ADMIN DASHBOARD ----------------

with admin_tab:
    st.header("Admin & Department Dashboard")

    if reports:
        selected_id = st.selectbox(
            "Choose a case to manage",
            [r["ID"] for r in reports],
            key="admin_case"
        )

        report = next(r for r in reports if r["ID"] == selected_id)

        with st.form("case_update_form"):
            team_options = list(ISSUE_TEAMS.values())

            team_index = (
                team_options.index(report["Team"])
                if report["Team"] in team_options else 0
            )

            assigned_team = st.selectbox(
                "Responsible team",
                team_options,
                index=team_index
            )

            new_status = st.selectbox(
                "Update status",
                STATUSES,
                index=STATUSES.index(report["Status"])
            )

            save = st.form_submit_button("Save Case Updates")

        if save:
            report["Team"] = assigned_team
            report["Status"] = new_status
            st.success("Case updated successfully!")
            st.rerun()

        st.divider()
        st.subheader("All Civic Cases")

        table_rows = [
            {key: value for key, value in r.items() if key != "Photo"}
            for r in reports
        ]

        st.dataframe(
            pd.DataFrame(table_rows),
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Issues by Category")

        category_counts = pd.Series(
            [r["Category"] for r in reports]
        ).value_counts()

        st.bar_chart(category_counts)

    else:
        st.info("Submitted civic reports will appear here.")

# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "CivicFix | Hackathon MVP | Prototype data is held in session memory. "
    "A persistent shared database and authenticated department accounts "
    "are needed for reliable multi-user production use."
)
