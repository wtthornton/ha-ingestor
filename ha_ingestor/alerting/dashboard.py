"""Alert dashboard for web-based alert management."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..utils.logging import get_logger
from .alert_manager import AlertManager
from .rules_engine import AlertRule, AlertSeverity


class AlertRuleCreate(BaseModel):
    """Model for creating new alert rules."""

    name: str
    description: str
    severity: str
    enabled: bool = True
    conditions: list[dict[str, Any]] = []
    threshold: float | None = None
    threshold_type: str | None = None
    time_window_minutes: int = 5
    cooldown_minutes: int = 15
    notification_channels: list[str] = []
    tags: dict[str, str] = {}


class AlertRuleUpdate(BaseModel):
    """Model for updating existing alert rules."""

    description: str | None = None
    severity: str | None = None
    enabled: bool | None = None
    conditions: list[dict[str, Any]] | None = None
    threshold: float | None = None
    threshold_type: str | None = None
    time_window_minutes: int | None = None
    cooldown_minutes: int | None = None
    notification_channels: list[str] | None = None
    tags: dict[str, str] | None = None


class AlertAction(BaseModel):
    """Model for alert actions."""

    action: str  # "acknowledge", "resolve"
    rule_name: str


class AlertDashboard:
    """Web dashboard for alert management."""

    def __init__(
        self, alert_manager: AlertManager, templates_dir: str = "templates"
    ) -> None:
        """Initialize the alert dashboard."""
        self.alert_manager = alert_manager
        self.logger = get_logger(__name__)
        self.router = APIRouter(prefix="/alerts", tags=["alerts"])

        # Templates setup
        try:
            self.templates = Jinja2Templates(directory=templates_dir)
        except Exception:
            # Fallback to basic HTML responses if templates are not available
            self.templates = None

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup FastAPI routes for the dashboard."""

        @self.router.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request) -> Response:
            """Main dashboard page."""
            if self.templates:
                return self.templates.TemplateResponse(
                    "alerts_dashboard.html",
                    {"request": request, "title": "Alert Dashboard"},
                )
            else:
                return self._get_basic_dashboard_html()

        @self.router.get("/api/rules")
        async def get_alert_rules() -> list[dict[str, Any]]:
            """Get all alert rules."""
            try:
                rules = self.alert_manager.get_alert_rules()
                return [rule.to_dict() for rule in rules]
            except Exception as e:
                self.logger.error(f"Error getting alert rules: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.post("/api/rules")
        async def create_alert_rule(rule_data: AlertRuleCreate) -> dict[str, Any]:
            """Create a new alert rule."""
            try:
                # Validate severity
                try:
                    severity = AlertSeverity(rule_data.severity)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid severity: {rule_data.severity}",
                    ) from None

                # Create rule
                rule = AlertRule(
                    name=rule_data.name,
                    description=rule_data.description,
                    severity=severity,
                    enabled=rule_data.enabled,
                    conditions=rule_data.conditions,
                    threshold=rule_data.threshold,
                    threshold_type=rule_data.threshold_type,
                    time_window_minutes=rule_data.time_window_minutes,
                    cooldown_minutes=rule_data.cooldown_minutes,
                    notification_channels=rule_data.notification_channels,
                    tags=rule_data.tags,
                )

                self.alert_manager.add_alert_rule(rule)

                return {
                    "success": True,
                    "message": f"Alert rule '{rule_data.name}' created successfully",
                    "rule": rule.to_dict(),
                }

            except Exception as e:
                self.logger.error(f"Error creating alert rule: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.put("/api/rules/{rule_name}")
        async def update_alert_rule(
            rule_name: str, rule_data: AlertRuleUpdate
        ) -> dict[str, Any]:
            """Update an existing alert rule."""
            try:
                rule = self.alert_manager.get_alert_rules()
                existing_rule = next((r for r in rule if r.name == rule_name), None)

                if not existing_rule:
                    raise HTTPException(
                        status_code=404, detail=f"Alert rule '{rule_name}' not found"
                    )

                # Update fields
                if rule_data.description is not None:
                    existing_rule.description = rule_data.description

                if rule_data.severity is not None:
                    try:
                        existing_rule.severity = AlertSeverity(rule_data.severity)
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid severity: {rule_data.severity}",
                        ) from None

                if rule_data.enabled is not None:
                    existing_rule.enabled = rule_data.enabled

                if rule_data.conditions is not None:
                    existing_rule.conditions = rule_data.conditions

                if rule_data.threshold is not None:
                    existing_rule.threshold = rule_data.threshold

                if rule_data.threshold_type is not None:
                    existing_rule.threshold_type = rule_data.threshold_type

                if rule_data.time_window_minutes is not None:
                    existing_rule.time_window_minutes = rule_data.time_window_minutes

                if rule_data.cooldown_minutes is not None:
                    existing_rule.cooldown_minutes = rule_data.cooldown_minutes

                if rule_data.notification_channels is not None:
                    existing_rule.notification_channels = (
                        rule_data.notification_channels
                    )

                if rule_data.tags is not None:
                    existing_rule.tags = rule_data.tags

                # Update timestamp
                existing_rule.update_timestamp()

                return {
                    "success": True,
                    "message": f"Alert rule '{rule_name}' updated successfully",
                    "rule": existing_rule.to_dict(),
                }

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error updating alert rule: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.delete("/api/rules/{rule_name}")
        async def delete_alert_rule(rule_name: str) -> dict[str, Any]:
            """Delete an alert rule."""
            try:
                success = self.alert_manager.remove_alert_rule(rule_name)

                if success:
                    return {
                        "success": True,
                        "message": f"Alert rule '{rule_name}' deleted successfully",
                    }
                else:
                    raise HTTPException(
                        status_code=404, detail=f"Alert rule '{rule_name}' not found"
                    )

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error deleting alert rule: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.get("/api/active")
        async def get_active_alerts() -> list[dict[str, Any]]:
            """Get all currently active alerts."""
            try:
                alerts = self.alert_manager.get_active_alerts()
                return [alert.to_dict() for alert in alerts]
            except Exception as e:
                self.logger.error(f"Error getting active alerts: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.get("/api/history")
        async def get_alert_history(limit: int = 100) -> list[dict[str, Any]]:
            """Get alert history."""
            try:
                history = self.alert_manager.get_alert_history(limit)
                return [entry.to_dict() for entry in history]
            except Exception as e:
                self.logger.error(f"Error getting alert history: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.post("/api/actions")
        async def perform_alert_action(action_data: AlertAction) -> dict[str, Any]:
            """Perform an action on an alert."""
            try:
                if action_data.action == "acknowledge":
                    success = self.alert_manager.acknowledge_alert(
                        action_data.rule_name
                    )
                    if success:
                        return {
                            "success": True,
                            "message": f"Alert '{action_data.rule_name}' acknowledged successfully",
                        }
                    else:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Alert '{action_data.rule_name}' not found",
                        )

                elif action_data.action == "resolve":
                    success = self.alert_manager.resolve_alert(action_data.rule_name)
                    if success:
                        return {
                            "success": True,
                            "message": f"Alert '{action_data.rule_name}' resolved successfully",
                        }
                    else:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Alert '{action_data.rule_name}' not found",
                        )

                else:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid action: {action_data.action}"
                    )

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error performing alert action: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.get("/api/statistics")
        async def get_alert_statistics() -> dict[str, Any]:
            """Get alerting system statistics."""
            try:
                return self.alert_manager.get_statistics()
            except Exception as e:
                self.logger.error(f"Error getting alert statistics: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.get("/api/health")
        async def get_alert_health() -> dict[str, Any]:
            """Get alerting system health status."""
            try:
                stats = self.alert_manager.get_statistics()

                # Determine health status
                is_healthy = (
                    stats["manager"]["is_running"]
                    and len(stats["notifications"]["channel_details"]) > 0
                )

                return {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "timestamp": datetime.now(datetime.UTC).isoformat(),
                    "details": {
                        "manager_running": stats["manager"]["is_running"],
                        "notification_channels": len(
                            stats["notifications"]["channel_details"]
                        ),
                        "active_alerts": stats["rules_engine"]["active_alerts"],
                        "total_rules": stats["rules_engine"]["total_rules"],
                    },
                }

            except Exception as e:
                self.logger.error(f"Error getting alert health: {e}")
                return {
                    "status": "error",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e),
                }

    def _get_basic_dashboard_html(self) -> Response:
        """Generate basic HTML dashboard when templates are not available."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>HA Ingestor - Alert Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #007bff; }
                .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .section h3 { margin-top: 0; color: #007bff; }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
                .stat-card { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007bff; }
                .stat-value { font-size: 24px; font-weight: bold; color: #007bff; }
                .stat-label { color: #666; margin-top: 5px; }
                .button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
                .button:hover { background: #0056b3; }
                .button.danger { background: #dc3545; }
                .button.danger:hover { background: #c82333; }
                .alert-list { max-height: 400px; overflow-y: auto; }
                .alert-item { padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #007bff; background: #f8f9fa; }
                .alert-item.critical { border-left-color: #dc3545; background: #f8d7da; }
                .alert-item.error { border-left-color: #fd7e14; background: #fff3cd; }
                .alert-item.warning { border-left-color: #ffc107; background: #fff3cd; }
                .alert-item.info { border-left-color: #17a2b8; background: #d1ecf1; }
                .form-group { margin-bottom: 15px; }
                .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
                .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                .hidden { display: none; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 HA Ingestor Alert Dashboard</h1>
                    <p>Monitor and manage your Home Assistant alerts</p>
                </div>

                <div class="section">
                    <h3>System Statistics</h3>
                    <div class="stats-grid" id="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value" id="total-rules">-</div>
                            <div class="stat-label">Total Rules</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="active-alerts">-</div>
                            <div class="stat-label">Active Alerts</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="total-alerts">-</div>
                            <div class="stat-label">Total Alerts</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="notifications">-</div>
                            <div class="stat-label">Notifications</div>
                        </div>
                    </div>
                </div>

                <div class="section">
                    <h3>Active Alerts</h3>
                    <div class="alert-list" id="active-alerts-list">
                        <p>Loading active alerts...</p>
                    </div>
                </div>

                <div class="section">
                    <h3>Alert Rules</h3>
                    <button class="button" onclick="showCreateRuleForm()">Create New Rule</button>
                    <div class="alert-list" id="rules-list">
                        <p>Loading alert rules...</p>
                    </div>
                </div>

                <div class="section hidden" id="create-rule-section">
                    <h3>Create Alert Rule</h3>
                    <form id="create-rule-form">
                        <div class="form-group">
                            <label for="rule-name">Rule Name:</label>
                            <input type="text" id="rule-name" name="name" required>
                        </div>
                        <div class="form-group">
                            <label for="rule-description">Description:</label>
                            <textarea id="rule-description" name="description" rows="3" required></textarea>
                        </div>
                        <div class="form-group">
                            <label for="rule-severity">Severity:</label>
                            <select id="rule-severity" name="severity" required>
                                <option value="info">Info</option>
                                <option value="warning">Warning</option>
                                <option value="error">Error</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="rule-enabled">Enabled:</label>
                            <input type="checkbox" id="rule-enabled" name="enabled" checked>
                        </div>
                        <button type="submit" class="button">Create Rule</button>
                        <button type="button" class="button danger" onclick="hideCreateRuleForm()">Cancel</button>
                    </form>
                </div>
            </div>

            <script>
                // Load dashboard data
                document.addEventListener('DOMContentLoaded', function() {
                    loadDashboardData();
                    setInterval(loadDashboardData, 30000); // Refresh every 30 seconds
                });

                function loadDashboardData() {
                    loadStatistics();
                    loadActiveAlerts();
                    loadAlertRules();
                }

                async function loadStatistics() {
                    try {
                        const response = await fetch('/alerts/api/statistics');
                        const stats = await response.json();

                        document.getElementById('total-rules').textContent = stats.rules_engine.total_rules;
                        document.getElementById('active-alerts').textContent = stats.rules_engine.active_alerts;
                        document.getElementById('total-alerts').textContent = stats.rules_engine.total_alerts;
                        document.getElementById('notifications').textContent = stats.manager.total_notifications_sent;
                    } catch (error) {
                        console.error('Error loading statistics:', error);
                    }
                }

                async function loadActiveAlerts() {
                    try {
                        const response = await fetch('/alerts/api/active');
                        const alerts = await response.json();

                        const container = document.getElementById('active-alerts-list');
                        if (alerts.length === 0) {
                            container.innerHTML = '<p>No active alerts</p>';
                            return;
                        }

                        container.innerHTML = alerts.map(alert => `
                            <div class="alert-item ${alert.severity}">
                                <strong>${alert.rule_name}</strong> - ${alert.message}<br>
                                <small>Severity: ${alert.severity.toUpperCase()} | Status: ${alert.status} | Triggered: ${new Date(alert.triggered_at).toLocaleString()}</small>
                                <div style="margin-top: 10px;">
                                    <button class="button" onclick="acknowledgeAlert('${alert.rule_name}')">Acknowledge</button>
                                    <button class="button" onclick="resolveAlert('${alert.rule_name}')">Resolve</button>
                                </div>
                            </div>
                        `).join('');
                    } catch (error) {
                        console.error('Error loading active alerts:', error);
                    }
                }

                async function loadAlertRules() {
                    try {
                        const response = await fetch('/alerts/api/rules');
                        const rules = await response.json();

                        const container = document.getElementById('rules-list');
                        if (rules.length === 0) {
                            container.innerHTML = '<p>No alert rules configured</p>';
                            return;
                        }

                        container.innerHTML = rules.map(rule => `
                            <div class="alert-item">
                                <strong>${rule.name}</strong> - ${rule.description}<br>
                                <small>Severity: ${rule.severity.toUpperCase()} | Enabled: ${rule.enabled ? 'Yes' : 'No'} | Created: ${new Date(rule.created_at).toLocaleString()}</small>
                                <div style="margin-top: 10px;">
                                    <button class="button danger" onclick="deleteRule('${rule.name}')">Delete</button>
                                </div>
                            </div>
                        `).join('');
                    } catch (error) {
                        console.error('Error loading alert rules:', error);
                    }
                }

                async function acknowledgeAlert(ruleName) {
                    try {
                        const response = await fetch('/alerts/api/actions', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({action: 'acknowledge', rule_name: ruleName})
                        });

                        if (response.ok) {
                            loadDashboardData();
                        } else {
                            alert('Error acknowledging alert');
                        }
                    } catch (error) {
                        console.error('Error acknowledging alert:', error);
                    }
                }

                async function resolveAlert(ruleName) {
                    try {
                        const response = await fetch('/alerts/api/actions', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({action: 'resolve', rule_name: ruleName})
                        });

                        if (response.ok) {
                            loadDashboardData();
                        } else {
                            alert('Error resolving alert');
                        }
                    } catch (error) {
                        console.error('Error resolving alert:', error);
                    }
                }

                async function deleteRule(ruleName) {
                    if (!confirm(`Are you sure you want to delete the rule '${ruleName}'?`)) {
                        return;
                    }

                    try {
                        const response = await fetch(`/alerts/api/rules/${ruleName}`, {
                            method: 'DELETE'
                        });

                        if (response.ok) {
                            loadDashboardData();
                        } else {
                            alert('Error deleting rule');
                        }
                    } catch (error) {
                        console.error('Error deleting rule:', error);
                    }
                }

                function showCreateRuleForm() {
                    document.getElementById('create-rule-section').classList.remove('hidden');
                }

                function hideCreateRuleForm() {
                    document.getElementById('create-rule-section').classList.add('hidden');
                    document.getElementById('create-rule-form').reset();
                }

                document.getElementById('create-rule-form').addEventListener('submit', async function(e) {
                    e.preventDefault();

                    const formData = new FormData(e.target);
                    const ruleData = {
                        name: formData.get('name'),
                        description: formData.get('description'),
                        severity: formData.get('severity'),
                        enabled: formData.get('enabled') === 'on'
                    };

                    try {
                        const response = await fetch('/alerts/api/rules', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(ruleData)
                        });

                        if (response.ok) {
                            hideCreateRuleForm();
                            loadDashboardData();
                        } else {
                            alert('Error creating rule');
                        }
                    } catch (error) {
                        console.error('Error creating rule:', error);
                    }
                });
            </script>
        </body>
        </html>
        """

        return Response(content=html_content, media_type="text/html")

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for the dashboard."""
        return self.router
