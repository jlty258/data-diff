"""
MonitorScheduler - 监控调度器

支持基于 cron 表达式的定时调度
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional

try:
    from croniter import croniter
except ImportError:
    raise ImportError("croniter is required for MonitorScheduler. Install it with: pip install croniter")

from data_diff.monitor.monitor import DataMonitor, MonitorRule, MonitorResult
from data_diff.monitor.alert import AlertManager
from data_diff.utils import getLogger

logger = getLogger(__name__)


class MonitorScheduler:
    """监控调度器"""
    
    def __init__(self, monitor: DataMonitor, alert_manager: Optional[AlertManager] = None):
        self.monitor = monitor
        self.alert_manager = alert_manager
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._schedule_times: Dict[str, datetime] = {}
    
    def start(self) -> None:
        """启动调度器"""
        if self._running:
            logger.warning("调度器已在运行")
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        logger.info("监控调度器已启动")
    
    def stop(self) -> None:
        """停止调度器"""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("监控调度器已停止")
    
    def _run_scheduler(self) -> None:
        """调度器主循环"""
        while self._running and not self._stop_event.is_set():
            try:
                now = datetime.now()
                rules = self.monitor.list_rules()
                
                for rule in rules:
                    if not rule.enabled or not rule.schedule:
                        continue
                    
                    # 检查是否到了执行时间
                    if self._should_run(rule, now):
                        logger.info(f"执行定时监控: {rule.name}")
                        result = self.monitor.run_monitor(rule.name)
                        
                        # 如果触发阈值，发送告警
                        if result and result.triggered and self.alert_manager:
                            self.alert_manager.send_alert(rule, result)
                
                # 每秒检查一次
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"调度器运行时出错: {e}", exc_info=True)
                time.sleep(5)  # 出错后等待5秒再继续
    
    def _should_run(self, rule: MonitorRule, now: datetime) -> bool:
        """检查规则是否应该执行"""
        rule_name = rule.name
        
        try:
            # 获取上次执行时间
            last_run = self._schedule_times.get(rule_name)
            
            if last_run is None:
                # 第一次运行，计算下次执行时间
                cron = croniter(rule.schedule, now)
                next_run = cron.get_next(datetime)
                self._schedule_times[rule_name] = next_run
                return False
            
            # 检查是否到了执行时间
            if now >= last_run:
                # 计算下次执行时间
                cron = croniter(rule.schedule, now)
                next_run = cron.get_next(datetime)
                self._schedule_times[rule_name] = next_run
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"解析 cron 表达式 '{rule.schedule}' 时出错: {e}")
            return False
    
    def trigger_now(self, rule_name: str) -> Optional[MonitorResult]:
        """立即触发执行某个规则"""
        logger.info(f"手动触发监控: {rule_name}")
        result = self.monitor.run_monitor(rule_name)
        
        if result and result.triggered and self.alert_manager:
            rule = self.monitor.get_rule(rule_name)
            if rule:
                self.alert_manager.send_alert(rule, result)
        
        return result
    
    def get_next_run_time(self, rule_name: str) -> Optional[datetime]:
        """获取规则的下次执行时间"""
        return self._schedule_times.get(rule_name)

