from typing import Optional, Dict, Any
from phi.tools import Toolkit
from jira_client import JiraAgent
from analytics import JiraAnalytics
import difflib
import re


class AnalyticsTools(Toolkit):
    """Tools exposing per-assignee Jira performance analytics.

    These functions return markdown/text summaries so they can be used in chat or UIs.
    """

    def __init__(self):
        super().__init__(name="analytics_tools")
        self.jira_agent = JiraAgent()
        self.analytics = JiraAnalytics(self.jira_agent)

    # ---------- Epic title search ----------
    def search_epics_by_title(self, project_key: Optional[str], title_query: str, limit: int = 10) -> str:
        """Search epics by (fuzzy) title within a project; returns best matches with keys and summaries."""
        try:
            if not title_query or not title_query.strip():
                return "❌ Provide a non-empty title query"
            project = (project_key or "").strip().upper() or None
            epics = self.jira_agent.list_epics(project)
            if not epics:
                return f"No epics found{' in ' + project if project else ''}"
            q = title_query.strip().lower()
            scored = []
            for e in epics:
                title = (e.get('summary') or '').strip()
                ratio = difflib.SequenceMatcher(None, q, title.lower()).ratio()
                contains = 1.0 if q in title.lower() else 0.0
                score = max(ratio, contains)
                scored.append((score, e.get('key'), title))
            scored.sort(key=lambda x: x[0], reverse=True)
            out = [f"**Epic matches for '{title_query}':**"]
            for score, key, title in scored[: max(1, int(limit))]:
                out.append(f"- {key}: {title} (score {score:.2f})")
            return "\n".join(out)
        except Exception as e:
            return f"❌ Error searching epics: {str(e)}"

    def assignee_performance_summary(self, min_tickets: int = 1, limit: int = 25) -> str:
        """Summary per assignee: total, resolved, avg_days, resolution_rate (top N)."""
        try:
            df = self.analytics.get_fresh_data()
            if df.empty:
                return "No data available"
            stats = self.analytics.get_assignee_analytics(df).get("assignee_stats")
            if stats is None or getattr(stats, "empty", True):
                return "No assignee analytics available"
            filtered = stats[stats["total_tickets"] >= max(0, int(min_tickets))]
            top = filtered.head(max(1, int(limit)))
            lines = ["**Assignee Performance (top)**"]
            for name, row in top.iterrows():
                total = int(row.get("total_tickets", 0) or 0)
                resolved = int(row.get("resolved_tickets", 0) or 0)
                avg_days = float(row.get("avg_resolution_time", 0) or 0.0)
                rate = float(row.get("resolution_rate", 0) or 0.0)
                lines.append(f"- {name}: total={total}, resolved={resolved}, avg_days={avg_days:.1f}, rate={rate:.1f}%")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Error generating summary: {str(e)}"

    def assignee_detail(self, query: str) -> str:
        """Detailed metrics for a single assignee matched by substring (case-insensitive)."""
        try:
            q = (query or "").strip().lower()
            if not q:
                return "❌ Provide an assignee substring (name/email)"
            df = self.analytics.get_fresh_data()
            if df.empty:
                return "No data available"
            stats = self.analytics.get_assignee_analytics(df).get("assignee_stats")
            if stats is None or getattr(stats, "empty", True):
                return "No assignee analytics available"
            # Find best match by substring in the index (assignee display name)
            matches = [name for name in stats.index if q in str(name).lower()]
            if not matches:
                return f"No assignee matching '{query}'"
            name = matches[0]
            row = stats.loc[name]
            total = int(row.get("total_tickets", 0) or 0)
            resolved = int(row.get("resolved_tickets", 0) or 0)
            avg_days = float(row.get("avg_resolution_time", 0) or 0.0)
            rate = float(row.get("resolution_rate", 0) or 0.0)
            return (
                f"**Assignee: {name}**\n"
                f"- Total tickets: {total}\n"
                f"- Resolved tickets: {resolved}\n"
                f"- Avg resolution (days): {avg_days:.1f}\n"
                f"- Resolution rate: {rate:.1f}%\n"
            )
        except Exception as e:
            return f"❌ Error fetching assignee detail: {str(e)}"

    def top_assignees(self, metric: str = "total_tickets", limit: int = 10) -> str:
        """Return top assignees by a metric: total_tickets | resolved_tickets | resolution_rate | avg_resolution_time."""
        try:
            metric = (metric or "").strip()
            df = self.analytics.get_fresh_data()
            if df.empty:
                return "No data available"
            stats = self.analytics.get_assignee_analytics(df).get("assignee_stats")
            if stats is None or getattr(stats, "empty", True):
                return "No assignee analytics available"

            valid = {"total_tickets", "resolved_tickets", "resolution_rate", "avg_resolution_time"}
            if metric not in valid:
                return f"❌ metric must be one of: {', '.join(sorted(valid))}"

            if metric == "avg_resolution_time":
                ordered = stats[stats["avg_resolution_time"].notna()].nsmallest(max(1, int(limit)), metric)
            else:
                ordered = stats.nlargest(max(1, int(limit)), metric)

            lines = [f"**Top assignees by {metric}:**"]
            for name, row in ordered.iterrows():
                total = int(row.get("total_tickets", 0) or 0)
                resolved = int(row.get("resolved_tickets", 0) or 0)
                avg_days = float(row.get("avg_resolution_time", 0) or 0.0)
                rate = float(row.get("resolution_rate", 0) or 0.0)
                lines.append(f"- {name}: total={total}, resolved={resolved}, avg_days={avg_days:.1f}, rate={rate:.1f}%")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Error computing top assignees: {str(e)}"


