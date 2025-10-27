from jira import JIRA
from typing import List, Dict, Optional, Any
import re
import requests
import difflib
from config import JiraConfig, JiraFieldIds, JiraBehavior

class JiraAgent:
    def __init__(self):
        """Initialize Jira client with authentication."""
        try:
            # Initialize with explicit parameters to avoid conflicts
            self.jira = JIRA(
                server=JiraConfig.JIRA_URL,
                basic_auth=(JiraConfig.JIRA_EMAIL, JiraConfig.JIRA_API_TOKEN),
                options={'verify': True}
            )
            print("✅ Successfully connected to Jira")
        except Exception as e:
            print(f"❌ Failed to connect to Jira: {e}")
            self.jira = None

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects in Jira."""
        if not self.jira:
            return []
        
        try:
            projects = self.jira.projects()
            return [
                {
                    'key': project.key,
                    'name': project.name,
                    'id': project.id,
                    'description': getattr(project, 'description', ''),
                    'lead': getattr(project, 'lead', {}).get('displayName', '') if hasattr(project, 'lead') else ''
                }
                for project in projects
            ]
        except Exception as e:
            print(f"Error listing projects: {e}")
            return []

    def list_users(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """List users in Jira, optionally filtered by project."""
        if not self.jira:
            return []
        
        try:
            users = []
            
            # Check if we're in GDPR strict mode or have authentication issues
            try:
                # Prefer REST v3 endpoint to avoid GDPR username param issues
                users = self.search_users_v3('a')
            except Exception as e:
                error_msg = str(e)
                if "GDPR strict mode" in error_msg:
                    print("⚠️  Jira is configured with GDPR strict mode - user listing is not available")
                    print("💡 You can still use the agent for other operations like creating tickets")
                    print("💡 For user assignments, you'll need to provide account IDs manually")
                    return []
                elif "AUTHENTICATED_FAILED" in error_msg or "401" in error_msg:
                    print("⚠️  Authentication failed - please check your Jira credentials")
                    print("💡 Make sure your JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN are correct")
                    return []
                else:
                    print(f"⚠️  User listing not available: {error_msg}")
                    return []
            return users
            
        except Exception as e:
            print(f"Error listing users: {e}")
            return []

    def search_users_v3(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search users via REST v3 using 'query' param (GDPR-safe)."""
        server = JiraConfig.JIRA_URL.rstrip('/')
        url = f"{server}/rest/api/3/users/search"
        all_users: List[Dict[str, Any]] = []
        start_at = 0
        while True:
            params = {"query": query, "startAt": start_at, "maxResults": max_results}
            resp = requests.get(url, params=params, auth=(JiraConfig.JIRA_EMAIL, JiraConfig.JIRA_API_TOKEN), timeout=15)
            if resp.status_code != 200:
                raise Exception(f"User search failed: {resp.status_code} {resp.text}")
            batch = resp.json() or []
            for u in batch:
                all_users.append({
                    'accountId': u.get('accountId', ''),
                    'displayName': u.get('displayName', ''),
                    'emailAddress': u.get('emailAddress', ''),
                    'active': u.get('active', True),
                })
            if len(batch) < max_results:
                break
            start_at += max_results
        return all_users

    def search_user_account_id(self, query: str) -> Optional[str]:
        """Search a user's accountId by email/displayName. Handles simple nicknames via default domain."""
        if not self.jira:
            return None
        query = (query or '').strip()
        if not query:
            return None
        try:
            lc_query = query.lower()
            parts = [p for p in re.split(r"\s+", lc_query) if p]
            first = re.sub(r"[^a-z0-9]", "", parts[0]) if parts else ""
            last = re.sub(r"[^a-z0-9]", "", parts[-1]) if len(parts) > 1 else ""
            domain = JiraConfig.DEFAULT_EMAIL_DOMAIN

            candidates: List[str] = []
            if '@' in lc_query:
                candidates.append(lc_query)
            if first:
                candidates.append(f"{first}@{domain}")
            if first and last:
                candidates.extend([
                    f"{first}.{last}@{domain}",
                    f"{first}{last}@{domain}",
                    f"{first}_{last}@{domain}",
                    f"{first[0]}{last}@{domain}",
                ])

            # Always try the raw name as well
            if lc_query not in candidates:
                candidates.append(lc_query)

            def matches(u: Dict[str, Any], needle: str) -> bool:
                email = (u.get('emailAddress') or '').lower()
                name = (u.get('displayName') or '').lower()
                if needle in email or needle in name:
                    return True
                if first and last and (first in name and last in name):
                    return True
                if first and not last and name.startswith(first):
                    return True
                return False

            for cand in candidates:
                users = self.search_users_v3(cand)
                for u in users:
                    if matches(u, cand):
                        return u.get('accountId')
        except Exception as e:
            print(f"⚠️  User search failed: {e}")
            return None
        return None

    def list_epics(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """List epics in Jira using REST v3 API."""
        if not self.jira:
            return []
        
        try:
            jql = "issuetype = Epic ORDER BY created DESC"
            if project_key:
                jql = f"project = {project_key} AND issuetype = Epic ORDER BY created DESC"
            
            # Use _rest_search_all helper
            results = self._rest_search_all(jql, fields=['summary', 'description', 'status', 'assignee', 'reporter', 'created', 'updated', 'project'])
            
            epics = []
            for issue in results:
                fields = issue.get('fields', {})
                assignee = fields.get('assignee')
                reporter = fields.get('reporter')
                status = fields.get('status')
                project = fields.get('project')
                
                epics.append({
                    'key': issue.get('key'),
                    'summary': fields.get('summary', ''),
                    'description': fields.get('description', ''),
                    'status': status.get('name') if status else 'Unknown',
                    'assignee': assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned',
                    'reporter': reporter.get('displayName', 'Unknown') if reporter else 'Unknown',
                    'created': fields.get('created', ''),
                    'updated': fields.get('updated', ''),
                    'project': project.get('key') if project else ''
                })
            
            return epics
        except Exception as e:
            print(f"❌ Error listing epics: {e}")
            return []

    def resolve_epic_key_by_title(self, project_key: str, epic_title: str, min_ratio: float = 0.5) -> Optional[str]:
        """Resolve an epic key by (approximate) title within a project.

        Uses fuzzy matching to tolerate typos and minor variations.
        Returns the best matching epic key if similarity >= min_ratio, else None.
        """
        try:
            title_norm = (epic_title or "").strip().lower()
            if not title_norm:
                return None
            epics = self.list_epics(project_key)
            if not epics:
                return None
            
            # Quick contains match first (bidirectional)
            for e in epics:
                epic_title_lower = (e.get('summary') or '').strip().lower()
                # Check if query is in epic title OR epic title is in query
                if title_norm in epic_title_lower or epic_title_lower in title_norm:
                    return e.get('key')
            
            # Word-based matching: check if significant words overlap
            query_words = set(title_norm.split())
            for e in epics:
                epic_title_lower = (e.get('summary') or '').strip().lower()
                epic_words = set(epic_title_lower.split())
                # If more than 50% of query words are in epic title, it's a match
                if query_words and len(query_words & epic_words) / len(query_words) >= 0.5:
                    return e.get('key')
            
            # Fuzzy ratio best-match
            candidates = [(e.get('key'), (e.get('summary') or '').strip()) for e in epics]
            best_key = None
            best_ratio = 0.0
            for key, title in candidates:
                ratio = difflib.SequenceMatcher(None, title_norm, title.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_key = key
            if best_ratio >= min_ratio:
                return best_key
            return None
        except Exception:
            return None

    def create_epic(self, project_key: str, summary: str, description: str = "", 
                   assignee: Optional[str] = None) -> Optional[str]:
        """Create a new epic in Jira."""
        if not self.jira:
            return None
        
        try:
            epic_data = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Epic'}
            }
            
            if assignee:
                epic_data['assignee'] = {'accountId': assignee}
            
            new_epic = self.jira.create_issue(fields=epic_data)
            print(f"✅ Created epic: {new_epic.key}")
            return new_epic.key
        except Exception as e:
            print(f"❌ Error creating epic: {e}")
            return None

    def create_ticket(self, project_key: str, summary: str, description: str = "",
                     issue_type: str = "Task", assignee: Optional[str] = None,
                     epic_link: Optional[str] = None, priority: str = "Medium",
                     story_points: Optional[float] = None,
                     assign_to_active_sprint: bool = False,
                     desired_status: Optional[str] = None) -> Optional[str]:
        """Create a new ticket in Jira with optional story points, epic link, sprint, and status."""
        if not self.jira:
            return None
        
        try:
            ticket_data = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
                'priority': {'name': priority}
            }
            
            if assignee:
                ticket_data['assignee'] = {'accountId': assignee}
            
            # Set Epic Link correctly for company-managed projects
            if epic_link:
                ticket_data[JiraFieldIds.EPIC_LINK] = epic_link

            # Set story points on create if provided (resolve field id); retry without if fails
            sp_field = None
            if story_points is not None:
                sp_field = self.get_story_points_field_id()
                if sp_field:
                    ticket_data[sp_field] = story_points

            try:
                new_ticket = self.jira.create_issue(fields=ticket_data)
            except Exception as create_err:
                err_text = str(create_err)
                if sp_field and sp_field in ticket_data and "cannot be set" in err_text:
                    ticket_data.pop(sp_field, None)
                    new_ticket = self.jira.create_issue(fields=ticket_data)
                else:
                    raise
            print(f"✅ Created ticket: {new_ticket.key}")

            # Assign to active sprint if requested
            if assign_to_active_sprint:
                try:
                    self.add_issues_to_active_sprint(project_key, [new_ticket.key])
                except Exception as sprint_err:
                    print(f"⚠️  Failed to add {new_ticket.key} to active sprint: {sprint_err}")

            # Set story points post-create if requested and not set during create
            if story_points is not None:
                try:
                    sp_field = sp_field or self.get_story_points_field_id()
                    if sp_field:
                        issue = self.jira.issue(new_ticket.key)
                        issue.update(fields={sp_field: story_points})
                except Exception as sp_err:
                    print(f"⚠️  Failed to set story points on {new_ticket.key}: {sp_err}")

            # Transition to desired status if provided
            if desired_status:
                try:
                    self.change_ticket_status(new_ticket.key, desired_status)
                except Exception as status_err:
                    print(f"⚠️  Failed to set status for {new_ticket.key}: {status_err}")
            
            return new_ticket.key
        except Exception as e:
            print(f"❌ Error creating ticket: {e}")
            return None

    def get_story_points_field_id(self) -> Optional[str]:
        """Resolve the Story Points field id from Jira; fallback to configured default."""
        try:
            fields = self.jira.fields()
            for f in fields:
                try:
                    name = (f.get('name') or '').strip().lower()
                    if name in ('story points', 'story point estimate', 'story point estimates'):
                        return f.get('id')
                except Exception:
                    continue
        except Exception as e:
            print(f"⚠️  Could not fetch fields to resolve story points: {e}")
        return JiraFieldIds.STORY_POINTS

    def assign_ticket(self, ticket_key: str, assignee_account_id: str) -> bool:
        """Assign a ticket to a user."""
        if not self.jira:
            return False
        
        try:
            issue = self.jira.issue(ticket_key)
            issue.update(assignee={'accountId': assignee_account_id})
            print(f"✅ Assigned {ticket_key} to user")
            return True
        except Exception as e:
            print(f"❌ Error assigning ticket: {e}")
            return False

    def change_ticket_status(self, ticket_key: str, new_status: str) -> bool:
        """Change the status of a ticket."""
        if not self.jira:
            return False
        
        try:
            issue = self.jira.issue(ticket_key)
            transitions = self.jira.transitions(issue)
            
            # Find the transition that matches the target status
            target_transition = None
            for transition in transitions:
                if transition['name'].lower() == new_status.lower():
                    target_transition = transition
                    break
            
            if target_transition:
                self.jira.transition_issue(issue, target_transition['id'])
                print(f"✅ Changed {ticket_key} status to {new_status}")
                return True
            else:
                print(f"❌ No transition found to status: {new_status}")
                print(f"Available transitions: {[t['name'] for t in transitions]}")
                return False
        except Exception as e:
            print(f"❌ Error changing ticket status: {e}")
            return False

    def get_ticket_details(self, ticket_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a ticket."""
        if not self.jira:
            return None
        
        try:
            issue = self.jira.issue(ticket_key)
            return {
                'key': issue.key,
                'summary': issue.fields.summary,
                'description': getattr(issue.fields, 'description', ''),
                'status': issue.fields.status.name,
                'assignee': getattr(issue.fields.assignee, 'displayName', 'Unassigned') if issue.fields.assignee else 'Unassigned',
                'reporter': issue.fields.reporter.displayName,
                'created': issue.fields.created,
                'updated': issue.fields.updated,
                'project': issue.fields.project.key,
                'issue_type': issue.fields.issuetype.name,
                'priority': issue.fields.priority.name if issue.fields.priority else 'None'
            }
        except Exception as e:
            print(f"❌ Error getting ticket details: {e}")
            return None

    def _rest_search_all(self, jql: str, fields: Optional[List[str]] = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search Jira using REST v3 /rest/api/3/search/jql with pagination.
        Returns all matching issues as raw JSON dictionaries.
        
        Based on: https://developer.atlassian.com/changelog/#CHANGE-2046
        """
        server = JiraConfig.JIRA_URL.rstrip('/')
        url = f"{server}/rest/api/3/search/jql"
        
        all_issues: List[Dict[str, Any]] = []
        next_page_token = None
        
        # Default fields if not specified
        if fields is None:
            fields = ['summary', 'status', 'assignee', 'project', 'issuetype', 'created', 'updated', 'priority', 'reporter', 'description']
        
        while True:
            # Correct payload format for v3 search/jql endpoint
            payload = {
                "jql": jql,
                "maxResults": max_results,
                "fieldsByKeys": False,
                "fields": fields
            }
            
            if next_page_token:
                payload["pageToken"] = next_page_token
            
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    auth=(JiraConfig.JIRA_EMAIL, JiraConfig.JIRA_API_TOKEN),
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                    timeout=30
                )
                
                if resp.status_code != 200:
                    raise Exception(f"REST search failed: {resp.status_code} {resp.text}")
                
                data = resp.json()
                issues = data.get('issues', [])
                all_issues.extend(issues)
                
                # Check if there are more pages
                is_last = data.get('isLast', True)
                if is_last:
                    break
                
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
                
            except Exception as e:
                print(f"❌ Error in _rest_search_all: {e}")
                break
        
        return all_issues

    def search_tickets(self, jql: str) -> List[Dict[str, Any]]:
        """Search for tickets using JQL."""
        if not self.jira:
            return []
        
        try:
            jql = self._normalize_jql_assignees(jql)
            issues = self.jira.search_issues(jql)
            return [
                {
                    'key': issue.key,
                    'summary': issue.fields.summary,
                    'status': issue.fields.status.name,
                    'assignee': getattr(issue.fields.assignee, 'displayName', 'Unassigned') if issue.fields.assignee else 'Unassigned',
                    'project': issue.fields.project.key,
                    'issue_type': issue.fields.issuetype.name,
                    'created': issue.fields.created,
                    'updated': issue.fields.updated,
                    'priority': issue.fields.priority.name if issue.fields.priority else 'None',
                    'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown'
                }
                for issue in issues
            ]
        except Exception as e:
            print(f"❌ Error searching tickets: {e}")
            return []

    def _normalize_jql_assignees(self, jql: str) -> str:
        """Replace assignee names/emails in JQL with accountIds when possible (GDPR-safe).

        Examples:
          assignee = saad         -> assignee = 5d8b...
          assignee in (saad, ali) -> assignee in (5d8b..., 712020:...)
        """
        try:
            pattern_eq = re.compile(r"assignee\s*=\s*([^\s)]+)", re.IGNORECASE)
            pattern_in = re.compile(r"assignee\s+in\s*\(([^)]*)\)", re.IGNORECASE)

            def is_account_id(token: str) -> bool:
                return token.startswith("5d") or token.startswith("557058:") or token.startswith("712020:")

            # Handle assignee = token
            def repl_eq(match: re.Match) -> str:
                token = match.group(1).strip().strip('"\'')
                if is_account_id(token):
                    return match.group(0)
                account_id = self.search_user_account_id(token)
                if account_id:
                    return match.group(0).replace(token, account_id)
                return match.group(0)

            # Handle assignee in (...)
            def repl_in(match: re.Match) -> str:
                body = match.group(1)
                tokens = [t.strip().strip('"\'') for t in body.split(',') if t.strip()]
                replaced: List[str] = []
                for t in tokens:
                    if is_account_id(t):
                        replaced.append(t)
                    else:
                        account_id = self.search_user_account_id(t)
                        replaced.append(account_id or t)
                new_body = ", ".join(replaced)
                return match.group(0).replace(body, new_body)

            # Apply replacements
            jql = pattern_eq.sub(repl_eq, jql)
            jql = pattern_in.sub(repl_in, jql)
            return jql
        except Exception:
            return jql

    # ==============================
    # Sprint and Linking Helpers
    # ==============================
    def get_active_sprint(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Find the active sprint for the project's board.
        
        Searches for a board that belongs to the specified project and returns its active sprint.
        """
        if not self.jira:
            return None
        try:
            # Try to find boards for this specific project
            all_boards = self.jira.boards()
            project_boards = []
            
            for board in all_boards:
                try:
                    # Check if board belongs to this project by name matching
                    # Note: board details API may not be available in all Jira instances
                    if project_key.upper() in board.name.upper():
                        # Verify this board has the project
                        try:
                            # Get issues from board to verify project
                            issues = self.jira.search_issues(
                                f"project = {project_key} AND Sprint is not EMPTY",
                                maxResults=1
                            )
                            if issues:
                                project_boards.append(board)
                        except Exception:
                            # If search fails, use name matching
                            if project_key.upper() in board.name.upper():
                                project_boards.append(board)
                except Exception:
                    continue
            
            # If no project-specific boards found, try all scrum boards
            if not project_boards:
                scrum_boards = self.jira.boards(type='scrum')
                project_boards = list(scrum_boards) if scrum_boards else []
            
            # If still no boards, use all boards
            if not project_boards:
                project_boards = list(all_boards) if all_boards else []
            
            if not project_boards:
                print(f"⚠️  No boards found for project {project_key}")
                return None
            
            # Try to find active sprint in project boards
            for board in project_boards:
                try:
                    sprints = self.jira.sprints(board.id, state='active')
                    if sprints:
                        print(f"✅ Found active sprint '{sprints[0].name}' in board '{board.name}' for project {project_key}")
                        return sprints[0].raw
                except Exception as e:
                    continue
            
            print(f"⚠️  No active sprint found for project {project_key}")
            return None
        except Exception as e:
            print(f"⚠️  Error fetching active sprint for {project_key}: {e}")
            return None

    def add_issues_to_active_sprint(self, project_key: str, issue_keys: List[str]) -> bool:
        """Add issues to the active sprint for the given project."""
        try:
            sprint = self.get_active_sprint(project_key)
            if not sprint:
                return False
            sprint_id = sprint.get('id') or sprint.get('self', '').split('/')[-1]
            if not sprint_id:
                return False
            self.jira.add_issues_to_sprint(sprint_id, issue_keys)
            print(f"✅ Added issues {issue_keys} to sprint {sprint_id}")
            return True
        except Exception as e:
            print(f"⚠️  Failed adding issues to sprint: {e}")
            return False

    def link_issues(self, inward_key: str, outward_key: str, link_type: str = JiraBehavior.DEFAULT_LINK_TYPE) -> bool:
        """Create a Jira link between two issues."""
        if not self.jira:
            return False
        try:
            self.jira.create_issue_link(
                type=link_type,
                inwardIssue=inward_key,
                outwardIssue=outward_key,
            )
            print(f"✅ Linked {inward_key} -[{link_type}]-> {outward_key}")
            return True
        except Exception as e:
            print(f"⚠️  Failed to link issues: {e}")
            return False

    def find_or_create_deployment_epic(self, project_key: str) -> Optional[str]:
        """Find the 'Bugs and Configurations' epic in the project or create it.
        
        Uses partial matching to find existing epics like:
        - 'Bugs and Configuration'
        - '(PROJECT) Bugs and Configuration'
        - 'Bugs and Configuration Overflow'
        """
        try:
            epics = self.list_epics(project_key)
            target_name = JiraBehavior.DEPLOYMENT_EPIC_NAME.strip().lower()
            
            # First pass: Look for exact match
            for epic in epics:
                epic_summary = epic.get('summary', '').strip().lower()
                if epic_summary == target_name:
                    return epic['key']
            
            # Second pass: Look for partial matches (must contain key words)
            # Extract key words from target (e.g., "bugs", "configuration")
            target_words = set(w for w in target_name.split() if len(w) > 3)
            
            for epic in epics:
                epic_summary = epic.get('summary', '').strip().lower()
                epic_words = set(w for w in epic_summary.split() if len(w) > 3)
                
                # If epic contains all key words from target, it's a match
                if target_words and target_words.issubset(epic_words):
                    print(f"✅ Found matching epic by partial match: {epic['key']} - '{epic.get('summary')}'")
                    return epic['key']
            
            # Not found, create it with project prefix
            epic_summary = f"({project_key}) {JiraBehavior.DEPLOYMENT_EPIC_NAME}"
            epic_key = self.create_epic(
                project_key=project_key,
                summary=epic_summary,
                description=f"Auto-created epic for deployment & configuration tickets in {project_key}"
            )
            return epic_key
        except Exception as e:
            print(f"⚠️  Failed to find/create deployment epic: {e}")
            return None

    def create_deployment_ticket(
        self,
        project_key: str,
        dev_ticket_keys: List[str],
        summary: Optional[str] = None,
        description: str = "",
        assignee: Optional[str] = None,
        priority: str = "Medium",
        pr_link: Optional[str] = None,
        qa_contacts: Optional[str] = None,
        qa_instructions: Optional[str] = None,
        story_points: Optional[float] = None,
    ) -> Optional[str]:
        """Create a deployment ticket with defaults, links to dev tickets, epic, sprint, and status.
        
        The deployment ticket is created in the same project as the referenced dev ticket.
        Naming convention: (PROJECT) Deployment ticket for <DEV-TICKET>
        """
        if not self.jira:
            return None
        try:
            # Derive project from the first dev ticket if not provided or to ensure consistency
            actual_project_key = project_key
            if dev_ticket_keys:
                try:
                    # Get the project from the first dev ticket
                    first_dev_ticket = self.jira.issue(dev_ticket_keys[0])
                    actual_project_key = first_dev_ticket.fields.project.key
                    print(f"✅ Using project {actual_project_key} from dev ticket {dev_ticket_keys[0]}")
                except Exception as e:
                    print(f"⚠️  Could not fetch dev ticket project, using provided project: {e}")
            
            # Derive title following standard naming convention
            if not summary:
                # Standard format: (PROJECT) Deployment ticket for DEV-TICKET
                dev_tickets_str = ", ".join(dev_ticket_keys) if len(dev_ticket_keys) > 1 else dev_ticket_keys[0]
                summary = f"({actual_project_key}) Deployment ticket for {dev_tickets_str}"

            # Ensure epic in the correct project
            epic_key = self.find_or_create_deployment_epic(actual_project_key)

            # Build description with references
            desc_parts = []
            if description:
                desc_parts.append(description)
            if pr_link:
                desc_parts.append(f"PR: {pr_link}")
            if qa_contacts:
                desc_parts.append(f"QA: {qa_contacts}")
            if qa_instructions:
                desc_parts.append(f"QA Instructions:\n{qa_instructions}")
            if dev_ticket_keys:
                base = JiraConfig.JIRA_URL.rstrip('/')
                links = "\n".join([f"- {base}/browse/{k}" for k in dev_ticket_keys])
                desc_parts.append(f"Related development tickets:\n{links}")
            full_description = "\n\n".join([p for p in desc_parts if p])

            # Create ticket with defaults - use actual_project_key to ensure correct sprint
            ticket_key = self.create_ticket(
                project_key=actual_project_key,
                summary=summary,
                description=full_description,
                issue_type="Task",
                assignee=assignee,
                epic_link=epic_key,
                priority=priority,
                story_points=story_points,
                assign_to_active_sprint=True,
                desired_status=JiraBehavior.DEPLOYMENT_DEFAULT_STATUS,
            )
            if not ticket_key:
                return None

            # Link to dev tickets
            for dev_key in dev_ticket_keys:
                self.link_issues(ticket_key, dev_key)

            return ticket_key
        except Exception as e:
            print(f"❌ Error creating deployment ticket: {e}")
            return None
