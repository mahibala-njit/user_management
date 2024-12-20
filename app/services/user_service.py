from builtins import Exception, bool, classmethod, int, str
from datetime import datetime, timezone
import secrets
from typing import Optional, Dict, List
from pydantic import ValidationError
from sqlalchemy import func, null, update, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_email_service, get_settings
from app.models.user_model import User
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.utils.nickname_gen import generate_nickname
from app.utils.security import generate_verification_token, hash_password, verify_password, validate_password
from uuid import UUID
from app.services.email_service import EmailService
from app.models.user_model import UserRole
import logging
from sqlalchemy import or_, and_
from sqlalchemy import select
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from app.models.user_model import User, UserRole

settings = get_settings()
logger = logging.getLogger(__name__)

class UserService:
    @classmethod
    async def _execute_query(cls, session: AsyncSession, query):
        try:
            result = await session.execute(query)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            return None

    @classmethod
    async def _fetch_user(cls, session: AsyncSession, **filters) -> Optional[User]:
        query = select(User).filter_by(**filters)
        result = await cls._execute_query(session, query)
        return result.scalars().first() if result else None

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: UUID) -> Optional[User]:
        return await cls._fetch_user(session, id=user_id)

    @classmethod
    async def get_by_nickname(cls, session: AsyncSession, nickname: str) -> Optional[User]:
        return await cls._fetch_user(session, nickname=nickname)

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> Optional[User]:
        return await cls._fetch_user(session, email=email)

    @classmethod
    async def create(cls, session: AsyncSession, user_data: Dict[str, str], email_service: EmailService) -> Optional[User]:
        try:
            validated_data = UserCreate(**user_data).model_dump()

            # Check for existing email
            existing_user = await cls.get_by_email(session, validated_data['email'])
            if existing_user:
                logger.error("User with given email already exists.")
                return None

            # Validate and hash password
            password = validated_data.pop('password')
            try:
                validate_password(password)  # Ensures password meets security criteria
            except ValueError as e:
                logger.error(f"Password validation failed: {e}")
                return None
            validated_data['hashed_password'] = hash_password(password)

            # Prepare new user
            new_user = User(**validated_data)

            if validated_data.get("nickname"):
                # Use the provided nickname if unique
                if not await cls.get_by_nickname(session, validated_data["nickname"]):
                    new_user.nickname = validated_data["nickname"]
                else:
                    raise ValueError(f"Nickname '{validated_data['nickname']}' is already taken.")
            else:
                # Generate a unique nickname
                new_nickname = generate_nickname()
                while await cls.get_by_nickname(session, new_nickname):
                    new_nickname = generate_nickname()
                new_user.nickname = new_nickname

            logger.info(f"User Role: {new_user.role}")
            user_count = await cls.count(session)
            new_user.role = UserRole.ADMIN if user_count == 0 else UserRole.ANONYMOUS

            if new_user.role == UserRole.ADMIN:
                new_user.email_verified = True
            else:
                new_user.verification_token = generate_verification_token()
                await email_service.send_verification_email(new_user)

            session.add(new_user)
            await session.commit()
            return new_user
        except ValidationError as e:
            logger.error(f"Validation error during user creation: {e}")
            return None


    @classmethod
    async def update(cls, session: AsyncSession, user_id: UUID, update_data: Dict[str, str]) -> Optional[User]:
        try:
            # Validate the update data using UserUpdate schema
            validated_data = UserUpdate(**update_data).model_dump(exclude_unset=True)
    
            # Handle password hashing if the password is being updated
            if 'password' in validated_data:
                validated_data['hashed_password'] = hash_password(validated_data.pop('password'))
    
            # Check for duplicate nickname
            if 'nickname' in validated_data:
                existing_user = await cls.get_by_nickname(session, validated_data['nickname'])
                if existing_user and existing_user.id != user_id:
                    logger.error(f"Nickname '{validated_data['nickname']}' is already taken.")
                    raise ValueError(f"Nickname '{validated_data['nickname']}' is already taken.")
    
            # Perform the update
            query = (
                update(User)
                .where(User.id == user_id)
                .values(**validated_data)
                .execution_options(synchronize_session="fetch")
            )
            await cls._execute_query(session, query)
    
            # Retrieve and refresh the updated user object
            updated_user = await cls.get_by_id(session, user_id)
            if updated_user:
                session.refresh(updated_user)
                logger.info(f"User {user_id} updated successfully.")
                return updated_user
            else:
                logger.error(f"User {user_id} not found after update attempt.")
                return None
    
        except ValidationError as e:
            logger.error(f"Validation error during user update: {e}")
            return None
        except ValueError as ve:
            logger.error(f"Value error during user update: {ve}")
            return None
        except Exception as e:  # Broad exception handling for debugging
            logger.error(f"Error during user update: {e}")
            return None


    @classmethod
    async def delete(cls, session: AsyncSession, user_id: UUID) -> bool:
        user = await cls.get_by_id(session, user_id)
        if not user:
            logger.info(f"User with ID {user_id} not found.")
            return False
        await session.delete(user)
        await session.commit()
        return True

    @classmethod
    async def list_users(cls, session: AsyncSession, skip: int = 0, limit: int = 10) -> List[User]:
        query = select(User).offset(skip).limit(limit)
        result = await cls._execute_query(session, query)
        logger.debug(f"List of Users {result}")
        return result.scalars().all() if result else []

    @classmethod
    async def register_user(cls, session: AsyncSession, user_data: Dict[str, str], get_email_service) -> Optional[User]:
        return await cls.create(session, user_data, get_email_service)
    

    @classmethod
    async def login_user(cls, session: AsyncSession, nickname: str, password: str) -> Optional[User]:
        user = await cls.get_by_nickname(session, nickname=nickname)
        if user:
            logger.info(f"User with ID found")
            if user.email_verified is False:
                return None
            if user.is_locked:
                return None
            if verify_password(password, user.hashed_password):
                user.failed_login_attempts = 0
                user.last_login_at = datetime.now(timezone.utc)
                session.add(user)
                await session.commit()
                return user
            else:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= settings.max_login_attempts:
                    user.is_locked = True
                session.add(user)
                await session.commit()
        return None

    @classmethod
    async def is_account_locked(cls, session: AsyncSession, email: str) -> bool:
        user = await cls.get_by_email(session, email)
        return user.is_locked if user else False


    @classmethod
    async def reset_password(cls, session: AsyncSession, user_id: UUID, new_password: str) -> bool:
        hashed_password = hash_password(new_password)
        user = await cls.get_by_id(session, user_id)
        if user:
            user.hashed_password = hashed_password
            user.failed_login_attempts = 0  # Resetting failed login attempts
            user.is_locked = False  # Unlocking the user account, if locked
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def verify_email_with_token(cls, session: AsyncSession, user_id: UUID, token: str) -> bool:
        user = await cls.get_by_id(session, user_id)
        if user and user.verification_token == token:
            user.email_verified = True
            user.verification_token = None  # Clear the token once used
            user.role = UserRole.AUTHENTICATED
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        """
        Count the number of users in the database.

        :param session: The AsyncSession instance for database access.
        :return: The count of users.
        """
        query = select(func.count()).select_from(User)
        result = await session.execute(query)
        count = result.scalar()
        return count
    
    @classmethod
    async def unlock_user_account(cls, session: AsyncSession, user_id: UUID) -> bool:
        user = await cls.get_by_id(session, user_id)
        if user and user.is_locked:
            user.is_locked = False
            user.failed_login_attempts = 0  # Optionally reset failed login attempts
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def search_and_filter_users(
        cls,
        session: AsyncSession,
        username: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_locked: Optional[bool] = None,
        skip: int = 0,
        limit: int = 10,
    ):
        """
        Perform basic user search and filtering.

        Parameters:
            - session: Database session.
            - username: Filter by username.
            - email: Filter by email.
            - role: Filter by user role.
            - is_locked: Filter by account lock status.
            - skip: Pagination offset.
            - limit: Pagination limit.

        Returns:
            Tuple of total count and list of users matching criteria.
        """
        query = select(User)
        if username:
            query = query.where(User.nickname.ilike(f"%{username}%"))
        if email:
            query = query.where(User.email.ilike(f"%{email}%"))
        if role:
            query = query.where(User.role == role)
        if is_locked is not None:
            query = query.where(User.is_locked == is_locked)

        total_users = await session.execute(select(func.count()).select_from(query.subquery()))
        result = await session.execute(query.offset(skip).limit(limit))

        return total_users.scalar(), result.scalars().all()

    @classmethod
    async def advanced_search_users(cls, session: AsyncSession, filters: Dict):
        """
        Perform advanced search based on multiple criteria.

        Parameters:
            - session: Database session.
            - filters: Dictionary containing filter criteria.

        Returns:
            Tuple of total count and list of users matching criteria.
        """
        query = select(User)

        # Apply filters dynamically
        for field, value in filters.items():
            if field == "username":
                query = query.where(User.nickname.ilike(f"%{value}%"))
            elif field == "email":
                query = query.where(User.email.ilike(f"%{value}%"))
            elif field == "role":
                query = query.where(User.role == value)
            elif field == "is_locked":
                query = query.where(User.is_locked == value)
            elif field == "created_from":
                query = query.where(User.created_at >= value)
            elif field == "created_to":
                query = query.where(User.created_at <= value)

        total_users = await session.execute(select(func.count()).select_from(query.subquery()))
        result = await session.execute(query.offset(filters.get("skip", 0)).limit(filters.get("limit", 10)))

        return total_users.scalar(), result.scalars().all()
