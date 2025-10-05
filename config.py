import os
from dotenv import load_dotenv

load_dotenv()

class GeneralConfig:
    # Azure OpenAI Configuration
    AZURE_OPENAPI_VERSION = os.environ.get("azure_openai_api_version", "2024-02-15-preview")
    AZURE_GPT_4O_MINI_MODEL = os.environ.get('azure_openai_model_name_4o_mini', "")
    AZURE_OPENAI_4O_MINI_KEY = os.environ.get("azure_openai_4o_mini_key", "")
    AZURE_OPENAI_4O_MINI_URL = os.environ.get("azure_openai_4o_mini_url", "")
    AZURE_EMBEDDING_KEY_3 = os.environ.get("azure_embedding_key_3", "")
    AZURE_EMBEDDING_VERSION = os.environ.get("azure_embedding_version", "2023-05-15")
    AZURE_EMBEDDING_MODEL_3 = os.environ.get("azure_embedding_model_3", "text-embedding-3-large")

class JiraConfig:
    # Jira Configuration
    JIRA_URL = os.environ.get("JIRA_URL", "")
    JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
    JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
    DEFAULT_EMAIL_DOMAIN = os.environ.get("JIRA_DEFAULT_EMAIL_DOMAIN", "teamsolve.com")

class JiraFieldIds:
    """Central place to configure Jira custom field IDs used by the app.

    These defaults are common on Jira Cloud but may vary per instance.
    Override via environment variables if needed.
    """
    EPIC_LINK = os.environ.get("JIRA_EPIC_LINK_FIELD", "customfield_10014")
    STORY_POINTS = os.environ.get("JIRA_STORY_POINTS_FIELD", "customfield_10016")

class JiraBehavior:
    """Default behaviors for ticket creation and deployment handling."""
    DEPLOYMENT_EPIC_NAME = os.environ.get("JIRA_DEPLOYMENT_EPIC_NAME", "Bugs and Configurations")
    DEPLOYMENT_DEFAULT_STATUS = os.environ.get("JIRA_DEPLOYMENT_DEFAULT_STATUS", "Ready to Deploy")
    TASK_DEFAULT_STATUS = os.environ.get("JIRA_TASK_DEFAULT_STATUS", "To Do")
    DEFAULT_LINK_TYPE = os.environ.get("JIRA_DEFAULT_LINK_TYPE", "Relates")
