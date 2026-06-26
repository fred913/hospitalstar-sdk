"""Pydantic models for the report viewing APIs."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SDKModel(BaseModel):
    """Base model that keeps original API field aliases intact."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def to_api_payload(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class ApiEnvelope(SDKModel, Generic[T]):
    code: int | str | None = None
    message: str | None = None
    msg: str | None = None
    err_msg: str | None = Field(default=None, alias="errMsg")
    resp_code: int | str | None = Field(default=None, alias="respCode")
    sign_content: str | None = Field(default=None, alias="signContent")
    result: T | None = None
    data: Any | None = None

    @property
    def ok(self) -> bool:
        success_codes = {0, 1, 200, "0", "1", "200", "success", "SUCCESS"}
        if self.code is not None:
            return self.code in success_codes
        if self.code is None and self.resp_code is None:
            return True
        if self.resp_code is not None and self.resp_code not in success_codes:
            return False
        return True

    @property
    def error_message(self) -> str:
        return self.message or self.msg or self.err_msg or "request failed"


class ReportPageRequest(SDKModel):
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    sys_code: str = Field(alias="sysCode")
    current_page: int = Field(default=1, alias="currentPage", ge=1)
    page_size: int = Field(default=15, alias="pageSize", ge=1)


class PatientReportListRequest(ReportPageRequest):
    account_id: str | None = Field(default=None, alias="accountId")
    account_type: str | None = Field(default=None, alias="accountType")
    bar_code: str = Field(default="", alias="barCode")
    hos_id: str | None = Field(default=None, alias="hosId")
    patient_binding_id: str | None = Field(default=None, alias="id")
    id_card: str = Field(default="", alias="idCard")
    pat_name: str | None = Field(default=None, alias="patName")


class CheckoutReportListRequest(PatientReportListRequest):
    """List lab reports."""


class ExamineReportListRequest(PatientReportListRequest):
    """List exam reports."""


class MedicalReportListRequest(SDKModel):
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    sys_code: str = Field(alias="sysCode")
    patient_id: str = Field(alias="patientId")


class ScanReportListRequest(ReportPageRequest):
    content: str
    hos_patient_id_encry: str = Field(alias="hosPatientIdEncry")


class CheckoutReportDetailRequest(SDKModel):
    hos_id: str | None = Field(default=None, alias="hosId")
    item_no: str | None = Field(default=None, alias="itemNo")
    rep_id: str = Field(alias="repId")
    rep_type: str = Field(default="1", alias="repType")
    sys_code: str = Field(alias="sysCode")
    visit_no: str | None = Field(default=None, alias="visitNo")
    checkout_type: str | None = Field(default=None, alias="checkoutType")
    rep_id_sign: str | None = Field(default=None, alias="repIdSign")


class ExamineReportDetailRequest(SDKModel):
    act_number: str = Field(default="", alias="actNumber")
    hos_id: str = Field(default="", alias="hosId")
    rep_id: str = Field(default="", alias="repId")
    rep_time: str = Field(default="", alias="repTime")
    sys_code: str = Field(alias="sysCode")
    rep_id_sign: str = Field(default="", alias="repIdSign")
    content: str | None = None


class SharedExamineReportDetailRequest(ExamineReportDetailRequest):
    generated_time: str | None = Field(default=None, alias="generatedTime")
    share_type: str = Field(default="1", alias="shareType")


class MedicalReportDetailsRequest(SDKModel):
    hos_patient_id: str = Field(alias="hosPatientId")
    rep_id: str = Field(alias="repId")
    rep_time: str = Field(alias="repTime")
    hos_id: str = Field(alias="hosId")
    data_source: str | None = Field(default=None, alias="dataSource")
    sys_code: str = Field(alias="sysCode")


class CheckoutReportItem(SDKModel):
    hos_name: str | None = Field(default=None, alias="hosName")
    hos_id: str | None = Field(default=None, alias="hosId")
    part_date: str | None = Field(default=None, alias="partDate")
    item_no: str | None = Field(default=None, alias="itemNo")
    item_name: str | None = Field(default=None, alias="itemName")
    rep_id: str | None = Field(default=None, alias="repId")
    rep_type: str | None = Field(default=None, alias="repType")
    rep_time: str | None = Field(default=None, alias="repTime")
    visit_no: str | None = Field(default=None, alias="visitNo")
    checkout_type: str | None = Field(default=None, alias="checkoutType")
    rep_id_sign: str | None = Field(default=None, alias="repIdSign")


class CheckoutReportGroup(SDKModel):
    checkout_report_list_result_list: list[CheckoutReportItem] = Field(
        default_factory=list,
        alias="checkoutReportListResultList",
    )


class CheckoutReportDateGroup(SDKModel):
    date: str | None = None
    checkout_report_list: list[CheckoutReportGroup] = Field(
        default_factory=list,
        alias="checkoutReportList",
    )


class ExamineReportItem(SDKModel):
    act_number: str | None = Field(default=None, alias="actNumber")
    generated_time: str | None = Field(default=None, alias="generatedTime")
    hos_name: str | None = Field(default=None, alias="hosName")
    hos_id: str | None = Field(default=None, alias="hosId")
    part_date: str | None = Field(default=None, alias="partDate")
    rep_id: str | None = Field(default=None, alias="repId")
    rep_id_sign: str | None = Field(default=None, alias="repIdSign")
    rep_name: str | None = Field(default=None, alias="repName")
    rep_time: str | None = Field(default=None, alias="repTime")
    report_type: str | None = Field(default=None, alias="reportType")
    dicom_list: list[str] | None = Field(default=None, alias="dicomList")


class ExamineReportGroup(SDKModel):
    examine_report_list: list[ExamineReportItem] = Field(default_factory=list, alias="examineReportList")


class ExamineReportDateGroup(SDKModel):
    date: str | None = None
    examine_report_map_list: list[ExamineReportGroup] = Field(
        default_factory=list,
        alias="examineReportMapList",
    )


class LabNormalItem(SDKModel):
    item_name: str | None = Field(default=None, alias="itemName")
    item_result: str | None = Field(default=None, alias="itemResult")
    result: str | None = None
    unit: str | None = None
    reference_range: str | None = Field(default=None, alias="referenceRange")
    flag: str = ""
    image_flag: int | str | None = Field(default=None, alias="imageFlag")


class LabAntiItem(SDKModel):
    anti_list: list[Any] = Field(default_factory=list, alias="antiList")


class CheckoutReportScheme(SDKModel):
    hos_id: str | None = Field(default=None, alias="hosId")
    patient_name: str | None = Field(default=None, alias="patientName")
    rep_id: str | None = Field(default=None, alias="repId")
    normal_list: list[LabNormalItem] = Field(default_factory=list, alias="normalList")
    anti_item_result: list[LabAntiItem] = Field(default_factory=list, alias="antiItemResult")


class CheckoutReportDetailsResult(SDKModel):
    scheme: CheckoutReportScheme | dict[str, Any] | None = None


class ExamineReportDetailItem(SDKModel):
    apply_time: str | None = Field(default=None, alias="applyTime")
    approve_doc: str | None = Field(default=None, alias="approveDoc")
    description: str | None = None
    diagnosis: str | None = None
    dicom_list: list[str] = Field(default_factory=list, alias="dicomList")
    doc_name: str | None = Field(default=None, alias="docName")
    part: str | None = None
    reg_time: str | None = Field(default=None, alias="regTime")
    rep_id: str | None = Field(default=None, alias="repId")
    rep_id_sign: str | None = Field(default=None, alias="repIdSign")
    rep_name: str | None = Field(default=None, alias="repName")
    rep_time: str | None = Field(default=None, alias="repTime")
    suggest: str | None = None


class ExamineReportDetailsResult(SDKModel):
    details_result: list[ExamineReportDetailItem] = Field(default_factory=list, alias="detailsResult")
    patient_name: str | None = Field(default=None, alias="patientName")
    hos_patient_id: str | None = Field(default=None, alias="hosPatientId")
    dicom_list: list[str] = Field(default_factory=list, alias="dicomList")


class MedicalReportSummary(SDKModel):
    hos_id: str | None = Field(default=None, alias="hosId")
    hos_patient_id: str | None = Field(default=None, alias="hosPatientId")
    data_source: str | None = Field(default=None, alias="dataSource")
    rep_id: str | None = Field(default=None, alias="repId")
    rep_name: str | None = Field(default=None, alias="repName")
    rep_time: str | None = Field(default=None, alias="repTime")
    sys_code: str | None = Field(default=None, alias="sysCode")


class MedicalReportDetailsResult(SDKModel):
    patient_name: str | None = Field(default=None, alias="patientName")
    name: str | None = None
    rep_id: str | None = Field(default=None, alias="repId")
    rep_name: str | None = Field(default=None, alias="repName")
    rep_time: str | None = Field(default=None, alias="repTime")
    report_doc: str | None = Field(default=None, alias="reportDoc")
    conclusion: str | None = None
    collect: str | None = None
    suggest: str | None = None
