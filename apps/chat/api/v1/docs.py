from drf_spectacular.utils import OpenApiResponse, extend_schema

conversation_list_schema = extend_schema(
    summary="List Conversations (Inbox)",
    description="Retrieve all conversations for the authenticated user (patient or doctor). Includes unread count.",
    tags=["Chat"]
)

conversation_detail_schema = extend_schema(
    summary="Get Conversation Detail",
    description="Fetch a specific conversation's details and pointers.",
    tags=["Chat"]
)

message_list_schema = extend_schema(
    summary="Get Message History",
    description="Get paginated history of messages using Cursor Pagination. Deleted messages are masked.",
    tags=["Chat"]
)

message_create_schema = extend_schema(
    summary="Send Message",
    description="Send a text, image, or document message. Requires an active online appointment for patients.",
    tags=["Chat"]
)

message_delete_schema = extend_schema(
    summary="Delete Message",
    description="Soft delete a message. **ONLY the doctor can perform this action.**",
    responses={
        204: OpenApiResponse(description="Message deleted successfully."),
        403: OpenApiResponse(description="Permission Denied (Patient trying to delete).")
    },
    tags=["Chat"]
)

update_read_pointer_schema = extend_schema(
    summary="Update Read Pointer",
    description="Update the patient or doctor's last read message pointer. This automatically updates the unread_count.",
    responses={200: OpenApiResponse(description="Pointer updated successfully.")},
    tags=["Chat"]
)


