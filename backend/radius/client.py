"""
RADIUS client implementation using pyrad
"""
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad import packet
from django.conf import settings
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class RadiusClient:
    """Client for RADIUS authentication and accounting"""

    def __init__(
        self,
        server: Optional[str] = None,
        secret: Optional[str] = None,
        auth_port: Optional[int] = None,
        acct_port: Optional[int] = None
    ):
        """
        Initialize RADIUS client

        Args:
            server: RADIUS server IP/hostname
            secret: Shared secret
            auth_port: Authentication port (default 1812)
            acct_port: Accounting port (default 1813)
        """
        radius_config = getattr(settings, 'RADIUS_CONFIG', {})

        self.server = server or radius_config.get('SERVER', '127.0.0.1')
        self.secret = secret or radius_config.get('SECRET', 'testing123')
        self.auth_port = auth_port or radius_config.get('AUTH_PORT', 1812)
        self.acct_port = acct_port or radius_config.get('ACCT_PORT', 1813)

        # Create dictionary path (using default pyrad dictionary)
        self.dict_path = self._get_dictionary_path()

    def _get_dictionary_path(self) -> str:
        """
        Get path to RADIUS dictionary file

        Returns:
            Path to dictionary file
        """
        # Try to find pyrad's default dictionary
        try:
            import pyrad
            pyrad_path = os.path.dirname(pyrad.__file__)
            dict_path = os.path.join(pyrad_path, 'dictionary')
            if os.path.exists(dict_path):
                return dict_path
        except Exception:
            pass

        # Fallback to a basic dictionary path
        return '/usr/share/freeradius/dictionary'

    def _create_client(self, auth: bool = True) -> Client:
        """
        Create a pyrad Client instance

        Args:
            auth: If True, use auth port, else use acct port

        Returns:
            Configured Client instance
        """
        port = self.auth_port if auth else self.acct_port

        try:
            # Create dictionary
            dictionary = Dictionary(self.dict_path)
        except Exception as e:
            logger.warning(f"Failed to load RADIUS dictionary: {e}. Using minimal dict.")
            # Create a minimal in-memory dictionary
            dictionary = Dictionary()

        # Create client
        client = Client(
            server=self.server,
            secret=self.secret.encode('utf-8'),
            dict=dictionary
        )
        client.timeout = 5
        client.retries = 2

        return client

    def authenticate(
        self,
        username: str,
        password: str,
        nas_ip: Optional[str] = None,
        nas_port: Optional[int] = None,
        calling_station_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform RADIUS authentication (Access-Request)

        Args:
            username: Username to authenticate
            password: Password to verify
            nas_ip: NAS IP address
            nas_port: NAS port number
            calling_station_id: MAC address of client

        Returns:
            Authentication result dictionary
        """
        try:
            # Create client
            client = self._create_client(auth=True)

            # Create authentication request
            req = client.CreateAuthPacket(
                code=packet.AccessRequest,
                User_Name=username.encode('utf-8')
            )

            # Add password
            req["User-Password"] = req.PwCrypt(password)

            # Add optional attributes
            if nas_ip:
                req["NAS-IP-Address"] = nas_ip
            if nas_port:
                req["NAS-Port"] = nas_port
            if calling_station_id:
                req["Calling-Station-Id"] = calling_station_id

            # Send request
            logger.info(f"Sending RADIUS auth request for user: {username}")
            reply = client.SendPacket(req)

            # Check response
            if reply.code == packet.AccessAccept:
                logger.info(f"RADIUS auth accepted for user: {username}")
                return {
                    'success': True,
                    'status': 'accept',
                    'username': username,
                    'reply_message': reply.get('Reply-Message', [b''])[0].decode('utf-8') if 'Reply-Message' in reply else None,
                    'attributes': self._extract_attributes(reply)
                }
            else:
                logger.warning(f"RADIUS auth rejected for user: {username}")
                return {
                    'success': False,
                    'status': 'reject',
                    'username': username,
                    'reply_message': reply.get('Reply-Message', [b''])[0].decode('utf-8') if 'Reply-Message' in reply else None
                }

        except Exception as e:
            logger.error(f"RADIUS authentication error: {str(e)}")
            return {
                'success': False,
                'status': 'error',
                'username': username,
                'error': str(e)
            }

    def accounting_start(
        self,
        username: str,
        session_id: str,
        nas_ip: Optional[str] = None,
        nas_port: Optional[int] = None,
        framed_ip: Optional[str] = None,
        calling_station_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send accounting start packet

        Args:
            username: Username
            session_id: Unique session ID
            nas_ip: NAS IP address
            nas_port: NAS port
            framed_ip: IP assigned to user
            calling_station_id: MAC address

        Returns:
            Accounting result
        """
        return self._send_accounting(
            username=username,
            session_id=session_id,
            status_type='Start',
            nas_ip=nas_ip,
            nas_port=nas_port,
            framed_ip=framed_ip,
            calling_station_id=calling_station_id
        )

    def accounting_stop(
        self,
        username: str,
        session_id: str,
        session_time: int,
        input_octets: int,
        output_octets: int,
        input_packets: int,
        output_packets: int,
        terminate_cause: Optional[str] = None,
        nas_ip: Optional[str] = None,
        nas_port: Optional[int] = None,
        framed_ip: Optional[str] = None,
        calling_station_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send accounting stop packet

        Args:
            username: Username
            session_id: Unique session ID
            session_time: Session duration in seconds
            input_octets: Bytes received
            output_octets: Bytes sent
            input_packets: Packets received
            output_packets: Packets sent
            terminate_cause: Reason for termination
            nas_ip: NAS IP address
            nas_port: NAS port
            framed_ip: IP assigned to user
            calling_station_id: MAC address

        Returns:
            Accounting result
        """
        return self._send_accounting(
            username=username,
            session_id=session_id,
            status_type='Stop',
            session_time=session_time,
            input_octets=input_octets,
            output_octets=output_octets,
            input_packets=input_packets,
            output_packets=output_packets,
            terminate_cause=terminate_cause,
            nas_ip=nas_ip,
            nas_port=nas_port,
            framed_ip=framed_ip,
            calling_station_id=calling_station_id
        )

    def _send_accounting(
        self,
        username: str,
        session_id: str,
        status_type: str,
        session_time: Optional[int] = None,
        input_octets: Optional[int] = None,
        output_octets: Optional[int] = None,
        input_packets: Optional[int] = None,
        output_packets: Optional[int] = None,
        terminate_cause: Optional[str] = None,
        nas_ip: Optional[str] = None,
        nas_port: Optional[int] = None,
        framed_ip: Optional[str] = None,
        calling_station_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send accounting packet

        Args:
            Multiple accounting parameters

        Returns:
            Accounting result
        """
        try:
            # Create client
            client = self._create_client(auth=False)

            # Create accounting request
            req = client.CreateAcctPacket(
                User_Name=username.encode('utf-8')
            )

            # Required attributes
            req["Acct-Session-Id"] = session_id
            req["Acct-Status-Type"] = status_type

            # Optional attributes
            if nas_ip:
                req["NAS-IP-Address"] = nas_ip
            if nas_port:
                req["NAS-Port"] = nas_port
            if framed_ip:
                req["Framed-IP-Address"] = framed_ip
            if calling_station_id:
                req["Calling-Station-Id"] = calling_station_id

            # Stop-specific attributes
            if status_type == 'Stop':
                if session_time is not None:
                    req["Acct-Session-Time"] = session_time
                if input_octets is not None:
                    req["Acct-Input-Octets"] = input_octets
                if output_octets is not None:
                    req["Acct-Output-Octets"] = output_octets
                if input_packets is not None:
                    req["Acct-Input-Packets"] = input_packets
                if output_packets is not None:
                    req["Acct-Output-Packets"] = output_packets
                if terminate_cause:
                    req["Acct-Terminate-Cause"] = terminate_cause

            # Send request
            logger.info(f"Sending RADIUS accounting {status_type} for session: {session_id}")
            reply = client.SendPacket(req)

            logger.info(f"RADIUS accounting {status_type} sent successfully")
            return {
                'success': True,
                'status_type': status_type,
                'session_id': session_id,
                'username': username
            }

        except Exception as e:
            logger.error(f"RADIUS accounting error: {str(e)}")
            return {
                'success': False,
                'status_type': status_type,
                'session_id': session_id,
                'username': username,
                'error': str(e)
            }

    def _extract_attributes(self, reply: packet.Packet) -> Dict[str, Any]:
        """
        Extract attributes from RADIUS reply packet

        Args:
            reply: RADIUS reply packet

        Returns:
            Dictionary of attributes
        """
        attributes = {}
        try:
            for attr, value in reply.items():
                if isinstance(value, list) and len(value) > 0:
                    # Decode bytes to string if possible
                    decoded_values = []
                    for v in value:
                        if isinstance(v, bytes):
                            try:
                                decoded_values.append(v.decode('utf-8'))
                            except:
                                decoded_values.append(str(v))
                        else:
                            decoded_values.append(v)
                    attributes[attr] = decoded_values
        except Exception as e:
            logger.warning(f"Failed to extract attributes: {e}")

        return attributes
