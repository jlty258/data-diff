"""
AlertManager - 告警管理器

支持多种告警渠道：邮件、Webhook、日志等
"""

import logging
import json
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import requests
except ImportError:
    requests = None
    logging.warning("requests is not installed. Webhook/Slack/Dingtalk alerts will not work.")

from data_diff.monitor.monitor import MonitorRule, MonitorResult
from data_diff.utils import getLogger

logger = getLogger(__name__)


class AlertChannel(Enum):
    """告警渠道类型"""
    LOG = "log"  # 日志
    EMAIL = "email"  # 邮件
    WEBHOOK = "webhook"  # Webhook
    SLACK = "slack"  # Slack
    DINGTALK = "dingtalk"  # 钉钉


@dataclass
class AlertConfig:
    """告警配置"""
    channel: AlertChannel
    enabled: bool = True
    # 渠道特定配置
    config: Dict[str, Any] = field(default_factory=dict)


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.channels: Dict[AlertChannel, AlertConfig] = {}
        self.alert_history: List[Dict[str, Any]] = []
    
    def add_channel(self, channel: AlertChannel, config: Optional[Dict[str, Any]] = None) -> None:
        """添加告警渠道"""
        self.channels[channel] = AlertConfig(
            channel=channel,
            enabled=True,
            config=config or {}
        )
        logger.info(f"添加告警渠道: {channel.value}")
    
    def remove_channel(self, channel: AlertChannel) -> None:
        """移除告警渠道"""
        if channel in self.channels:
            del self.channels[channel]
            logger.info(f"移除告警渠道: {channel.value}")
    
    def send_alert(self, rule: MonitorRule, result: MonitorResult) -> None:
        """发送告警"""
        if not result.triggered:
            return
        
        alert_data = {
            "rule_name": rule.name,
            "timestamp": result.timestamp.isoformat(),
            "diff_count": result.diff_count,
            "diff_percent": result.diff_percent,
            "row_count_table1": result.row_count_table1,
            "row_count_table2": result.row_count_table2,
            "stats": result.stats,
            "error": result.error
        }
        
        # 记录告警历史
        self.alert_history.append(alert_data)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # 发送到各个渠道
        for channel_type, config in self.channels.items():
            if not config.enabled:
                continue
            
            try:
                if channel_type == AlertChannel.LOG:
                    self._send_log_alert(rule, result)
                elif channel_type == AlertChannel.EMAIL:
                    self._send_email_alert(rule, result, config.config)
                elif channel_type == AlertChannel.WEBHOOK:
                    self._send_webhook_alert(rule, result, config.config)
                elif channel_type == AlertChannel.SLACK:
                    self._send_slack_alert(rule, result, config.config)
                elif channel_type == AlertChannel.DINGTALK:
                    self._send_dingtalk_alert(rule, result, config.config)
            except Exception as e:
                logger.error(f"发送告警到 {channel_type.value} 时出错: {e}", exc_info=True)
    
    def _send_log_alert(self, rule: MonitorRule, result: MonitorResult) -> None:
        """发送日志告警"""
        logger.warning(
            f"🚨 监控告警 - 规则: {rule.name}\n"
            f"  差异数量: {result.diff_count}\n"
            f"  差异百分比: {result.diff_percent:.2f}%\n"
            f"  表1行数: {result.row_count_table1}\n"
            f"  表2行数: {result.row_count_table2}\n"
            f"  时间: {result.timestamp}"
        )
    
    def _send_email_alert(self, rule: MonitorRule, result: MonitorResult, config: Dict[str, Any]) -> None:
        """发送邮件告警"""
        smtp_host = config.get("smtp_host", "localhost")
        smtp_port = config.get("smtp_port", 25)
        smtp_user = config.get("smtp_user")
        smtp_password = config.get("smtp_password")
        from_email = config.get("from_email", "data-monitor@example.com")
        to_emails = config.get("to_emails", [])
        
        if not to_emails:
            logger.warning("邮件告警未配置收件人")
            return
        
        subject = f"数据监控告警: {rule.name}"
        body = f"""
监控规则: {rule.name}
描述: {rule.description or '无'}

告警详情:
- 差异数量: {result.diff_count}
- 差异百分比: {result.diff_percent:.2f}%
- 表1行数: {result.row_count_table1}
- 表2行数: {result.row_count_table2}
- 执行时间: {result.timestamp}
- 耗时: {result.duration_seconds:.2f}秒

统计信息:
{json.dumps(result.stats, indent=2, ensure_ascii=False)}
"""
        
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if smtp_user and smtp_password:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
            logger.info(f"邮件告警已发送到: {to_emails}")
        except Exception as e:
            logger.error(f"发送邮件告警失败: {e}")
    
    def _send_webhook_alert(self, rule: MonitorRule, result: MonitorResult, config: Dict[str, Any]) -> None:
        """发送 Webhook 告警"""
        if requests is None:
            logger.error("requests 库未安装，无法发送 Webhook 告警")
            return
        
        webhook_url = config.get("url")
        if not webhook_url:
            logger.warning("Webhook 告警未配置 URL")
            return
        
        payload = {
            "rule_name": rule.name,
            "description": rule.description,
            "timestamp": result.timestamp.isoformat(),
            "diff_count": result.diff_count,
            "diff_percent": result.diff_percent,
            "row_count_table1": result.row_count_table1,
            "row_count_table2": result.row_count_table2,
            "stats": result.stats,
            "error": result.error
        }
        
        headers = config.get("headers", {"Content-Type": "application/json"})
        timeout = config.get("timeout", 10)
        
        try:
            response = requests.post(webhook_url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Webhook 告警已发送到: {webhook_url}")
        except Exception as e:
            logger.error(f"发送 Webhook 告警失败: {e}")
    
    def _send_slack_alert(self, rule: MonitorRule, result: MonitorResult, config: Dict[str, Any]) -> None:
        """发送 Slack 告警"""
        if requests is None:
            logger.error("requests 库未安装，无法发送 Slack 告警")
            return
        
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.warning("Slack 告警未配置 webhook_url")
            return
        
        # Slack 消息格式
        text = f"🚨 *数据监控告警*\n\n"
        text += f"*规则名称:* {rule.name}\n"
        text += f"*差异数量:* {result.diff_count}\n"
        text += f"*差异百分比:* {result.diff_percent:.2f}%\n"
        text += f"*表1行数:* {result.row_count_table1}\n"
        text += f"*表2行数:* {result.row_count_table2}\n"
        text += f"*时间:* {result.timestamp}"
        
        payload = {"text": text}
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Slack 告警已发送")
        except Exception as e:
            logger.error(f"发送 Slack 告警失败: {e}")
    
    def _send_dingtalk_alert(self, rule: MonitorRule, result: MonitorResult, config: Dict[str, Any]) -> None:
        """发送钉钉告警"""
        if requests is None:
            logger.error("requests 库未安装，无法发送钉钉告警")
            return
        
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.warning("钉钉告警未配置 webhook_url")
            return
        
        text = f"🚨 数据监控告警\n\n"
        text += f"规则名称: {rule.name}\n"
        text += f"差异数量: {result.diff_count}\n"
        text += f"差异百分比: {result.diff_percent:.2f}%\n"
        text += f"表1行数: {result.row_count_table1}\n"
        text += f"表2行数: {result.row_count_table2}\n"
        text += f"时间: {result.timestamp}"
        
        payload = {
            "msgtype": "text",
            "text": {
                "content": text
            }
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("钉钉告警已发送")
        except Exception as e:
            logger.error(f"发送钉钉告警失败: {e}")
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取告警历史"""
        return self.alert_history[-limit:]

