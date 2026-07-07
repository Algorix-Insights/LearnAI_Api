from app.infra.repositories.aggregate import (
    BaseSupabaseAggregateRepository,
    BaseSupabaseCompositeRepository,
)


class RoomRepository(BaseSupabaseAggregateRepository):
    table_name = "rooms"
    id_field = "room_id"


class MemberRoomRepository(BaseSupabaseCompositeRepository):
    table_name = "members_rooms"


class RoomNotebookRepository(BaseSupabaseCompositeRepository):
    table_name = "room_notebooks"
