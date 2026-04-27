from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.users.models import Withdrawal


class WithdrawalSerializer(serializers.Serializer[Withdrawal]):
    reason = serializers.ChoiceField(choices=Withdrawal.Reason.choices)
    reason_detail = serializers.CharField(required=False, default="", allow_blank=True)


class RestoreSerializer(serializers.Serializer[Any]):
    email_token = serializers.CharField()
