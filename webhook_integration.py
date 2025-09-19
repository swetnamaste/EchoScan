"""
Webhook Integration Module for EchoScan
Provides lightweight webhook support for Slack, Teams, AWS Lambda, SIEM, and Jira
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
import time
from datetime import datetime, timezone
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookConfig:
    """Configuration class for webhook settings"""
    
    def __init__(self):
        self.slack_url = os.getenv('SLACK_WEBHOOK_URL')
        self.teams_url = os.getenv('TEAMS_WEBHOOK_URL')
        self.lambda_url = os.getenv('AWS_LAMBDA_WEBHOOK_URL')
        self.siem_url = os.getenv('SIEM_WEBHOOK_URL')
        self.custom_url = os.getenv('CUSTOM_WEBHOOK_URL')
        
        # Jira configuration
        self.jira_base_url = os.getenv('JIRA_BASE_URL')
        self.jira_username = os.getenv('JIRA_USERNAME')
        self.jira_api_token = os.getenv('JIRA_API_TOKEN')
        self.jira_project_key = os.getenv('JIRA_PROJECT_KEY', 'ECHOSCAN')
        self.jira_issue_type = os.getenv('JIRA_ISSUE_TYPE', 'Bug')
        
        # Webhook settings
        self.timeout = int(os.getenv('WEBHOOK_TIMEOUT', '30'))
        self.retries = int(os.getenv('WEBHOOK_RETRIES', '3'))
        self.enabled = os.getenv('ENABLE_WEBHOOKS', 'true').lower() == 'true'

class WebhookManager:
    """Main webhook management class"""
    
    def __init__(self):
        self.config = WebhookConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EchoScan-Webhook/1.0',
            'Content-Type': 'application/json'
        })
    
    def format_alert_data(self, echoscan_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format EchoScan result for webhook notifications"""
        
        # Extract key information
        verdict = echoscan_result.get('verdict', 'Unknown')
        input_text = echoscan_result.get('input', '')[:100]  # Truncate for privacy
        delta_s = echoscan_result.get('delta_s', 0.0)
        echo_sense = echoscan_result.get('echo_sense', 0.0)
        glyph_id = echoscan_result.get('glyph_id', 'Unknown')
        vault_permission = echoscan_result.get('vault_permission', False)
        
        # Determine alert level
        if verdict == 'Hallucination' or delta_s > 0.05:
            alert_level = 'CRITICAL'
        elif verdict == 'Plausible' or echo_sense < 0.5:
            alert_level = 'WARNING'
        else:
            alert_level = 'INFO'
        
        alert_data = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'source': 'EchoScan',
            'version': '1.0',
            'alert_level': alert_level,
            'verdict': verdict,
            'confidence': echo_sense,
            'delta_s': delta_s,
            'glyph_id': glyph_id,
            'vault_access': vault_permission,
            'input_preview': input_text,
            'full_result': echoscan_result
        }
        
        return alert_data
    
    def send_slack_notification(self, alert_data: Dict[str, Any]) -> bool:
        """Send notification to Slack"""
        if not self.config.slack_url:
            return False
        
        # Format for Slack
        color = {
            'CRITICAL': 'danger',
            'WARNING': 'warning',  
            'INFO': 'good'
        }.get(alert_data['alert_level'], 'good')
        
        payload = {
            'text': f"EchoScan Alert - {alert_data['alert_level']}",
            'attachments': [{
                'color': color,
                'fields': [
                    {'title': 'Verdict', 'value': alert_data['verdict'], 'short': True},
                    {'title': 'Confidence', 'value': f"{alert_data['confidence']:.3f}", 'short': True},
                    {'title': 'Delta S', 'value': f"{alert_data['delta_s']:.5f}", 'short': True},
                    {'title': 'Glyph ID', 'value': alert_data['glyph_id'], 'short': True}
                ],
                'footer': 'EchoScan',
                'ts': int(time.time())
            }]
        }
        
        return self._send_webhook(self.config.slack_url, payload)
    
    def send_teams_notification(self, alert_data: Dict[str, Any]) -> bool:
        """Send notification to Microsoft Teams"""
        if not self.config.teams_url:
            return False
        
        # Format for Teams
        theme_color = {
            'CRITICAL': 'FF0000',
            'WARNING': 'FFA500',
            'INFO': '00FF00'
        }.get(alert_data['alert_level'], '00FF00')
        
        payload = {
            '@type': 'MessageCard',
            '@context': 'http://schema.org/extensions',
            'themeColor': theme_color,
            'summary': f"EchoScan Alert - {alert_data['alert_level']}",
            'sections': [{
                'activityTitle': 'EchoScan Detection Alert',
                'activitySubtitle': f"Level: {alert_data['alert_level']}",
                'facts': [
                    {'name': 'Verdict', 'value': alert_data['verdict']},
                    {'name': 'Confidence', 'value': f"{alert_data['confidence']:.3f}"},
                    {'name': 'Delta S', 'value': f"{alert_data['delta_s']:.5f}"},
                    {'name': 'Timestamp', 'value': alert_data['timestamp']}
                ]
            }]
        }
        
        return self._send_webhook(self.config.teams_url, payload)
    
    def send_lambda_webhook(self, alert_data: Dict[str, Any]) -> bool:
        """Send data to AWS Lambda endpoint"""
        if not self.config.lambda_url:
            return False
        
        # Lambda expects raw JSON data
        payload = {
            'event_type': 'echoscan_alert',
            'data': alert_data
        }
        
        return self._send_webhook(self.config.lambda_url, payload)
    
    def send_siem_event(self, alert_data: Dict[str, Any]) -> bool:
        """Send event to SIEM system"""
        if not self.config.siem_url:
            return False
        
        # Format for SIEM (CEF-like structure)
        payload = {
            'cef_version': '0',
            'device_vendor': 'EchoScan',
            'device_product': 'EchoScan',
            'device_version': '1.0',
            'signature_id': 'ECHO_DETECT',
            'name': f"EchoScan Detection - {alert_data['verdict']}",
            'severity': {'CRITICAL': 10, 'WARNING': 6, 'INFO': 2}.get(alert_data['alert_level'], 2),
            'extensions': {
                'act': 'detection',
                'cs1': alert_data['verdict'],
                'cs1Label': 'Verdict',
                'cs2': alert_data['glyph_id'],
                'cs2Label': 'GlyphID',
                'cs3': f"{alert_data['confidence']:.3f}",
                'cs3Label': 'Confidence',
                'cs4': f"{alert_data['delta_s']:.5f}",
                'cs4Label': 'DeltaS'
            }
        }
        
        return self._send_webhook(self.config.siem_url, payload)
    
    def create_jira_issue(self, alert_data: Dict[str, Any]) -> bool:
        """Create Jira issue for quarantined inputs"""
        if not all([self.config.jira_base_url, self.config.jira_username, self.config.jira_api_token]):
            return False
        
        # Only create issues for critical alerts
        if alert_data['alert_level'] != 'CRITICAL':
            return True  # Not an error, just not applicable
        
        auth = (self.config.jira_username, self.config.jira_api_token)
        url = f"{self.config.jira_base_url}/rest/api/2/issue"
        
        payload = {
            'fields': {
                'project': {'key': self.config.jira_project_key},
                'summary': f"EchoScan Critical Alert - {alert_data['verdict']} detected",
                'description': (
                    f"EchoScan has detected a critical issue:\n\n"
                    f"*Verdict:* {alert_data['verdict']}\n"
                    f"*Confidence:* {alert_data['confidence']:.3f}\n"
                    f"*Delta S:* {alert_data['delta_s']:.5f}\n"
                    f"*Glyph ID:* {alert_data['glyph_id']}\n"
                    f"*Timestamp:* {alert_data['timestamp']}\n\n"
                    f"Please investigate this detected content for potential AI generation or anomalies."
                ),
                'issuetype': {'name': self.config.jira_issue_type},
                'priority': {'name': 'High'},
                'labels': ['echoscan', 'ai-detection', 'security']
            }
        }
        
        try:
            response = self.session.post(
                url, 
                json=payload, 
                auth=auth, 
                timeout=self.config.timeout
            )
            response.raise_for_status()
            logger.info(f"Created Jira issue: {response.json().get('key', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to create Jira issue: {e}")
            return False
    
    def _send_webhook(self, url: str, payload: Dict[str, Any]) -> bool:
        """Generic webhook sender with retry logic"""
        if not url or not self.config.enabled:
            return False
        
        for attempt in range(self.config.retries):
            try:
                response = self.session.post(
                    url, 
                    json=payload, 
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                logger.info(f"Webhook sent successfully to {url[:50]}...")
                return True
            except Exception as e:
                logger.warning(f"Webhook attempt {attempt + 1} failed: {e}")
                if attempt < self.config.retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"All webhook attempts failed for {url[:50]}...")
        return False
    
    def send_all_notifications(self, echoscan_result: Dict[str, Any]) -> Dict[str, bool]:
        """Send notifications to all configured endpoints"""
        if not self.config.enabled:
            return {'enabled': False}
        
        alert_data = self.format_alert_data(echoscan_result)
        
        results = {
            'slack': self.send_slack_notification(alert_data),
            'teams': self.send_teams_notification(alert_data),
            'lambda': self.send_lambda_webhook(alert_data),
            'siem': self.send_siem_event(alert_data),
            'jira': self.create_jira_issue(alert_data)
        }
        
        return results

# Global webhook manager instance
webhook_manager = WebhookManager()

def send_webhook_notifications(echoscan_result: Dict[str, Any]) -> Dict[str, bool]:
    """Convenience function to send notifications"""
    return webhook_manager.send_all_notifications(echoscan_result)

def export_json(echoscan_result: Dict[str, Any], filepath: Optional[str] = None) -> str:
    """Export EchoScan results as JSON"""
    json_data = {
        'export_timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'version': '1.0',
        'source': 'EchoScan',
        'result': echoscan_result
    }
    
    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
    
    if filepath:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
    
    return json_str