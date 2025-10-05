import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from simple_jira_tools import (
    SimpleJiraTicketTools,
    SimpleJiraProjectTools,
    SimpleJiraEpicTools,
)
from jira_client import JiraAgent
from analytics import JiraAnalytics
from phi_jira_agent_final import get_phi_jira_agent


def initialize_state() -> None:
    if "jira_agent" not in st.session_state:
        st.session_state.jira_agent = JiraAgent()
    if "ticket_tools" not in st.session_state:
        st.session_state.ticket_tools = SimpleJiraTicketTools()
    if "project_tools" not in st.session_state:
        st.session_state.project_tools = SimpleJiraProjectTools()
    if "epic_tools" not in st.session_state:
        st.session_state.epic_tools = SimpleJiraEpicTools()
    if "analytics" not in st.session_state:
        st.session_state.analytics = JiraAnalytics(st.session_state.jira_agent)
    if "chat_agent" not in st.session_state:
        st.session_state.chat_agent = get_phi_jira_agent()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def page_create_ticket() -> None:
    st.subheader("Create Ticket")
    with st.form("create_ticket_form"):
        col1, col2 = st.columns(2)
        with col1:
            project_key = st.text_input("Project Key", placeholder="e.g., FIJI")
            summary = st.text_input("Summary", placeholder="Short title for the ticket")
            description = st.text_area("Description", height=140)
            issue_type = st.selectbox("Issue Type", ["Task", "Bug", "Story", "Epic"], index=0)
            priority = st.selectbox("Priority", ["Lowest", "Low", "Medium", "High", "Highest"], index=2)
        with col2:
            assignee = st.text_input("Assignee (email/name/accountId)")
            epic_link = st.text_input("Epic Key (optional)")
            story_points = st.number_input("Story Points (optional)", min_value=0.0, step=0.5, value=0.0, format="%.1f")
            assign_active_sprint = st.checkbox("Assign to active sprint")
            desired_status = st.text_input("Set Status on Create (optional)", placeholder="e.g., To Do")

        submitted = st.form_submit_button("Create Ticket")
        if submitted:
            sp_value = story_points if story_points > 0 else None
            result = st.session_state.ticket_tools.create_ticket(
                project_key=project_key.strip().upper(),
                summary=summary.strip(),
                description=description.strip(),
                issue_type=issue_type.strip(),
                assignee=assignee.strip() or None,
                epic_link=epic_link.strip() or None,
                priority=priority.strip(),
                story_points=sp_value,
                assign_active_sprint=assign_active_sprint,
                status=(desired_status.strip() or None),
            )
            if isinstance(result, str) and result.startswith("✅"):
                st.success(result)
            else:
                st.error(result)


def page_create_deployment() -> None:
    st.subheader("Create Deployment Ticket")
    with st.form("create_deploy_form"):
        col1, col2 = st.columns(2)
        with col1:
            project_key = st.text_input("Project Key", placeholder="e.g., FIJI")
            dev_keys_raw = st.text_input("Development Ticket Keys (comma separated)", placeholder="e.g., FIJI-817, FIJI-820")
            title = st.text_input("Deployment Title (optional)", placeholder="Deployment ticket for ...")
            description = st.text_area("Deployment Description", height=120)
            priority = st.selectbox("Priority", ["Lowest", "Low", "Medium", "High", "Highest"], index=2)
        with col2:
            assignee = st.text_input("Assignee (email/name/accountId)")
            pr_link = st.text_input("PR Link (optional)")
            qa_contacts = st.text_input("QA Contacts (optional)")
            qa_instructions = st.text_area("QA Instructions (optional)", height=120)
            story_points = st.number_input("Story Points (optional)", min_value=0.0, step=0.5, value=0.0, format="%.1f")

        submitted = st.form_submit_button("Create Deployment Ticket")
        if submitted:
            dev_ticket_keys = [k.strip().upper() for k in dev_keys_raw.split(",") if k.strip()]
            sp_value = story_points if story_points > 0 else None
            result = st.session_state.ticket_tools.create_deployment_ticket(
                project_key=project_key.strip().upper(),
                dev_ticket_keys=dev_ticket_keys,
                title=title.strip() or None,
                description=description.strip(),
                assignee=assignee.strip() or None,
                priority=priority.strip(),
                pr_link=pr_link.strip() or None,
                qa_contacts=qa_contacts.strip() or None,
                qa_instructions=qa_instructions.strip() or None,
                story_points=sp_value,
            )
            if isinstance(result, str) and result.startswith("✅"):
                st.success(result)
            else:
                st.error(result)


def page_search() -> None:
    st.subheader("Search Tickets (JQL)")
    col1, col2 = st.columns([3, 1])
    with col1:
        jql = st.text_input("JQL", placeholder="e.g., project = FIJI AND status != Done")
    with col2:
        run = st.button("Search")
    if run and jql.strip():
        result = st.session_state.ticket_tools.search_tickets(jql.strip())
        st.markdown(result)


def page_ticket_details() -> None:
    st.subheader("Ticket Details & Actions")
    ticket_key = st.text_input("Ticket Key", placeholder="e.g., FIJI-850")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Get Details") and ticket_key.strip():
            result = st.session_state.ticket_tools.get_ticket_details(ticket_key.strip().upper())
            st.markdown(result)
    with col2:
        new_status = st.text_input("Change Status", placeholder="e.g., In Progress")
        if st.button("Apply Status") and ticket_key.strip() and new_status.strip():
            result = st.session_state.ticket_tools.change_ticket_status(ticket_key.strip().upper(), new_status.strip())
            if isinstance(result, str) and result.startswith("✅"):
                st.success(result)
            else:
                st.error(result)
    with col3:
        assignee = st.text_input("Assign To (email/name/accountId)")
        if st.button("Assign") and ticket_key.strip() and assignee.strip():
            result = st.session_state.ticket_tools.assign_ticket(ticket_key.strip().upper(), assignee.strip())
            if isinstance(result, str) and result.startswith("✅"):
                st.success(result)
            else:
                st.error(result)

    st.divider()
    st.subheader("Edit Summary / Description / Priority")
    new_summary = st.text_input("New Summary")
    new_description = st.text_area("New Description", height=100)
    new_priority = st.selectbox("New Priority", ["", "Lowest", "Low", "Medium", "High", "Highest"], index=0)
    if st.button("Apply Edit") and ticket_key.strip():
        result = st.session_state.ticket_tools.edit_ticket(
            ticket_key=ticket_key.strip().upper(),
            summary=new_summary.strip() or None,
            description=new_description.strip() or None,
            priority=(new_priority.strip() or None) if new_priority else None,
        )
        if isinstance(result, str) and result.startswith("✅"):
            st.success(result)
        else:
            st.error(result)


def page_projects_users() -> None:
    st.subheader("Projects & Users")
    col1, col2 = st.columns(2)
    with col1:
        st.write("List Projects")
        if st.button("Fetch Projects"):
            projects = st.session_state.project_tools.list_projects()
            st.markdown(projects)
    with col2:
        st.write("Search Users")
        query = st.text_input("User Search", placeholder="name or email")
        if st.button("Search Users") and query.strip():
            users = st.session_state.project_tools.search_user(query.strip())
            st.markdown(users)


def page_epics() -> None:
    st.subheader("Epics")
    col1, col2 = st.columns(2)
    with col1:
        project_key = st.text_input("Project Key (optional)", key="epic_project")
        if st.button("List Epics"):
            epics = st.session_state.epic_tools.list_epics(project_key.strip().upper() or None)
            st.markdown(epics)
    with col2:
        st.write("Create Epic")
        epic_project = st.text_input("Project Key", key="create_epic_project")
        epic_summary = st.text_input("Epic Summary")
        epic_description = st.text_area("Epic Description", height=100)
        epic_assignee = st.text_input("Assignee (optional)")
        if st.button("Create Epic") and epic_project.strip() and epic_summary.strip():
            resp = st.session_state.epic_tools.create_epic(
                project_key=epic_project.strip().upper(),
                summary=epic_summary.strip(),
                description=epic_description.strip(),
                assignee=epic_assignee.strip() or None,
            )
            if isinstance(resp, str) and resp.startswith("✅"):
                st.success(resp)
            else:
                st.error(resp)


def page_analytics() -> None:
    st.subheader("Analytics Dashboard")
    with st.spinner("Loading analytics..."):
        report = st.session_state.analytics.generate_comprehensive_report()

    if not report or 'error' in report:
        st.error("Unable to load analytics data. Please check your Jira connection.")
        return

    overview = report.get('overview', {})
    status_data = report.get('status', {})
    projects_data = report.get('projects', {})
    assignee_data = report.get('assignees', {})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tickets", overview.get('total_tickets', 0))
    with col2:
        st.metric("Active Tickets", overview.get('active_tickets', 0))
    with col3:
        st.metric("Resolved Tickets", overview.get('resolved_tickets', 0))
    with col4:
        st.metric("Resolution Rate", f"{overview.get('resolution_rate', 0):.1f}%")

    st.divider()
    st.subheader("Tickets by Status")
    status_series = status_data.get('status_distribution', pd.Series())
    if not status_series.empty:
        fig = px.pie(values=status_series.values, names=status_series.index, title="Tickets by Status")
        st.plotly_chart(fig, config={"displaylogo": False}, width='stretch')

    st.subheader("Tickets per Project")
    most_active = projects_data.get('most_active_projects', pd.DataFrame())
    if isinstance(most_active, pd.DataFrame) and not most_active.empty:
        fig = px.bar(x=most_active.index, y=most_active['total_tickets'], labels={'x': 'Project', 'y': 'Tickets'})
        st.plotly_chart(fig, config={"displaylogo": False}, width='stretch')

    st.subheader("Top Assignees")
    top_assignees = assignee_data.get('top_assignees', pd.DataFrame())
    if isinstance(top_assignees, pd.DataFrame) and not top_assignees.empty and 'total_tickets' in top_assignees.columns:
        fig = px.bar(x=top_assignees.index, y=top_assignees['total_tickets'], labels={'x': 'Assignee', 'y': 'Tickets'})
        st.plotly_chart(fig, config={"displaylogo": False}, width='stretch')


def page_chat() -> None:
    st.subheader("Chat with Jira Agent")

    # Render conversation
    for msg in st.session_state.chat_history[-50:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        with st.chat_message("user" if role == "user" else "assistant"):
            st.markdown(content)

    prompt = st.chat_input("Ask me to create tickets, search by JQL, assign, change status, etc.")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant reply (agent maintains its own internal history as well)
        reply = st.session_state.chat_agent.run(prompt, stream=False)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

    if st.button("Clear Conversation"):
        st.session_state.chat_history = []
        st.rerun()

def page_assignee_performance() -> None:
    st.subheader("Assignee Performance")
    with st.spinner("Loading assignee analytics..."):
        report = st.session_state.analytics.generate_comprehensive_report()

    if not report or 'error' in report:
        st.error("Unable to load analytics data.")
        return

    assignee_data = report.get('assignees', {})
    stats = assignee_data.get('assignee_stats')
    if stats is None or getattr(stats, 'empty', True):
        st.info("No assignee data available.")
        return

    st.markdown("""
    Metrics per assignee:
    - total_tickets
    - resolved_tickets
    - avg_resolution_time (days)
    - resolution_rate (%)
    """)

    # Controls
    col1, col2 = st.columns(2)
    with col1:
        min_tickets = st.slider("Minimum tickets", min_value=0, max_value=50, value=1, step=1)
    with col2:
        sort_metric = st.selectbox(
            "Sort by",
            ["total_tickets", "resolved_tickets", "resolution_rate", "avg_resolution_time"],
            index=0,
        )

    filtered = stats[stats['total_tickets'] >= min_tickets]
    if sort_metric == "avg_resolution_time":
        filtered = filtered.sort_values(sort_metric, ascending=True)
    else:
        filtered = filtered.sort_values(sort_metric, ascending=False)

    st.dataframe(
        filtered[["total_tickets", "resolved_tickets", "avg_resolution_time", "resolution_rate"]],
        width='stretch',
        use_container_width=False,
    )

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tickets per Assignee")
        fig = px.bar(
            x=filtered.index,
            y=filtered['total_tickets'],
            labels={'x': 'Assignee', 'y': 'Total Tickets'},
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, width='stretch')
    with col2:
        st.subheader("Resolution Rate (%)")
        fig = px.bar(
            x=filtered.index,
            y=filtered['resolution_rate'],
            labels={'x': 'Assignee', 'y': 'Resolution Rate (%)'},
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Assignee Drilldown")
    assignee_query = st.text_input("Filter by Assignee (substring)", key="assignee_drill_q")
    if assignee_query.strip():
        df = st.session_state.analytics.get_fresh_data()
        if not df.empty:
            # Ensure status_category exists by recomputing metrics if missing
            if 'status_category' not in df.columns:
                df = st.session_state.analytics.get_fresh_data(force_refresh=True)
            mask = df['assignee'].astype(str).str.lower().str.contains(assignee_query.strip().lower())
            df_assignee = df[mask].copy()
            if df_assignee.empty:
                st.info("No tickets for this filter.")
            else:
                st.write(f"Tickets for '{assignee_query}': {len(df_assignee)}")
                cols = [c for c in ["key", "summary", "project", "status", "status_category", "priority", "created", "updated"] if c in df_assignee.columns]
                st.dataframe(df_assignee[cols], width='stretch', use_container_width=False)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("By Status")
                    status_counts = df_assignee['status'].value_counts()
                    if not status_counts.empty:
                        fig = px.pie(values=status_counts.values, names=status_counts.index)
                        st.plotly_chart(fig, config={"displaylogo": False}, width='stretch')
                with col2:
                    st.subheader("By Project")
                    proj_counts = df_assignee['project'].value_counts()
                    if not proj_counts.empty:
                        fig = px.bar(x=proj_counts.index, y=proj_counts.values, labels={'x': 'Project', 'y': 'Tickets'})
                        fig.update_xaxes(tickangle=45)
                        st.plotly_chart(fig, config={"displaylogo": False}, width='stretch')

                # Resolved vs Active vs Pending summary
                st.subheader("Status Category Breakdown")
                cat_counts = df_assignee['status_category'].value_counts()
                st.write(cat_counts)



def main() -> None:
    st.set_page_config(page_title="Jira Agent Dashboard", page_icon="🎫", layout="wide")
    initialize_state()

    st.markdown("""
    <style>
      .stMetric { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🎫 Jira Agent Dashboard")

    tabs = st.tabs([
        "Chat",
        "Create Ticket",
        "Deployment Ticket",
        "Search",
        "Ticket Details",
        "Projects & Users",
        "Epics",
        "Analytics",
        "Assignee Performance",
    ])

    with tabs[0]:
        page_chat()
    with tabs[1]:
        page_create_ticket()
    with tabs[2]:
        page_create_deployment()
    with tabs[3]:
        page_search()
    with tabs[4]:
        page_ticket_details()
    with tabs[5]:
        page_projects_users()
    with tabs[6]:
        page_epics()
    with tabs[7]:
        page_analytics()
    with tabs[8]:
        page_assignee_performance()


if __name__ == "__main__":
    main()


