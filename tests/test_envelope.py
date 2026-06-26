from hospitalstar_sdk.models import ApiEnvelope


def test_code_zero_takes_precedence_over_non_success_resp_code() -> None:
    envelope = ApiEnvelope.model_validate({"code": "0", "respCode": "999002", "message": "成功"})

    assert envelope.ok
