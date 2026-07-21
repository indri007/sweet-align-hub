import json
import requests
import logging
from typing import Optional, List, Dict, Any

from config import SNOWFLAKE_ACCOUNT, SNOWFLAKE_TOKEN, SNOWFLAKE_DB, SNOWFLAKE_SCHEMA

logger = logging.getLogger(__name__)

class SnowflakeClient:
    """Client for interacting with Snowflake REST APIs and MCP Functions."""
    
    def __init__(self):
        self.account = SNOWFLAKE_ACCOUNT
        self.token = SNOWFLAKE_TOKEN
        self.db = SNOWFLAKE_DB
        self.schema = SNOWFLAKE_SCHEMA
        
        if not self.account or not self.token:
            logger.warning("Snowflake credentials (SNOWFLAKE_ACCOUNT, SNOWFLAKE_TOKEN) are not fully configured.")

    def _get_base_url(self) -> str:
        """Construct the base URL for the Snowflake account."""
        return f"https://{self.account}.snowflakecomputing.com/api/v2/databases/{self.db}/schemas/{self.schema}"

    def _get_headers(self) -> Dict[str, str]:
        """Construct standard authentication headers."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def call_align_data(self, input_text: str, target_format: str) -> Optional[Any]:
        """
        Call the ALIGN_DATA(VARCHAR, VARCHAR) function via REST API.
        
        Args:
            input_text: The input data to align.
            target_format: The target format specification.
            
        Returns:
            The parsed JSON response or None on failure.
        """
        if not self.account or not self.token:
            logger.error("Cannot call ALIGN_DATA: Snowflake credentials missing.")
            return None

        url = f"{self._get_base_url()}/functions/ALIGN_DATA(VARCHAR,VARCHAR):execute"
        
        payload = {
            "data": [[input_text, target_format]]
        }

        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Snowflake ALIGN_DATA: {e}")
            return None

    def call_map_fields(self, source_schema: str, target_schema: str) -> Optional[Any]:
        """
        Call the MAP_FIELDS(VARCHAR, VARCHAR) function via REST API.
        
        Args:
            source_schema: The source schema definition.
            target_schema: The target schema definition.
            
        Returns:
            The parsed JSON response or None on failure.
        """
        if not self.account or not self.token:
            logger.error("Cannot call MAP_FIELDS: Snowflake credentials missing.")
            return None

        url = f"{self._get_base_url()}/functions/MAP_FIELDS(VARCHAR,VARCHAR):execute"
        
        payload = {
            "data": [[source_schema, target_schema]]
        }

        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Snowflake MAP_FIELDS: {e}")
            return None

# Singleton instance for easy import
snowflake_client = SnowflakeClient()
