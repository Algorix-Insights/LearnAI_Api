from app.infra.repositories.aggregate import BaseSupabaseAggregateRepository


class StudyMemberRepository(BaseSupabaseAggregateRepository):
    table_name = "study_members"
    id_field = "member_id"
