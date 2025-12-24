"""
Utility functions for Mikrotik Agent API integration
"""
import requests
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MikrotikAgentClient:
    """Client for communicating with the Mikrotik Agent API"""

    def __init__(self, agent_url: Optional[str] = None):
        """
        Initialize the Mikrotik Agent client

        Args:
            agent_url: URL of the Mikrotik Agent API (default from settings)
        """
        self.agent_url = agent_url or getattr(
            settings,
            'MIKROTIK_AGENT_URL',
            'http://localhost:3001'
        )
        self.timeout = getattr(settings, 'MIKROTIK_AGENT_TIMEOUT', 10)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Mikrotik Agent

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request payload for POST/PUT requests

        Returns:
            Response data as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.agent_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Mikrotik Agent request failed: {method} {url} - {str(e)}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Mikrotik router via agent

        Returns:
            Connection test result
        """
        return self._make_request('GET', '/api/mikrotik/test')

    def get_hotspot_users(self) -> Dict[str, Any]:
        """
        Get all hotspot users from Mikrotik

        Returns:
            List of hotspot users
        """
        return self._make_request('GET', '/api/mikrotik/hotspot/users')

    def create_hotspot_user(
        self,
        username: str,
        password: str,
        profile: Optional[str] = None,
        mac_address: Optional[str] = None,
        comment: Optional[str] = None,
        limit_uptime: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new hotspot user on Mikrotik

        Args:
            username: Username for hotspot access
            password: Password for hotspot access
            profile: User profile name (optional)
            mac_address: MAC address binding (optional)
            comment: User comment (optional)
            limit_uptime: Session time limit (optional)

        Returns:
            Created user data
        """
        data = {
            'username': username,
            'password': password
        }

        if profile:
            data['profile'] = profile
        if mac_address:
            data['mac_address'] = mac_address
        if comment:
            data['comment'] = comment
        if limit_uptime:
            data['limit_uptime'] = limit_uptime

        return self._make_request('POST', '/api/mikrotik/hotspot/users', data)

    def update_hotspot_user(
        self,
        username: str,
        password: Optional[str] = None,
        profile: Optional[str] = None,
        disabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update an existing hotspot user on Mikrotik

        Args:
            username: Username to update
            password: New password (optional)
            profile: New profile (optional)
            disabled: Disable/enable user (optional)

        Returns:
            Updated user data
        """
        data = {}
        if password:
            data['password'] = password
        if profile:
            data['profile'] = profile
        if disabled is not None:
            data['disabled'] = disabled

        return self._make_request(
            'PUT',
            f'/api/mikrotik/hotspot/users/{username}',
            data
        )

    def delete_hotspot_user(self, username: str) -> Dict[str, Any]:
        """
        Delete a hotspot user from Mikrotik

        Args:
            username: Username to delete

        Returns:
            Deletion result
        """
        return self._make_request(
            'DELETE',
            f'/api/mikrotik/hotspot/users/{username}'
        )

    def get_active_connections(self) -> Dict[str, Any]:
        """
        Get all active hotspot connections

        Returns:
            List of active connections
        """
        return self._make_request('GET', '/api/mikrotik/hotspot/active')

    def disconnect_session(self, session_id: str) -> Dict[str, Any]:
        """
        Disconnect an active hotspot session

        Args:
            session_id: Session ID to disconnect

        Returns:
            Disconnection result
        """
        return self._make_request(
            'DELETE',
            f'/api/mikrotik/hotspot/active/{session_id}'
        )

    def get_hotspot_profiles(self) -> Dict[str, Any]:
        """
        Get all hotspot user profiles

        Returns:
            List of user profiles
        """
        return self._make_request('GET', '/api/mikrotik/hotspot/profiles')

    def get_system_resources(self) -> Dict[str, Any]:
        """
        Get Mikrotik system resources

        Returns:
            System resource information
        """
        return self._make_request('GET', '/api/mikrotik/system/resources')

    # DNS Static Entries Management
    # =============================

    def get_dns_static_entries(self) -> Dict[str, Any]:
        """
        Get all DNS static entries from Mikrotik

        Returns:
            List of DNS static entries
        """
        return self._make_request('GET', '/api/mikrotik/dns/static')

    def create_dns_static_entry(
        self,
        name: Optional[str] = None,
        address: str = '0.0.0.0',
        regexp: Optional[str] = None,
        comment: Optional[str] = None,
        disabled: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new DNS static entry on Mikrotik

        Args:
            name: Domain name to match (e.g., 'facebook.com')
            address: IP address to resolve to (default: 0.0.0.0 for blocking)
            regexp: Regex pattern for matching (e.g., '.*\\.tiktok\\.com$')
            comment: Entry comment for identification
            disabled: Whether the entry is disabled

        Returns:
            Created entry data with ID
        """
        data = {
            'address': address,
            'disabled': disabled
        }

        if name:
            data['name'] = name
        if regexp:
            data['regexp'] = regexp
        if comment:
            data['comment'] = comment

        return self._make_request('POST', '/api/mikrotik/dns/static', data)

    def update_dns_static_entry(
        self,
        entry_id: str,
        name: Optional[str] = None,
        address: Optional[str] = None,
        regexp: Optional[str] = None,
        comment: Optional[str] = None,
        disabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update an existing DNS static entry

        Args:
            entry_id: ID of the entry to update
            name: New domain name
            address: New IP address
            regexp: New regex pattern
            comment: New comment
            disabled: New disabled state

        Returns:
            Updated entry data
        """
        data = {}
        if name is not None:
            data['name'] = name
        if address is not None:
            data['address'] = address
        if regexp is not None:
            data['regexp'] = regexp
        if comment is not None:
            data['comment'] = comment
        if disabled is not None:
            data['disabled'] = disabled

        return self._make_request('PUT', f'/api/mikrotik/dns/static/{entry_id}', data)

    def delete_dns_static_entry(self, entry_id: str) -> Dict[str, Any]:
        """
        Delete a DNS static entry

        Args:
            entry_id: ID of the entry to delete

        Returns:
            Deletion result
        """
        return self._make_request('DELETE', f'/api/mikrotik/dns/static/{entry_id}')
