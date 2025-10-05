"""
Enhanced analytics module for Jira data analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any
from jira_client import JiraAgent

class JiraAnalytics:
    """Enhanced analytics for Jira data."""
    
    def __init__(self, jira_agent: JiraAgent):
        self.jira_agent = jira_agent
        self.data_cache = {}
        self.cache_timestamp = None
        self.cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
    
    def get_fresh_data(self, force_refresh: bool = False) -> pd.DataFrame:
        """Get fresh data from Jira, with caching."""
        now = datetime.now()
        
        # Check if we need to refresh cache
        if (not force_refresh and 
            self.cache_timestamp and 
            now - self.cache_timestamp < self.cache_duration and 
            'tickets' in self.data_cache):
            return self.data_cache['tickets']
        
        try:
            # Fetch tickets with date restriction to avoid unbounded queries
            # Get tickets from the last 6 months to avoid hitting limits
            six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            jql = f"created >= '{six_months_ago}' ORDER BY created DESC"
            tickets = self.jira_agent.search_tickets(jql)
            
            if not tickets:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(tickets)
            
            # Parse dates
            df['created'] = pd.to_datetime(df['created'], errors='coerce')
            df['updated'] = pd.to_datetime(df['updated'], errors='coerce')
            
            # Calculate additional metrics
            df = self._calculate_metrics(df)
            
            # Cache the data
            self.data_cache['tickets'] = df
            self.cache_timestamp = now
            
            return df
            
        except (ConnectionError, ValueError, KeyError) as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()
    
    def _calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional metrics for the dataframe."""
        if df.empty:
            return df
        
        # Resolution time calculation
        df['resolution_time_days'] = None
        df['is_resolved'] = df['status'].isin(['Done', 'Closed', 'Resolved', 'Completed'])
        
        for idx, row in df.iterrows():
            if row['is_resolved'] and pd.notna(row['created']) and pd.notna(row['updated']):
                df.at[idx, 'resolution_time_days'] = (row['updated'] - row['created']).days
        
        # Time-based columns
        df['created_date'] = df['created'].dt.date
        df['created_week'] = df['created'].dt.isocalendar().week
        df['created_month'] = df['created'].dt.to_period('M')
        df['created_year'] = df['created'].dt.year
        
        # Priority scoring
        priority_map = {'Critical': 5, 'High': 4, 'Medium': 3, 'Low': 2, 'Lowest': 1}
        df['priority_score'] = df['priority'].map(priority_map).fillna(0)
        
        # Status categories
        df['status_category'] = df['status'].apply(self._categorize_status)
        
        return df
    
    def _categorize_status(self, status: str) -> str:
        """Categorize status into broader categories."""
        if status in ['Done', 'Closed', 'Resolved', 'Completed']:
            return 'Resolved'
        elif status in ['In Progress', 'Active', 'Development']:
            return 'Active'
        elif status in ['To Do', 'Open', 'New', 'Backlog']:
            return 'Pending'
        else:
            return 'Other'
    
    def get_overview_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get overview metrics."""
        if df.empty:
            return {}
        
        total_tickets = len(df)
        active_tickets = len(df[df['status_category'] == 'Active'])
        resolved_tickets = len(df[df['status_category'] == 'Resolved'])
        pending_tickets = len(df[df['status_category'] == 'Pending'])
        
        # Calculate average resolution time
        resolved_df = df[df['resolution_time_days'].notna()]
        avg_resolution_time = resolved_df['resolution_time_days'].mean() if not resolved_df.empty else 0
        
        # Calculate resolution rate
        resolution_rate = (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0
        
        return {
            'total_tickets': total_tickets,
            'active_tickets': active_tickets,
            'resolved_tickets': resolved_tickets,
            'pending_tickets': pending_tickets,
            'avg_resolution_time': avg_resolution_time,
            'resolution_rate': resolution_rate
        }
    
    def get_assignee_analytics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get detailed assignee analytics."""
        if df.empty:
            return {}
        
        # Assignee performance metrics
        assignee_stats = df.groupby('assignee').agg({
            'key': 'count',
            'resolution_time_days': 'mean',
            'priority_score': 'mean',
            'status_category': lambda x: (x == 'Resolved').sum()
        }).rename(columns={
            'key': 'total_tickets',
            'resolution_time_days': 'avg_resolution_time',
            'priority_score': 'avg_priority',
            'status_category': 'resolved_tickets'
        })
        
        # Calculate resolution rate per assignee
        assignee_stats['resolution_rate'] = (
            assignee_stats['resolved_tickets'] / assignee_stats['total_tickets'] * 100
        ).round(1)
        
        # Sort by total tickets
        assignee_stats = assignee_stats.sort_values('total_tickets', ascending=False)
        
        return {
            'assignee_stats': assignee_stats,
            'top_assignees': assignee_stats.head(10),
            'most_efficient': assignee_stats[assignee_stats['total_tickets'] >= 3].nlargest(5, 'resolution_rate'),
            'slowest_resolvers': assignee_stats[assignee_stats['total_tickets'] >= 3].nsmallest(5, 'resolution_rate')
        }
    
    def get_project_analytics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get detailed project analytics."""
        if df.empty:
            return {}
        
        # Project performance metrics
        project_stats = df.groupby('project').agg({
            'key': 'count',
            'resolution_time_days': 'mean',
            'priority_score': 'mean',
            'status_category': lambda x: (x == 'Resolved').sum()
        }).rename(columns={
            'key': 'total_tickets',
            'resolution_time_days': 'avg_resolution_time',
            'priority_score': 'avg_priority',
            'status_category': 'resolved_tickets'
        })
        
        # Calculate completion rate
        project_stats['completion_rate'] = (
            project_stats['resolved_tickets'] / project_stats['total_tickets'] * 100
        ).round(1)
        
        # Sort by total tickets
        project_stats = project_stats.sort_values('total_tickets', ascending=False)
        
        return {
            'project_stats': project_stats,
            'most_active_projects': project_stats.head(10),
            'most_completed_projects': project_stats.nlargest(5, 'completion_rate'),
            'project_count': len(project_stats)
        }
    
    def get_trend_analytics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get trend analytics over time."""
        if df.empty:
            return {}
        
        # Daily ticket creation
        daily_creation = df.groupby('created_date').size().reset_index(name='tickets_created')
        
        # Weekly trends: compute Monday start by normalizing to midnight and subtracting weekday
        df['week_start'] = df['created'].dt.normalize() - pd.to_timedelta(df['created'].dt.weekday, unit='D')
        weekly_creation = df.groupby('week_start').size().reset_index(name='tickets_created')
        
        # Monthly trends
        monthly_creation = df.groupby('created_month').size().reset_index(name='tickets_created')
        
        # Resolution trends
        resolved_df = df[df['is_resolved']]
        if not resolved_df.empty:
            daily_resolution = resolved_df.groupby('updated').size().reset_index(name='tickets_resolved')
        else:
            daily_resolution = pd.DataFrame(columns=['updated', 'tickets_resolved'])
        
        return {
            'daily_creation': daily_creation,
            'weekly_creation': weekly_creation,
            'monthly_creation': monthly_creation,
            'daily_resolution': daily_resolution,
            'creation_trend': self._calculate_trend(daily_creation['tickets_created']),
            'resolution_trend': self._calculate_trend(daily_resolution['tickets_resolved']) if not daily_resolution.empty else 0
        }
    
    def _calculate_trend(self, series: pd.Series) -> float:
        """Calculate trend direction (-1 to 1)."""
        if len(series) < 2:
            return 0
        
        # Simple linear trend calculation
        x = np.arange(len(series))
        y = series.values
        
        if len(y) < 2:
            return 0
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalize to -1 to 1 range
        max_slope = max(abs(slope), 1)
        return slope / max_slope
    
    def get_status_analytics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get status distribution analytics."""
        if df.empty:
            return {}
        
        # Status distribution
        status_dist = df['status'].value_counts()
        status_category_dist = df['status_category'].value_counts()
        
        # Status transitions (simplified)
        status_flow = df.groupby(['status_category', 'project']).size().unstack(fill_value=0)
        
        return {
            'status_distribution': status_dist,
            'status_category_distribution': status_category_dist,
            'status_flow': status_flow,
            'status_count': len(status_dist)
        }
    
    def get_priority_analytics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get priority-based analytics."""
        if df.empty:
            return {}
        
        # Priority distribution
        priority_dist = df['priority'].value_counts()
        
        # Priority by project
        priority_by_project = df.groupby(['project', 'priority']).size().unstack(fill_value=0)
        
        # Priority resolution times
        priority_resolution = df.groupby('priority')['resolution_time_days'].agg(['mean', 'median', 'count'])
        
        return {
            'priority_distribution': priority_dist,
            'priority_by_project': priority_by_project,
            'priority_resolution_times': priority_resolution
        }
    
    def get_epic_analytics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get epic-related analytics."""
        if df.empty:
            return {}
        
        # This would require additional Jira API calls to get epic information
        # For now, return basic structure
        return {
            'epic_count': 0,  # Would need to fetch epics separately
            'epic_tickets': {},  # Would need epic linking
            'epic_progress': {}  # Would need epic status tracking
        }
    
    def generate_comprehensive_report(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Generate a comprehensive analytics report."""
        df = self.get_fresh_data(force_refresh)
        
        if df.empty:
            return {'error': 'No data available'}
        
        return {
            'overview': self.get_overview_metrics(df),
            'assignees': self.get_assignee_analytics(df),
            'projects': self.get_project_analytics(df),
            'trends': self.get_trend_analytics(df),
            'status': self.get_status_analytics(df),
            'priority': self.get_priority_analytics(df),
            'epics': self.get_epic_analytics(df),
            'data_freshness': self.cache_timestamp,
            'total_records': len(df)
        }
