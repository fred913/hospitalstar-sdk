from hospitalstar_sdk.models import (
    ApiEnvelope,
    CheckoutReportListRequest,
    ExamineReportDetailsResult,
)


def test_request_model_serializes_original_aliases() -> None:
    request = CheckoutReportListRequest(
        accountId="card-1",
        accountType="01",
        endDate="2026-06-26",
        hosId="129163",
        id="patient-1",
        patName="Test Patient",
        startDate="2025-06-26",
        sysCode="1001017",
        currentPage=2,
        pageSize=30,
    )

    payload = request.to_api_payload()

    assert payload["accountId"] == "card-1"
    assert payload["currentPage"] == 2
    assert payload["id"] == "patient-1"
    assert "patient_binding_id" not in payload


def test_response_envelope_parses_nested_report_details() -> None:
    envelope = ApiEnvelope[ExamineReportDetailsResult].model_validate(
        {
            "code": 0,
            "result": {
                "patientName": "Test Patient",
                "detailsResult": [
                    {
                        "repName": "CT",
                        "description": "No abnormality",
                        "dicomList": ["dicom-1"],
                    }
                ],
            },
        }
    )

    assert envelope.ok
    assert envelope.result is not None
    assert envelope.result.patient_name == "Test Patient"
    assert envelope.result.details_result[0].rep_name == "CT"

