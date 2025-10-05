# Jira Automation Agent

A comprehensive AI-powered agent for automating Jira project management tasks including ticket creation, assignment, status management, epic organization, and more.

## Features

### 🎯 Core Capabilities
- **Ticket Management**: Create, edit, assign, and change status of tickets
- **Project Management**: List projects and users
- **Epic Management**: Create and organize epics
- **Search & Discovery**: Advanced ticket searching with JQL
- **URL Generation**: Direct links to tickets and epics
- **Status Management**: Workflow transitions and status updates
- **Assignment**: Assign tickets to team members
- **Priority Management**: Set and update ticket priorities

### 🚀 Supported Operations

#### Ticket Operations
- Create tickets (Task, Bug, Story, etc.)
- Edit ticket details (summary, description, priority)
- Assign tickets to users
- Change ticket status through workflow
- Search tickets using JQL
- Get ticket details and URLs

#### Project Operations
- List all projects
- List users (system-wide or project-specific)
- Get project information

#### Epic Operations
- Create epics
- List epics (system-wide or project-specific)
- Link tickets to epics
- Get epic URLs

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
Copy `.env.example` to `.env` and fill in values:

```env
JIRA_URL=
JIRA_EMAIL=
JIRA_API_TOKEN=
JIRA_DEFAULT_EMAIL_DOMAIN=

azure_openai_api_version=2024-02-15-preview
azure_openai_model_name_4o_mini=
azure_openai_4o_mini_key=
azure_openai_4o_mini_url=
azure_embedding_key_3=
azure_embedding_version=2023-05-15
azure_embedding_model_3=text-embedding-3-large
```

3. **Get Jira API Token:**
   - Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Create a new API token
   - Use your email and this token for authentication

## Usage

### Basic Usage

```python
from phi_jira_agent_final import get_phi_jira_agent

# Create the agent
agent = get_phi_jira_agent()

# Use the agent
response = agent.run("List all projects",stream=False)
print(response)
```

### Interactive Mode

```bash
python example_usage.py interactive
```

### Streamlit Dashboard

```bash
streamlit run dashboard_app.py
```

After packaging, you can run:

```bash
jir-agent-dashboard
```

### API Server

```bash
uvicorn main:app --reload
```

After packaging, you can run:

```bash
jir-agent-api
```

### Microsoft Teams Bot via API

1) Configure environment variables

Set these in your shell or `.env`:

```env
MICROSOFT_APP_ID=<bot app id>
MICROSOFT_APP_PASSWORD=<bot client secret>
MICROSOFT_APP_TENANT_ID=<tenant id or 'common'>
```

2) Run the API locally

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

3) Expose a public URL (for local testing)

- Use a tunneling tool (e.g., ngrok): `ngrok http http://localhost:8000`
- Note the public HTTPS URL.

4) Configure the Bot in Azure

- In Azure Bot registration, set the Messaging endpoint to:
  `https://<your-public-host>/api/messages`
- Ensure Microsoft App ID/Password match your environment variables.

5) Test from Teams

- Add your bot to a Team or personal scope.
- Send a message (e.g., "List projects"). The bot relays to `main.py` → agent and replies via Bot Framework.

Health check:

```bash
curl http://localhost:8000/health
# {"status":"ok","agent":"Phi Jira Agent ready"}
```

Notes:
- The agent uses the same tools as the dashboard (ticket creation, status changes, search, epics, analytics queries).
- Make sure Jira/Azure env vars are set in `.env` before starting.

```

### Example Commands

#### Project Management
```python
# List all projects
agent.run("List all projects",stream=False)

# List users
agent.run("List all users",stream=False)
agent.run("List users in project PROJ",stream=False)
```

#### Ticket Management
```python
# Create a ticket
agent.run("Create a new task in project PROJ titled 'Implement login' with description 'Add user authentication' and priority High",stream=False)

# Assign a ticket
agent.run("Assign ticket PROJ-123 to user with account ID 5d8b8c8e-1234-5678-9abc-123456789abc",stream=False)

# Change ticket status
agent.run("Change ticket PROJ-123 status to 'In Progress'",stream=False)

# Edit ticket
agent.run("Edit ticket PROJ-123 to update summary to 'Updated: Implement login' and priority to Critical",stream=False)

# Get ticket details
agent.run("Get details for ticket PROJ-123",stream=False)

# Get ticket URL
agent.run("Get the URL for ticket PROJ-123",stream=False)
```

#### Epic Management
```python
# Create an epic
agent.run("Create a new epic in project PROJ titled 'User Management System' with description 'Complete user management functionality'",stream=False)

# List epics
agent.run("List all epics",stream=False)
agent.run("List epics in project PROJ",stream=False)
```

### Workflow Integration
The agent can handle Jira workflow transitions:

```python
# Change ticket status (follows Jira workflow)
agent.run("Change ticket PROJ-123 status to 'In Progress'",stream=False)
agent.run("Change ticket PROJ-123 status to 'Done'",stream=False)
agent.run("Change ticket PROJ-123 status to 'To Do'",stream=False)
```

## File Structure

```
jir_agent/
├── config.py              # Configuration settings
├── jira_client.py         # Jira API client
├── llm_client.py          # LLM client for Azure OpenAI
├── jira_tools.py          # Tool definitions for the agent
├── jira_agent.py          # Main agent implementation
├── example_usage.py       # Usage examples
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Configuration

### Jira Setup
1. Ensure you have access to a Jira instance
2. Create an API token in your Atlassian account
3. Update the configuration in `config.py` or `.env` file

### Azure OpenAI Setup
1. Create an Azure OpenAI resource
2. Deploy a GPT-4o-mini model
3. Get your API key and endpoint
4. Update the configuration

## Error Handling

The agent includes comprehensive error handling:
- Connection validation
- Input validation
- Graceful error messages
- Retry mechanisms for API calls

## Security

- API tokens are stored securely in environment variables
- No hardcoded credentials in the code
- Proper authentication for all Jira operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the error messages for specific guidance
2. Verify your Jira and Azure OpenAI configuration
3. Ensure you have proper permissions in Jira
4. Check the Jira API documentation for advanced features

## Examples

See `example_usage.py` for comprehensive usage examples including:
- Basic operations
- Interactive mode
- Error handling
- Advanced JQL queries
