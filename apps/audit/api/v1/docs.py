from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)

from apps.audit.api.v1.serializers import AuditLogReadSerializer

audit_log_list_schema = extend_schema(
    summary="List visible audit logs",
    description="Returns audit logs visible to the authenticated user.",
    responses={200: AuditLogReadSerializer(many=True)},
    tags=["Audit"],
)


my_audit_logs_schema = extend_schema(
    summary="List my audit logs",
    responses={200: AuditLogReadSerializer(many=True)},
    tags=["Audit"],
)


organization_audit_logs_schema = extend_schema(
    summary="List organization audit logs",
    parameters=[
        OpenApiParameter(
            name="organization_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )
    ],
    responses={
        200: AuditLogReadSerializer(many=True),
        403: OpenApiResponse(description="Permission denied."),
        404: OpenApiResponse(description="Organization not found."),
    },
    tags=["Audit"],
)


audit_log_detail_schema = extend_schema(
    summary="Retrieve audit log",
    responses={
        200: AuditLogReadSerializer,
        403: OpenApiResponse(description="Permission denied."),
        404: OpenApiResponse(description="Audit log not found."),
    },
    tags=["Audit"],
)
