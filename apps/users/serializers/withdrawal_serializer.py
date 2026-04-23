from __future__ import annotations

from rest_framework import serializers

from apps.users.models import Withdrawal


class WithdrawalSerializer(serializers.Serializer[Withdrawal]):
    reason = serializers.ChoiceField(choices=Withdrawal.Reason.choices)
    reason_detail = serializers.CharField(required=False, default="", allow_blank=True)
