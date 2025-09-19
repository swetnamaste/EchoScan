"""
Tests for EchoScan Webhook Integration
"""

import pytest
import os
import json
from unittest.mock import patch, Mock
from webhook_integration import WebhookManager, export_json
from excitement_layer import generate_excitement_triggers


class TestWebhookIntegration:
    """Test webhook integration functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.sample_result = {
            'verdict': 'Hallucination',
            'confidence': 0.85,
            'echo_sense': 0.72,
            'delta_s': 0.06,
            'glyph_id': 'TEST-1234',
            'vault_permission': False,
            'input': 'This is a test message'
        }
    
    def test_webhook_manager_initialization(self):
        """Test webhook manager initializes correctly"""
        manager = WebhookManager()
        assert manager.config is not None
        assert manager.session is not None
    
    def test_format_alert_data(self):
        """Test alert data formatting"""
        manager = WebhookManager()
        alert_data = manager.format_alert_data(self.sample_result)
        
        assert alert_data['source'] == 'EchoScan'
        assert alert_data['verdict'] == 'Hallucination'
        assert alert_data['alert_level'] == 'CRITICAL'
        assert 'timestamp' in alert_data
        assert alert_data['glyph_id'] == 'TEST-1234'
    
    def test_alert_level_determination(self):
        """Test alert level is determined correctly"""
        manager = WebhookManager()
        
        # Critical case
        critical_result = self.sample_result.copy()
        critical_result['verdict'] = 'Hallucination'
        alert_data = manager.format_alert_data(critical_result)
        assert alert_data['alert_level'] == 'CRITICAL'
        
        # Warning case
        warning_result = self.sample_result.copy()
        warning_result['verdict'] = 'Plausible'
        warning_result['echo_sense'] = 0.4
        alert_data = manager.format_alert_data(warning_result)
        assert alert_data['alert_level'] == 'WARNING'
        
        # Info case
        info_result = self.sample_result.copy()
        info_result['verdict'] = 'Authentic'
        info_result['echo_sense'] = 0.9
        info_result['delta_s'] = 0.001
        alert_data = manager.format_alert_data(info_result)
        assert alert_data['alert_level'] == 'INFO'
    
    @patch('webhook_integration.requests.Session.post')
    def test_send_slack_notification(self, mock_post):
        """Test Slack notification sending"""
        mock_post.return_value.raise_for_status = Mock()
        
        manager = WebhookManager()
        # Set a mock URL
        manager.config.slack_url = "https://hooks.slack.com/test"
        
        alert_data = manager.format_alert_data(self.sample_result)
        result = manager.send_slack_notification(alert_data)
        
        assert mock_post.called
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        
        assert 'text' in payload
        assert 'attachments' in payload
        assert payload['attachments'][0]['color'] == 'danger'  # Critical alert
    
    @patch('webhook_integration.requests.Session.post')
    def test_send_teams_notification(self, mock_post):
        """Test Teams notification sending"""
        mock_post.return_value.raise_for_status = Mock()
        
        manager = WebhookManager()
        manager.config.teams_url = "https://teams.test.com/webhook"
        
        alert_data = manager.format_alert_data(self.sample_result)
        result = manager.send_teams_notification(alert_data)
        
        assert mock_post.called
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        
        assert payload['@type'] == 'MessageCard'
        assert payload['themeColor'] == 'FF0000'  # Red for critical
    
    @patch('webhook_integration.requests.Session.post')
    def test_jira_issue_creation(self, mock_post):
        """Test Jira issue creation for critical alerts"""
        mock_response = Mock()
        mock_response.json.return_value = {'key': 'ECHO-123'}
        mock_post.return_value = mock_response
        mock_post.return_value.raise_for_status = Mock()
        
        manager = WebhookManager()
        manager.config.jira_base_url = "https://test.atlassian.net"
        manager.config.jira_username = "test@example.com"
        manager.config.jira_api_token = "test-token"
        
        alert_data = manager.format_alert_data(self.sample_result)
        result = manager.create_jira_issue(alert_data)
        
        assert result == True
        assert mock_post.called
        
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        
        assert 'fields' in payload
        assert 'EchoScan Critical Alert' in payload['fields']['summary']
    
    def test_export_json_functionality(self):
        """Test JSON export functionality"""
        json_str = export_json(self.sample_result)
        
        exported_data = json.loads(json_str)
        assert exported_data['source'] == 'EchoScan'
        assert exported_data['version'] == '1.0'
        assert 'export_timestamp' in exported_data
        assert exported_data['result'] == self.sample_result
    
    @patch('webhook_integration.open', create=True)
    def test_export_json_to_file(self, mock_open):
        """Test JSON export to file"""
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        filepath = "/tmp/test_export.json"
        json_str = export_json(self.sample_result, filepath)
        
        assert mock_open.called
        assert mock_file.write.called
        
        # Verify the content written to file
        written_content = mock_file.write.call_args[0][0]
        exported_data = json.loads(written_content)
        assert exported_data['result'] == self.sample_result


class TestExcitementLayer:
    """Test excitement layer functionality"""
    
    def test_excitement_triggers_authentic(self):
        """Test excitement triggers for authentic content"""
        from excitement_layer import generate_excitement_triggers
        
        triggers = generate_excitement_triggers('Authentic', 0.9, 0.85)
        
        assert triggers['excitement_enabled'] == True
        assert triggers['verdict'] == 'Authentic'
        assert len(triggers['triggers']) >= 2  # Should have confetti and fireworks
        
        # Check for confetti trigger
        confetti_triggers = [t for t in triggers['triggers'] if t['type'] == 'confetti']
        assert len(confetti_triggers) > 0
        assert confetti_triggers[0]['intensity'] == 'high'
    
    def test_excitement_triggers_hallucination(self):
        """Test excitement triggers for hallucination detection"""
        from excitement_layer import generate_excitement_triggers
        
        triggers = generate_excitement_triggers('Hallucination', 0.8, 0.6)
        
        assert triggers['excitement_enabled'] == True
        assert triggers['verdict'] == 'Hallucination'
        
        # Check for warning-style triggers
        confetti_triggers = [t for t in triggers['triggers'] if t['type'] == 'confetti']
        if confetti_triggers:
            assert '#FF4500' in confetti_triggers[0]['colors'] or '#FF6347' in confetti_triggers[0]['colors']
    
    def test_excitement_disabled(self):
        """Test excitement layer when disabled"""
        from excitement_layer import generate_excitement_triggers
        
        # Mock environment variable
        with patch.dict(os.environ, {'UI_EXCITEMENT_ENABLED': 'false'}):
            triggers = generate_excitement_triggers('Authentic', 0.9, 0.85)
            assert triggers['excitement_enabled'] == False
    
    def test_high_echo_sense_bonus(self):
        """Test sparkles trigger for high echo_sense scores"""
        from excitement_layer import generate_excitement_triggers
        
        triggers = generate_excitement_triggers('Plausible', 0.7, 0.95)  # Very high echo_sense
        
        # Should have sparkles trigger
        sparkle_triggers = [t for t in triggers['triggers'] if t['type'] == 'sparkles']
        assert len(sparkle_triggers) > 0
        assert 'Exceptional EchoSense Score' in sparkle_triggers[0]['message']


class TestAdaptiveML:
    """Test adaptive ML functionality"""
    
    def test_adaptive_sbsm_analysis(self):
        """Test adaptive SBSM analysis"""
        from adaptive_sbsm import adaptive_sbsm_analysis
        
        sbsm_result = {
            'fold_vector': [0.5] * 16,
            'source_classification': 'Human-Generated',
            'confidence': 0.8,
            'input': 'test input'
        }
        
        detector_results = {
            'sbsm': sbsm_result,
            'echosense': {'echo_sense': 0.7}
        }
        
        result = adaptive_sbsm_analysis(sbsm_result, detector_results)
        
        assert 'adaptive_confidences' in result
        assert 'detector_agreement' in result
        assert 'paradox_analysis' in result
        assert 'ml_drift_immunity' in result
        
        # Check adaptive confidences
        confidences = result['adaptive_confidences']
        assert 'human_generated' in confidences
        assert 'ai_generated' in confidences
        assert 'questionable' in confidences
    
    def test_ml_drift_immunity_status(self):
        """Test ML drift immunity status reporting"""
        from adaptive_sbsm import get_ml_drift_immunity_status
        
        status = get_ml_drift_immunity_status()
        
        assert 'adaptive_refresh_enabled' in status
        assert 'reference_vectors_loaded' in status
        assert 'immunity_level' in status
        assert status['immunity_level'] in ['HIGH', 'MODERATE', 'LOW']
    
    def test_paradox_synthesis(self):
        """Test paradox synthesis functionality"""
        from adaptive_sbsm import paradox_hooks
        
        result = paradox_hooks.paradox_synthesis("test input", [0.6] * 16)
        
        assert 'forward_binding' in result
        assert 'backward_binding' in result
        assert 'synthesis_score' in result
        assert 'paradox_resolved' in result
        
        # Check forward binding
        forward = result['forward_binding']
        assert forward['binding_type'] == 'forward'
        assert 'paradox_id' in forward
        assert 'binding_strength' in forward


if __name__ == '__main__':
    pytest.main([__file__])