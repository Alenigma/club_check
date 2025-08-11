from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0001_init'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(), unique=True, index=True),
        sa.Column('full_name', sa.String()),
        sa.Column('hashed_password', sa.String()),
        sa.Column('role', sa.String(), server_default='student'),
        sa.Column('otp_secret', sa.String(), nullable=True),
        sa.Column('master_qr_mode_enabled', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('master_qr_secret', sa.String(), nullable=True),
    )

    op.create_table(
        'attendance',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        'sections',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), unique=True, index=True),
    )

    op.create_table(
        'section_students',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('section_id', sa.Integer(), sa.ForeignKey('sections.id')),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id')),
    )

    op.create_table(
        'section_teachers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('section_id', sa.Integer(), sa.ForeignKey('sections.id')),
        sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('users.id')),
    )

    op.create_table(
        'section_attendance',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('section_id', sa.Integer(), sa.ForeignKey('sections.id')),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        'section_beacons',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('section_id', sa.Integer(), sa.ForeignKey('sections.id')),
        sa.Column('beacon_id', sa.String(), index=True),
    )


def downgrade() -> None:
    op.drop_table('section_beacons')
    op.drop_table('section_attendance')
    op.drop_table('section_teachers')
    op.drop_table('section_students')
    op.drop_table('sections')
    op.drop_table('attendance')
    op.drop_table('users')


