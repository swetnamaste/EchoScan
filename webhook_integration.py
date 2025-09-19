"""
EchoScan Webhook Integration Module
Handles external integrations for anomaly reporting and notifications.
"""

import json
import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import os


class WebhookNotifier:
    """Handle webhook notifications for anomalies and events."""
    
    def __init__(self, webhook_url: Optional[str] = None, slack_webhook: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('ECHOSCAN_WEBHOOK_URL')
        self.slack_webhook = slack_webhook or os.getenv('ECHOSCAN_SLACK_WEBHOOK')
        self.enabled = bool(self.webhook_url or self.slack_webhook)
    
    async def send_anomaly_alert(self, anomaly_type: str, input_data: str, metadata: Dict[str, Any]):
        """Send anomaly alert to configured webhooks."""
        if not self.enabled:
            return {"status": "disabled", "message": "No webhook URLs configured"}
        
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "alert_type": "anomaly_detected",
            "anomaly_type": anomaly_type,
            "input_sample": input_data[:100] + "..." if len(input_data) > 100 else input_data,
            "metadata": metadata,
            "severity": self._determine_severity(anomaly_type, metadata),
            "source": "echoscan_monitoring"
        }
        
        results = {}
        
        # Send to generic webhook
        if self.webhook_url:
            results["webhook"] = await self._send_generic_webhook(alert_data)
        
        # Send to Slack
        if self.slack_webhook:
            results["slack"] = await self._send_slack_notification(alert_data)
        
        return results
    
    async def send_performance_alert(self, operation: str, latency_ms: float, threshold_ms: float):
        """Send performance spike alert."""
        if not self.enabled:
            return {"status": "disabled"}
        
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "alert_type": "performance_spike",
            "operation": operation,
            "latency_ms": latency_ms,
            "threshold_ms": threshold_ms,
            "severity": "high" if latency_ms > threshold_ms * 2 else "medium",
            "source": "echoscan_monitoring"
        }
        
        results = {}
        
        if self.webhook_url:
            results["webhook"] = await self._send_generic_webhook(alert_data)
        
        if self.slack_webhook:
            results["slack"] = await self._send_slack_notification(alert_data)
        
        return results
    
    async def _send_generic_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send to generic webhook endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return {"status": "success", "response_code": response.status}
                    else:
                        return {"status": "error", "response_code": response.status, "error": await response.text()}
        
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _send_slack_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send formatted notification to Slack."""
        try:
            # Format for Slack
            slack_message = self._format_slack_message(data)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_webhook,
                    json=slack_message,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return {"status": "success", "response_code": response.status}
                    else:
                        return {"status": "error", "response_code": response.status, "error": await response.text()}
        
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _format_slack_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format alert data for Slack webhook."""
        if data["alert_type"] == "anomaly_detected":
            return {
                "text": f"🚨 EchoScan Anomaly Detected",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 EchoScan Anomaly Alert"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Type:* {data['anomaly_type']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Severity:* {data['severity']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Time:* {data['timestamp']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Input Sample:* `{data['input_sample']}`"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Details:* ```{json.dumps(data['metadata'], indent=2)}```"
                        }
                    }
                ]
            }
        
        elif data["alert_type"] == "performance_spike":
            return {
                "text": f"⚡ EchoScan Performance Alert",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "⚡ EchoScan Performance Alert"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Operation:* {data['operation']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Latency:* {data['latency_ms']:.2f}ms"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Threshold:* {data['threshold_ms']}ms"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Severity:* {data['severity']}"
                            }
                        ]
                    }
                ]
            }
    
    def _determine_severity(self, anomaly_type: str, metadata: Dict[str, Any]) -> str:
        """Determine alert severity based on anomaly type and metadata."""
        if anomaly_type == "delta_s_drift":
            delta_s = metadata.get("delta_s", 0)
            if delta_s > 0.05:
                return "high"
            elif delta_s > 0.03:
                return "medium"
            else:
                return "low"
        
        elif anomaly_type == "unclassified_glyph":
            return "medium"
        
        elif anomaly_type == "user_feedback":
            return "low"
        
        return "medium"


class SlackIntegration:
    """Specialized Slack integration for rich notifications."""
    
    def __init__(self, webhook_url: Optional[str] = None, bot_token: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('ECHOSCAN_SLACK_WEBHOOK')
        self.bot_token = bot_token or os.getenv('ECHOSCAN_SLACK_BOT_TOKEN')
        self.enabled = bool(self.webhook_url)
    
    async def send_daily_summary(self, stats: Dict[str, Any]):
        """Send daily summary of anomalies and performance."""
        if not self.enabled:
            return {"status": "disabled"}
        
        summary_message = {
            "text": "📊 EchoScan Daily Summary",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 EchoScan Daily Summary"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Date:* {datetime.now().strftime('%Y-%m-%d')}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Total Requests:* {stats.get('total_requests', 0)}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Anomalies Detected:* {stats.get('anomalies_detected', 0)}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Avg Response Time:* {stats.get('avg_response_time', 0):.2f}ms"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Performance Spikes:* {stats.get('perf_spikes', 0)}"
                        }
                    ]
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=summary_message,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return {"status": "success", "response_code": response.status}
        
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global webhook notifier instance
webhook_notifier = WebhookNotifier()
slack_integration = SlackIntegration()


# Async wrapper functions for use in monitoring
async def notify_anomaly(anomaly_type: str, input_data: str, metadata: Dict[str, Any]):
    """Convenience function to send anomaly notification."""
    return await webhook_notifier.send_anomaly_alert(anomaly_type, input_data, metadata)

async def notify_performance_spike(operation: str, latency_ms: float, threshold_ms: float):
    """Convenience function to send performance alert."""
    return await webhook_notifier.send_performance_alert(operation, latency_ms, threshold_ms)


# Synchronous fallback for compatibility
def notify_anomaly_sync(anomaly_type: str, input_data: str, metadata: Dict[str, Any]):
    """Synchronous wrapper for anomaly notification."""
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(notify_anomaly(anomaly_type, input_data, metadata))
    except Exception as e:
        print(f"Webhook notification failed: {e}")
        return {"status": "error", "error": str(e)}