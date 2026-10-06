"""add user preferred_language and the assessments / question bank

Revision ID: c9d2f6a1e4b7
Revises: b7e1c4a9d3f5
Create Date: 2026-10-06 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c9d2f6a1e4b7"
down_revision: Union[str, Sequence[str], None] = "b7e1c4a9d3f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "preferred_language",
            sa.Enum("EN", "PT_BR", name="language", native_enum=False, length=32),
            server_default="EN",
            nullable=False,
        ),
    )

    op.create_table('assessments',
    sa.Column('code', sa.String(length=120), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('translations', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column('kind', sa.Enum('COMPETENCY', 'LEARNING_PATH', 'MIXED', name='assessment_kind', native_enum=False, length=32), nullable=False),
    sa.Column('competency_id', sa.UUID(), nullable=True),
    sa.Column('learning_path_id', sa.UUID(), nullable=True),
    sa.Column('pass_threshold', sa.Integer(), server_default='70', nullable=False),
    sa.Column('completion_bonus_xp', sa.Integer(), server_default='25', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('completion_bonus_xp >= 0', name='ck_assessment_bonus_non_negative'),
    sa.CheckConstraint('pass_threshold >= 1 AND pass_threshold <= 100', name='ck_assessment_threshold_range'),
    sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_assessments_competency_id'), 'assessments', ['competency_id'], unique=False)
    op.create_table('questions',
    sa.Column('code', sa.String(length=120), nullable=False),
    sa.Column('competency_id', sa.UUID(), nullable=False),
    sa.Column('type', sa.Enum('MULTIPLE_CHOICE', 'MULTI_SELECT', 'SHORT_ANSWER', 'CODE_READING', name='question_type', native_enum=False, length=32), nullable=False),
    sa.Column('difficulty', sa.Enum('EASY', 'MEDIUM', 'HARD', name='question_difficulty', native_enum=False, length=32), nullable=False),
    sa.Column('xp_value', sa.Integer(), nullable=False),
    sa.Column('correct_option_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
    sa.Column('source', sa.Enum('AI_GENERATED', 'MANUAL', name='question_source', native_enum=False, length=32), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index('ix_questions_competency_active', 'questions', ['competency_id', 'is_active'], unique=False)
    op.create_table('assessment_attempts',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('assessment_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('IN_PROGRESS', 'COMPLETED', name='attempt_status', native_enum=False, length=32), nullable=False),
    sa.Column('question_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('total_questions', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('correct_count', sa.Integer(), nullable=True),
    sa.Column('score_percent', sa.Float(), nullable=True),
    sa.Column('passed', sa.Boolean(), nullable=True),
    sa.Column('xp_awarded', sa.Integer(), nullable=False),
    sa.Column('xp_questions', sa.Integer(), nullable=False),
    sa.Column('xp_bonus', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attempts_user_assessment', 'assessment_attempts', ['user_id', 'assessment_id'], unique=False)
    op.create_index('ix_attempts_user_started_at', 'assessment_attempts', ['user_id', sa.literal_column('started_at DESC')], unique=False)
    op.create_index('uq_attempt_one_open', 'assessment_attempts', ['user_id', 'assessment_id'], unique=True, postgresql_where=sa.text("status = 'IN_PROGRESS'"))
    op.create_table('assessment_questions',
    sa.Column('assessment_id', sa.UUID(), nullable=False),
    sa.Column('question_id', sa.UUID(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('assessment_id', 'question_id')
    )
    op.create_table('question_translations',
    sa.Column('question_id', sa.UUID(), nullable=False),
    sa.Column('language', sa.Enum('EN', 'PT_BR', name='language', native_enum=False, length=32), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('model_answer', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('question_id', 'language', name='uq_question_language')
    )
    op.create_table('question_responses',
    sa.Column('attempt_id', sa.UUID(), nullable=False),
    sa.Column('question_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('answer', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('grading_status', sa.Enum('GRADED', 'PENDING_REVIEW', 'SELF_GRADED', name='grading_status', native_enum=False, length=32), nullable=False),
    sa.Column('is_correct', sa.Boolean(), nullable=True),
    sa.Column('is_first_correct', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('xp_awarded', sa.Integer(), server_default='0', nullable=False),
    sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
    sa.Column('answered_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['attempt_id'], ['assessment_attempts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('attempt_id', 'question_id', name='uq_response_attempt_question')
    )
    op.create_index('ix_responses_user_question', 'question_responses', ['user_id', 'question_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index('ix_responses_user_question', table_name='question_responses')
    op.drop_table('question_responses')
    op.drop_table('question_translations')
    op.drop_table('assessment_questions')
    op.drop_index('uq_attempt_one_open', table_name='assessment_attempts', postgresql_where=sa.text("status = 'IN_PROGRESS'"))
    op.drop_index('ix_attempts_user_started_at', table_name='assessment_attempts')
    op.drop_index('ix_attempts_user_assessment', table_name='assessment_attempts')
    op.drop_table('assessment_attempts')
    op.drop_index('ix_questions_competency_active', table_name='questions')
    op.drop_table('questions')
    op.drop_index(op.f('ix_assessments_competency_id'), table_name='assessments')
    op.drop_table('assessments')
    op.drop_column("users", "preferred_language")
