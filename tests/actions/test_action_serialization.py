from __future__ import annotations

import json
import logging
from typing import Type

import pytest

from great_expectations.checkpoint.actions import (
    APINotificationAction,
    EmailAction,
    MicrosoftTeamsNotificationAction,
    OpsgenieAlertAction,
    SlackNotificationAction,
    SNSNotificationAction,
    UpdateDataDocsAction,
    ValidationAction,
)

logger = logging.getLogger(__name__)


class TestActionSerialization:
    EXAMPLE_SLACK_WEBHOOK = "https://hooks.slack.com/services/test/slack/webhook"
    EXAMPLE_TEAMS_WEBHOOK = "https://hooks.microsoft.com/services/test/teams/webhook"
    EXAMPLE_API_KEY = "testapikey"
    EXAMPLE_SMTP_ADDRESS = "smtp.test.com"
    EXAMPLE_SMTP_PORT = 587
    EXAMPLE_EMAILS = "bob@gmail.com, jim@hotmail.com"
    EXAMPLE_SITE_NAMES = ["one_site", "two_site", "red_site", "blue_site"]
    EXAMPLE_SNS_TOPIC_ARN = "my_test_arn"
    EXAMPLE_URL = "http://www.example.com"

    ACTION_INIT_PARAMS = {
        SlackNotificationAction: {
            "name": "my_slack_action",
            "slack_webhook": EXAMPLE_SLACK_WEBHOOK,
        },
        MicrosoftTeamsNotificationAction: {
            "name": "my_teams_action",
            "teams_webhook": EXAMPLE_TEAMS_WEBHOOK,
        },
        OpsgenieAlertAction: {"name": "my_opsgenie_action", "api_key": EXAMPLE_API_KEY},
        EmailAction: {
            "name": "my_email_action",
            "smtp_address": EXAMPLE_SMTP_ADDRESS,
            "smtp_port": EXAMPLE_SMTP_PORT,
            "receiver_emails": EXAMPLE_EMAILS,
        },
        UpdateDataDocsAction: {"name": "my_data_docs_action", "site_names": EXAMPLE_SITE_NAMES},
        SNSNotificationAction: {"name": "my_sns_action", "sns_topic_arn": EXAMPLE_SNS_TOPIC_ARN},
        APINotificationAction: {"name": "my_api_action", "url": EXAMPLE_URL},
    }

    SERIALIZED_ACTIONS = {
        SlackNotificationAction: {
            "name": "my_slack_action",
            "notify_on": "all",
            "notify_with": None,
            "renderer": {
                "class_name": "SlackRenderer",
                "module_name": "great_expectations.render.renderer.slack_renderer",
            },
            "show_failed_expectations": False,
            "slack_channel": None,
            "slack_token": None,
            "slack_webhook": EXAMPLE_SLACK_WEBHOOK,
            "type": "slack",
        },
        MicrosoftTeamsNotificationAction: {
            "name": "my_teams_action",
            "notify_on": "all",
            "renderer": {
                "class_name": "MicrosoftTeamsRenderer",
                "module_name": "great_expectations.render.renderer.microsoft_teams_renderer",
            },
            "teams_webhook": EXAMPLE_TEAMS_WEBHOOK,
            "type": "microsoft",
        },
        OpsgenieAlertAction: {
            "name": "my_opsgenie_action",
            "api_key": EXAMPLE_API_KEY,
            "notify_on": "failure",
            "priority": "P3",
            "region": None,
            "renderer": {
                "class_name": "OpsgenieRenderer",
                "module_name": "great_expectations.render.renderer.opsgenie_renderer",
            },
            "tags": None,
            "type": "opsgenie",
        },
        EmailAction: {
            "name": "my_email_action",
            "notify_on": "all",
            "notify_with": None,
            "receiver_emails": EXAMPLE_EMAILS,
            "renderer": {
                "class_name": "EmailRenderer",
                "module_name": "great_expectations.render.renderer.email_renderer",
            },
            "sender_alias": None,
            "sender_login": None,
            "sender_password": None,
            "smtp_address": EXAMPLE_SMTP_ADDRESS,
            "smtp_port": str(EXAMPLE_SMTP_PORT),
            "type": "email",
            "use_ssl": None,
            "use_tls": None,
        },
        UpdateDataDocsAction: {
            "name": "my_data_docs_action",
            "site_names": EXAMPLE_SITE_NAMES,
            "type": "update_data_docs",
        },
        SNSNotificationAction: {
            "name": "my_sns_action",
            "sns_message_subject": None,
            "sns_topic_arn": EXAMPLE_SNS_TOPIC_ARN,
            "type": "sns",
        },
        APINotificationAction: {
            "name": "my_api_action",
            "type": "api",
            "url": EXAMPLE_URL,
        },
    }

    @pytest.mark.parametrize(
        "action_class, init_params",
        [(k, v) for k, v in ACTION_INIT_PARAMS.items()],
        ids=[k.__name__ for k in ACTION_INIT_PARAMS],
    )
    @pytest.mark.unit
    def test_action_serialization_and_deserialization(
        self,
        mock_context,
        action_class: Type[ValidationAction],
        init_params: dict,
    ):
        expected = self.SERIALIZED_ACTIONS[action_class]

        action = action_class(**init_params)
        json_dict = action.json()
        actual = json.loads(json_dict)

        assert actual == expected

    @pytest.mark.parametrize(
        "action_class, serialized_action",
        [(k, v) for k, v in SERIALIZED_ACTIONS.items()],
        ids=[k.__name__ for k in SERIALIZED_ACTIONS],
    )
    @pytest.mark.unit
    def test_action_deserialization(
        self, action_class: Type[ValidationAction], serialized_action: dict
    ):
        actual = action_class.parse_obj(serialized_action)
        assert isinstance(actual, action_class)
