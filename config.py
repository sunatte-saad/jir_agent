import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ---------- Azure OpenAI Configuration ----------
class GeneralConfig:
    AZURE_OPENAPI_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_GPT_4O_MINI_MODEL = os.environ.get("AZURE_OPENAI_MODEL_NAME_4O_MINI", "")
    AZURE_OPENAI_4O_MINI_KEY = os.environ.get("AZURE_OPENAI_4O_MINI_KEY", "")
    AZURE_OPENAI_4O_MINI_URL = os.environ.get("AZURE_OPENAI_4O_MINI_URL", "")
    AZURE_EMBEDDING_KEY_3 = os.environ.get("AZURE_EMBEDDING_KEY_3", "")
    AZURE_EMBEDDING_VERSION = os.environ.get("AZURE_EMBEDDING_VERSION", "2023-05-15")
    AZURE_EMBEDDING_MODEL_3 = os.environ.get("AZURE_EMBEDDING_MODEL_3", "text-embedding-3-large")

# ---------- Jira Configuration ----------
class JiraConfig:
    JIRA_URL = os.environ.get("JIRA_URL", "")
    JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
    JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
    DEFAULT_EMAIL_DOMAIN = os.environ.get("JIRA_DEFAULT_EMAIL_DOMAIN", "teamsolve.com")

class JiraFieldIds:
    """Jira custom field IDs used by the app."""
    EPIC_LINK = os.environ.get("JIRA_EPIC_LINK_FIELD", "customfield_10014")
    STORY_POINTS = os.environ.get("JIRA_STORY_POINTS_FIELD", "customfield_10016")

class JiraBehavior:
    """Default behaviors for ticket creation and deployment handling."""
    DEPLOYMENT_EPIC_NAME = os.environ.get("JIRA_DEPLOYMENT_EPIC_NAME", "Bugs and Configurations")
    DEPLOYMENT_DEFAULT_STATUS = os.environ.get("JIRA_DEPLOYMENT_DEFAULT_STATUS", "Ready to Deploy")
    TASK_DEFAULT_STATUS = os.environ.get("JIRA_TASK_DEFAULT_STATUS", "To Do")
    DEFAULT_LINK_TYPE = os.environ.get("JIRA_DEFAULT_LINK_TYPE", "Relates")

# ---------- Microsoft Bot Configuration ----------
class BotConfig:
    APP_ID = os.environ.get("MICROSOFT_APP_ID", "")
    APP_PASSWORD = os.environ.get("MICROSOFT_APP_PASSWORD", "")
    TENANT_ID = os.environ.get("MICROSOFT_APP_TENANT_ID", "")
