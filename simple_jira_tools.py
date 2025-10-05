"""
Simple Jira tools without phi dependency.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from jira_client import JiraAgent
from config import JiraConfig, JiraBehavior
import requests


# ==============================
# 🚀 TICKET TOOLS
# ==============================
class SimpleJiraTicketTools:
    """Simple Jira ticket tools without phi dependency."""

    def __init__(self):
        self.jira_agent = JiraAgent()

    def create_ticket(
        self,
        project_key: str,
        summary: str,
        description: str = "",
        issue_type: str = "Task",
        assignee: Optional[str] = None,
        epic_link: Optional[str] = None,
        priority: str = "Medium",
        story_points: Optional[float] = None,
        sprint: Optional[str] = None,
        status: Optional[str] = None,
        assign_active_sprint: bool = False,
    ) -> str:
        """Create a new ticket in Jira."""
        try:
            assignee_account_id = assignee
            # 🧠 Determine if we need to resolve assignee name/email -> accountId
            if assignee and not any(assignee.startswith(p) for p in ["5d8b8c8e", "557058:", "712020:"]):
                # Try direct search via Jira API helper (handles nicknames)
                resolved = self.jira_agent.search_user_account_id(assignee)
                if resolved:
                    assignee_account_id = resolved
                else:
                    # Fall back to listing (may be unavailable)
                    users = self.jira_agent.list_users()
                    found_user = None
                    query = assignee.lower()
                    for user in users:
                        email = (user.get("emailAddress") or "").lower()
                        name = (user.get("displayName") or "").lower()
                        if query in email or query in name or query == email or query == name:
                            found_user = user
                            break
                    if found_user:
                        assignee_account_id = found_user["accountId"]
                    else:
                        # Proceed unassigned but inform the caller
                        assignee_account_id = None

            # 🧱 Create ticket
            ticket_key = self.jira_agent.create_ticket(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type,
                assignee=assignee_account_id,
                epic_link=epic_link,
                priority=priority,
                story_points=story_points,
                assign_to_active_sprint=assign_active_sprint,
                desired_status=status,
            )

            if ticket_key:
                ticket_url = f"{self.jira_agent.jira.server_url}/browse/{ticket_key}"
                assignment_note = " (unassigned; provide accountId to assign)" if assignee and not assignee_account_id else ""
                return f"✅ Successfully created ticket: {ticket_key}{assignment_note}\n🔗 Ticket URL: {ticket_url}"
            else:
                return "❌ Failed to create ticket"
        except Exception as e:
            return f"❌ Error creating ticket: {str(e)}"

    def create_deployment_ticket(
        self,
        project_key: str,
        dev_ticket_keys: List[str],
        title: Optional[str] = None,
        description: str = "",
        assignee: Optional[str] = None,
        priority: str = "Medium",
        pr_link: Optional[str] = None,
        qa_contacts: Optional[str] = None,
        qa_instructions: Optional[str] = None,
        story_points: Optional[float] = None,
    ) -> str:
        """Create a standardized deployment ticket and link to development tickets."""
        try:
            assignee_account_id = assignee
            if assignee and not any(assignee.startswith(p) for p in ["5d8b8c8e", "557058:", "712020:"]):
                users = self.jira_agent.list_users()
                found_user = None
                query = assignee.lower()

                for user in users:
                    email = (user.get("emailAddress") or "").lower()
                    name = (user.get("displayName") or "").lower()
                    if query in email or query in name or query == email or query == name:
                        found_user = user
                        break

                if found_user:
                    assignee_account_id = found_user["accountId"]
                else:
                    visible_users = ", ".join([u["displayName"] for u in users[:5]])
                    return f"❌ User '{assignee}' not found. Available users: {visible_users}..."

            ticket_key = self.jira_agent.create_deployment_ticket(
                project_key=project_key,
                dev_ticket_keys=dev_ticket_keys,
                summary=title,
                description=description,
                assignee=assignee_account_id,
                priority=priority,
                pr_link=pr_link,
                qa_contacts=qa_contacts,
                qa_instructions=qa_instructions,
                story_points=story_points,
            )

            if ticket_key:
                ticket_url = f"{self.jira_agent.jira.server_url}/browse/{ticket_key}"
                return (
                    f"✅ Successfully created deployment ticket: {ticket_key}\n"
                    f"🔗 Ticket URL: {ticket_url}\n"
                    f"📌 Epic: {JiraBehavior.DEPLOYMENT_EPIC_NAME}\n"
                    f"🔁 Status: {JiraBehavior.DEPLOYMENT_DEFAULT_STATUS}"
                )
            else:
                return "❌ Failed to create deployment ticket"
        except Exception as e:
            return f"❌ Error creating deployment ticket: {str(e)}"

    def assign_ticket(self, ticket_key: str, assignee: str) -> str:
        """Assign a ticket to a user by name or account ID."""
        try:
            assignee_account_id = assignee
            if not any(assignee.startswith(p) for p in ["5d8b8c8e", "557058:", "712020:"]):
                users = self.jira_agent.list_users()
                found_user = None
                query = assignee.lower()

                for user in users:
                    email = (user.get("emailAddress") or "").lower()
                    name = (user.get("displayName") or "").lower()
                    if query in email or query in name or query == email or query == name:
                        found_user = user
                        break

                if found_user:
                    assignee_account_id = found_user["accountId"]
                else:
                    visible_users = ", ".join([u["displayName"] for u in users[:5]])
                    return f"❌ User '{assignee}' not found. Available users: {visible_users}..."

            success = self.jira_agent.assign_ticket(ticket_key, assignee_account_id)
            if success:
                ticket_url = f"{self.jira_agent.jira.server_url}/browse/{ticket_key}"
                return f"✅ Successfully assigned {ticket_key} to {assignee}\n🔗 Ticket URL: {ticket_url}"
            else:
                return f"❌ Failed to assign {ticket_key}"
        except Exception as e:
            return f"❌ Error assigning ticket: {str(e)}"

    def edit_ticket(
        self,
        ticket_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> str:
        """Edit ticket details."""
        try:
            issue = self.jira_agent.jira.issue(ticket_key)
            fields_to_update = {}

            if summary:
                fields_to_update["summary"] = summary
            if description:
                fields_to_update["description"] = description
            if priority:
                fields_to_update["priority"] = {"name": priority}

            if fields_to_update:
                issue.update(fields=fields_to_update)
                ticket_url = f"{self.jira_agent.jira.server_url}/browse/{ticket_key}"
                return f"✅ Successfully updated ticket {ticket_key}\n🔗 Ticket URL: {ticket_url}"
            else:
                return "❌ No fields provided to update"
        except Exception as e:
            return f"❌ Error editing ticket: {str(e)}"

    def change_ticket_status(self, ticket_key: str, new_status: str) -> str:
        """Change the status of a ticket."""
        try:
            success = self.jira_agent.change_ticket_status(ticket_key, new_status)
            if success:
                ticket_url = f"{self.jira_agent.jira.server_url}/browse/{ticket_key}"
                return f"✅ Successfully changed {ticket_key} status to {new_status}\n🔗 Ticket URL: {ticket_url}"
            else:
                return f"❌ Failed to change {ticket_key} status to {new_status}"
        except Exception as e:
            return f"❌ Error changing ticket status: {str(e)}"

    def get_ticket_details(self, ticket_key: str) -> str:
        """Get detailed information about a ticket."""
        try:
            details = self.jira_agent.get_ticket_details(ticket_key)
            if not details:
                return f"❌ Could not retrieve details for {ticket_key}"

            ticket_url = f"{self.jira_agent.jira.server_url}/browse/{ticket_key}"
            return f"""
**Ticket Details for {ticket_key}:**
- **Summary:** {details['summary']}
- **Description:** {details['description']}
- **Status:** {details['status']}
- **Assignee:** {details['assignee']}
- **Reporter:** {details['reporter']}
- **Project:** {details['project']}
- **Issue Type:** {details['issue_type']}
- **Priority:** {details['priority']}
- **Created:** {details['created']}
- **Updated:** {details['updated']}
- **URL:** {ticket_url}
"""
        except Exception as e:
            return f"❌ Error getting ticket details: {str(e)}"

    def search_tickets(self, jql: str) -> str:
        """Search for tickets using JQL."""
        try:
            # Add date restriction if not already present to avoid unbounded queries
            if "created" not in jql.lower() and "updated" not in jql.lower():
                six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
                # JQL doesn't use WHERE, just add AND directly
                jql = f"{jql} AND created >= '{six_months_ago}'"
            
            tickets = self.jira_agent.search_tickets(jql)
            if not tickets:
                return "No tickets found matching the search criteria"

            result = "**Search Results:**\n"
            for ticket in tickets:
                ticket_url = f"{self.jira_agent.jira.server_url}/browse/{ticket['key']}"
                result += f"- **{ticket['key']}**: {ticket['summary']} ({ticket['status']}) - {ticket['assignee']}\n"
                result += f"  🔗 URL: {ticket_url}\n"
            return result
        except Exception as e:
            return f"❌ Error searching tickets: {str(e)}"

    def get_ticket_url(self, ticket_key: str) -> str:
        """Get the URL for a ticket."""
        try:
            return f"{self.jira_agent.jira.server_url}/browse/{ticket_key}"
        except Exception as e:
            return f"❌ Error getting ticket URL: {str(e)}"


# ==============================
# 🧭 PROJECT TOOLS
# ==============================
class SimpleJiraProjectTools:
    """Simple Jira project tools without phi dependency."""

    def __init__(self):
        self.jira_agent = JiraAgent()
        self.server_url = JiraConfig.JIRA_URL.rstrip("/")
        self.auth = (JiraConfig.JIRA_EMAIL, JiraConfig.JIRA_API_TOKEN)

    def list_projects(self) -> str:
        """List all projects in Jira."""
        try:
            projects = self.jira_agent.list_projects()
            if not projects:
                return "No projects found or unable to access projects"

            result = "**Available Projects:**\n"
            for project in projects:
                result += f"- **{project['key']}**: {project['name']} (ID: {project['id']})\n"
                if project.get("description"):
                    result += f"  Description: {project['description']}\n"
                if project.get("lead"):
                    result += f"  Lead: {project['lead']}\n"
                result += "\n"
            return result
        except Exception as e:
            return f"❌ Error listing projects: {str(e)}"

    def list_users(self, max_results=100):
        """List all visible users (filters out app/system accounts)."""
        url = f"{self.server_url}/rest/api/3/users/search"
        all_users = []
        start_at = 0

        while True:
            params = {"startAt": start_at, "maxResults": max_results, "query": ""}
            response = requests.get(url, auth=self.auth, params=params, timeout=15)
            if response.status_code != 200:
                raise Exception(f"Failed to list users: {response.status_code} - {response.text}")

            users = response.json()
            if not users:
                break

            for user in users:
                name = (user.get("displayName") or "").lower()
                if any(x in name for x in ["automation", "system", "slack", "teams", "trello", "opsgenie", "jira"]):
                    continue  # skip bots/apps

                all_users.append(
                    {
                        "displayName": user.get("displayName"),
                        "emailAddress": user.get("emailAddress"),
                        "accountId": user.get("accountId"),
                        "active": user.get("active", True),
                    }
                )

            if len(users) < max_results:
                break
            start_at += max_results

        return all_users

    def search_user(self, query: str) -> str:
        """Search for users by partial name or email."""
        try:
            query = query.strip().lower()
            if not query:
                return "❌ Please provide a search query."

            users = self.list_users()
            matches = [
                u
                for u in users
                if query in (u.get("displayName") or "").lower()
                or query in (u.get("emailAddress") or "").lower()
            ]

            if not matches:
                return f"❌ No users found matching '{query}'."

            matches.sort(key=lambda u: (u.get("displayName") or "").lower().find(query))
            result = f"**Users matching '{query}':**\n"
            for u in matches[:10]:
                result += f"- **{u['displayName']}** ({u['emailAddress']}) → `{u['accountId']}`\n"

            if len(matches) > 10:
                result += f"... and {len(matches) - 10} more results.\n"

            return result.strip()
        except Exception as e:
            return f"❌ Error searching users: {str(e)}"


# ==============================
# 🌟 EPIC TOOLS
# ==============================
class SimpleJiraEpicTools:
    """Simple Jira epic tools without phi dependency."""

    def __init__(self):
        self.jira_agent = JiraAgent()

    def list_epics(self, project_key: Optional[str] = None) -> str:
        """List epics in Jira."""
        try:
            epics = self.jira_agent.list_epics(project_key)
            if not epics:
                return f"No epics found{' for project ' + project_key if project_key else ''}"

            result = f"**Available Epics{' in ' + project_key if project_key else ''}:**\n"
            for epic in epics:
                epic_url = f"{self.jira_agent.jira.server_url}/browse/{epic['key']}"
                result += f"- **{epic['key']}**: {epic['summary']} ({epic['status']})\n"
                result += f"  Assignee: {epic['assignee']}\n"
                result += f"  Reporter: {epic['reporter']}\n"
                result += f"  Project: {epic['project']}\n"
                result += f"  Created: {epic['created']}\n"
                result += f"  🔗 URL: {epic_url}\n"
                if epic.get("description"):
                    result += f"  Description: {epic['description']}\n"
                result += "\n"
            return result
        except Exception as e:
            return f"❌ Error listing epics: {str(e)}"

    def create_epic(self, project_key: str, summary: str, description: str = "", assignee: Optional[str] = None) -> str:
        """Create a new epic in Jira."""
        try:
            assignee_account_id = assignee
            if assignee and not any(assignee.startswith(p) for p in ["5d8b8c8e", "557058:", "712020:"]):
                users = self.jira_agent.list_users()
                found_user = None
                query = assignee.lower()

                for user in users:
                    email = (user.get("emailAddress") or "").lower()
                    name = (user.get("displayName") or "").lower()
                    if query in email or query in name or query == email or query == name:
                        found_user = user
                        break

                if found_user:
                    assignee_account_id = found_user["accountId"]
                else:
                    visible_users = ", ".join([u["displayName"] for u in users[:5]])
                    return f"❌ User '{assignee}' not found. Available users: {visible_users}..."

            epic_key = self.jira_agent.create_epic(
                project_key=project_key,
                summary=summary,
                description=description,
                assignee=assignee_account_id,
            )

            if epic_key:
                epic_url = f"{self.jira_agent.jira.server_url}/browse/{epic_key}"
                return f"✅ Successfully created epic: {epic_key}\n🔗 Epic URL: {epic_url}"
            else:
                return "❌ Failed to create epic"
        except Exception as e:
            return f"❌ Error creating epic: {str(e)}"

    def get_epic_url(self, epic_key: str) -> str:
        """Get the URL for an epic."""
        try:
            return f"{self.jira_agent.jira.server_url}/browse/{epic_key}"
        except Exception as e:
            return f"❌ Error getting epic URL: {str(e)}"
