"""Модуль содержит описание моделей для баз данных."""

from enum import Enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, MetaData, Table,
    ForeignKey, UniqueConstraint, Index, SmallInteger,
    Enum as sql_enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.config import DB_SETTINGS
from db import Base


class UUIDMixin:
    """Миксин для определения уникального автогенерируемого ключа."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)


class CreatedAtMixin:
    """Миксин для определения даты создания."""

    created_at = Column(DateTime, default=datetime.utcnow)


class UpdatedAtMixin:
    """Миксин для определения даты обновления."""

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


"""Таблица связи для пользователей и их ролей"""
user_role = Table(
    'user_role',
    Base.metadata,
    MetaData(schema=DB_SETTINGS.pg_schema),
    Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('user_id', UUID(as_uuid=True), ForeignKey(f'{DB_SETTINGS.pg_schema}.user.id', ondelete='CASCADE')),
    Column('role_id', UUID(as_uuid=True), ForeignKey(f'{DB_SETTINGS.pg_schema}.role.id', ondelete='CASCADE')),
    UniqueConstraint('user_id', 'role_id', name='uc_user_role_unique'),
)


class User(Base, UUIDMixin, CreatedAtMixin, UpdatedAtMixin):
    """Модель данных описывает таблицу user"""

    __tablename__ = 'user'
    __table_args__ = {
        'schema': DB_SETTINGS.pg_schema,
    }

    login = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    first_name = Column(String(200))
    surname = Column(String(200))
    patronymic = Column(String(200))
    phone = Column(String(100))

    roles = relationship('Role', secondary=user_role, back_populates='users', collection_class=set, lazy='subquery')
    history = relationship('UserAuthHistory')

    def __repr__(self):
        return f'<User {self.email}>'


class Role(Base, UUIDMixin, CreatedAtMixin, UpdatedAtMixin):
    """Модель данных для таблицы role"""

    __tablename__ = 'role'
    __table_args__ = {
        'schema': DB_SETTINGS.pg_schema,
    }

    name = Column(String(200), unique=True, nullable=False)
    description = Column(String(500))

    users = relationship('User', secondary=user_role, back_populates='roles', collection_class=set, lazy='subquery')

    def __repr__(self):
        return f'<Role {self.name}>'


class UserAuthHistoryMixin(Base, CreatedAtMixin):
    """Модель данных описывает абстрактную таблицу user_auth_history"""

    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f'{DB_SETTINGS.pg_schema}.user.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user_agent = Column(String(1000), nullable=False)
    device_type = Column(String(50), nullable=False, primary_key=True)


class UserAuthHistory(UserAuthHistoryMixin):
    """
        Модель данных описывает партицированную таблицу user_auth_history.
        Партицирование по столбцу device_type.
    """

    __tablename__ = 'user_auth_history'
    __table_args__ = {
            'schema': DB_SETTINGS.pg_schema,
            'postgresql_partition_by': 'LIST (device_type)',
    }


class UserAuthHistoryPC(UserAuthHistoryMixin):
    """
        Модель данных описывает партицию таблицы user_auth_history.
        Партицирование по столбцу device_type.
    """

    __tablename__ = 'user_auth_history_pc'
    partition_field = 'pc'


class UserAuthHistoryMobile(UserAuthHistoryMixin):
    """
        Модель данных описывает партицию таблицы user_auth_history.
        Партицирование по столбцу device_type.
    """

    __tablename__ = 'user_auth_history_mobile'
    partition_field = 'mobile'


class UserAuthHistoryOther(UserAuthHistoryMixin):
    """
        Модель данных описывает партицию таблицы user_auth_history.
        Партицирование по столбцу device_type.
    """

    __tablename__ = 'user_auth_history_other'
    partition_field = 'other'

Index('idx_user_is_created_at', UserAuthHistory.user_id, UserAuthHistory.created_at, UserAuthHistory.id)


class Scope(Base, UUIDMixin, CreatedAtMixin):
    """Модель данных для таблицы movies_scope"""

    __tablename__ = 'scope'
    __table_args__ = {
        'schema': DB_SETTINGS.pg_schema,
    }

    name = Column(String(50), unique=True, nullable=False)


class Permissions(Base, UUIDMixin, UpdatedAtMixin, CreatedAtMixin):
    """Модель данных для таблицы permissions"""

    __tablename__ = 'permissions'
    __table_args__ = (
        UniqueConstraint('scope_id', 'role_id', name='uc_scope_role_unique'),
        {'schema': DB_SETTINGS.pg_schema}
    )

    scope_id = Column(UUID(as_uuid=True),
                      ForeignKey(f'{DB_SETTINGS.pg_schema}.scope.id', ondelete='CASCADE'),
                      nullable=False)
    role_id = Column(UUID(as_uuid=True),
                     ForeignKey(f'{DB_SETTINGS.pg_schema}.role.id', ondelete='CASCADE'),
                     nullable=False)
    access_level = Column(SmallInteger(), nullable=False)


class SocialLogin(Enum):
    """Класс описывает возможные тэги для таблицы `oauth_user`"""
    vk = 'Vkontakte'
    yandex = 'Yandex'


"""Модель данных описывает таблицу oauth_user"""
OAuthUser = Table(
    'oauth_user',
    Base.metadata,
    MetaData(schema=DB_SETTINGS.pg_schema),
    Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False),
    Column('client_id', String(256), nullable=False),
    Column('email', String(100), unique=True, nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('tag', sql_enum(SocialLogin)),
    Column('user_id', UUID(as_uuid=True), ForeignKey(f'{DB_SETTINGS.pg_schema}.user.id', ondelete='CASCADE'))
)
