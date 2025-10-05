"""
Final Phi Jira Agent - Using functions directly as tools (correct approach).
"""

from phi.assistant import Assistant
from phi.llm.azure import AzureOpenAIChat
from typing import Optional
from textwrap import dedent
from config import GeneralConfig
from simple_jira_tools import SimpleJiraTicketTools, SimpleJiraProjectTools, SimpleJiraEpicTools
from analytics_tools import AnalyticsTools

# Create tool instances
ticket_tools = SimpleJiraTicketTools()
project_tools = SimpleJiraProjectTools()
epic_tools = SimpleJiraEpicTools()
analytics_tools = AnalyticsTools()

def create_phi_jira_agent(
    llm_model=AzureOpenAIChat(
            api_version=GeneralConfig.AZURE_OPENAPI_VERSION,
            model=GeneralConfig.AZURE_GPT_4O_MINI_MODEL,
            api_key=GeneralConfig.AZURE_OPENAI_4O_MINI_KEY,
            azure_endpoint=GeneralConfig.AZURE_OPENAI_4O_MINI_URL,
            temperature=0.1),
    user_id: Optional[str] = None,
    run_id: Optional[str] = None,
    debug_mode: bool = True,
) -> Assistant:
    """Create a comprehensive Jira automation agent using phi with direct function tools."""

    # List all tool functions directly (correct phi approach)
    tools = [
        # Ticket tools
        ticket_tools.create_ticket,
        ticket_tools.assign_ticket,
        ticket_tools.edit_ticket,
        ticket_tools.change_ticket_status,
        ticket_tools.get_ticket_details,
        ticket_tools.search_tickets,
        ticket_tools.get_ticket_url,
        ticket_tools.create_deployment_ticket,
        
        # Project tools
        project_tools.list_projects,
        #project_tools.list_users,
        project_tools.search_user,
        
        # Epic tools
        epic_tools.list_epics,
        epic_tools.create_epic,
        epic_tools.get_epic_url,

        # Analytics tools
    #     analytics_tools.assignee_performance_summary,
    #     analytics_tools.assignee_detail,
    #     analytics_tools.top_assignees,
     ]

    extra_instructions = [
        "You are a comprehensive Jira automation agent that can handle all aspects of Jira project management.",
        "Always provide clear, actionable responses with proper formatting.",
        "When creating tickets or epics, ensure all required fields are provided.",
        "Use JQL (Jira Query Language) for advanced ticket searches.",
        "Always return ticket URLs when creating or referencing tickets.",
        "Handle GDPR strict mode gracefully when user lookup is not available.",
        "For user assignments, try to use names/emails first, but fall back to account IDs if needed.",
        # Safety rules to avoid unintended edits
        "CRITICAL: If the user intent is to CREATE a ticket, do NOT modify existing tickets. Only call create_ticket or create_deployment_ticket.",
        "Only perform edits, status changes, or assignments when the user explicitly provides a ticket key (e.g., 'PROJ-123') and asks to edit/assign/change.",
        "Never infer or reuse a ticket key from prior context for modification. If no explicit key is given, ask for clarification instead of modifying anything.",
        "After a successful creation, always surface the NEW ticket key and URL."
    ]

    # Create LLM model if not provided
    if llm_model is None:
        llm_model = AzureOpenAIChat(
            api_version=GeneralConfig.AZURE_OPENAPI_VERSION,
            model=GeneralConfig.AZURE_GPT_4O_MINI_MODEL,
            api_key=GeneralConfig.AZURE_OPENAI_4O_MINI_KEY,
            azure_endpoint=GeneralConfig.AZURE_OPENAI_4O_MINI_URL,
            temperature=0.1
        )

    return Assistant(
        name="Jira Automation Agent",
        role="Comprehensive Jira project management automation assistant that can create, manage, and track tickets, epics, projects, and users.",
        llm=llm_model,
        instructions=[
            "You are an expert Jira automation agent with full access to Jira project management capabilities.",
            "Always validate project keys, user account IDs, and ticket keys before performing operations.",
            "Provide clear feedback on the success or failure of operations.",
            "When creating tickets, suggest appropriate issue types, priorities, and assignments based on context.",
            "Use JQL queries effectively for searching and filtering tickets.",
            "Always include ticket URLs in responses for easy access.",
            "Handle errors gracefully and provide helpful suggestions for resolution.",
            "Format responses clearly with proper markdown formatting for better readability.",
            "When user lookup is not available (GDPR strict mode), provide clear guidance on using account IDs.",
            "For assignments, try to use user names or emails first, but be prepared to use account IDs if needed.",
            # Reinforce safety
            "If the action is 'create', do not call edit_ticket, change_ticket_status, or assign_ticket."
        ],
        tools=tools,
        run_id=run_id,
        user_id=user_id,
        description=dedent(
            """\
            You are the most advanced Jira automation agent in the world.

            Your goal is to automate all aspects of Jira project management including:
            - Ticket creation, editing, and management
            - Project and user administration  
            - Epic organization and tracking
            - Status workflow management
            - Assignment and priority handling
            - Search and reporting capabilities
            - URL generation for easy access

            You can handle complex multi-step operations and provide comprehensive project management support.
            """
        ),
        show_tool_calls=False,
        read_chat_history=True,
        add_chat_history_to_messages=True,
        markdown=True,
        add_datetime_to_instructions=True,
        debug_mode=debug_mode,
        extra_instructions=extra_instructions,
        introduction=dedent(
            """\
            🎯 **Jira Automation Agent Ready!**

            I can help you automate all aspects of Jira project management:

            **🚀 What I can do:**
            - Create and manage tickets (Tasks, Bugs, Stories, etc.)
            - Assign tickets to team members by name or email (when available)
            - Change ticket statuses and priorities
            - Create and organize epics
            - List projects and users
            - Search tickets with JQL queries
            - **All operations return direct links automatically**
            - Edit ticket details and descriptions

            **💡 Example requests:**
            - "Create a new bug ticket in project HC titled 'Login issue' and assign it to saad@teamsolve.com"
            - "Assign ticket HC-123 to saad@teamsolve.com"
            - "Change ticket HC-123 status to 'In Progress'"
            - "List all epics in project HC"
            - "Search for all open tickets assigned to me"
            - "Create an epic and assign it to saad@teamsolve.com"
            - "Create a deployment ticket for FIJI-817 with PR link <url> and assign to Naqash"

            **✨ Features:**
            - Assign tickets by user names or emails (when user lookup is available)
            - All operations automatically return ticket/epic URLs
            - Smart user name resolution
            - Handles GDPR strict mode gracefully

            How can I help you manage your Jira projects today? 🎯
            """
        ),
        num_history_messages=10,
    )


# Convenience function to get a ready-to-use agent
def get_phi_jira_agent(user_id: Optional[str] = None, run_id: Optional[str] = None) -> Assistant:
    """Get a configured Jira agent ready for use."""
    return create_phi_jira_agent(user_id=user_id, run_id=run_id)


# Example usage
if __name__ == "__main__":
    # Create and test the agent
    agent = get_phi_jira_agent()
    
    print("🎯 Phi Jira Agent")
    print("=" * 50)
    print("✨ Features:")
    print("- Assign tasks by user names (when available)")
    print("- All operations return URLs automatically")
    print("- Uses phi framework with direct function tools")
    print()
    print("Type 'quit' to exit")
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            
            if not user_input:
                continue
            
            print("\n🤖 Agent:")
            response = agent.run(user_input,stream=False)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

