from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from sqlalchemy.orm import Session

from core.jwt_tokens import (
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from core.security import verify_password
from models import RefreshToken, User
from utils.config import settings
from utils.logging import get_logger

logger = get_logger()


class AuthService:
    @staticmethod
    def _normalize_utc(dt: datetime | None) -> datetime | None:
        """将 datetime 统一规范为 UTC 以便进行安全比较。"""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    def login(
        self,
        *,
        db: Session,
        username: str,
        password: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
        device_id: str | None = None,
    ) -> dict[str, Any]:
        """
        登录校验：
        - 检查用户是否存在、是否锁定、是否启用
        - 验证密码，成功则签发 access/refresh 令牌
        - 持久化刷新令牌记录（含 jti/生命周期/客户端信息）
        - 成功后重置失败次数

        注意：失败计数与锁定策略的窗口计算在 6.1 中扩展，这里只做基础读写与锁定检查。
        """
        try:
            user: User | None = db.query(User).filter(User.username == username).first()
            if user is None:
                # 匿名报错，不泄露用户名是否存在
                return {"code": 40101, "message": "用户名或密码错误"}

            # 锁定检查与窗口清理：
            # - 30 分钟窗口：失败次数在窗口外自动重置
            # - 连续 5 次失败：设置锁定 1 小时
            now = datetime.now(UTC)

            lock_cmp = self._normalize_utc(user.lock_until) if isinstance(user.lock_until, datetime) else None
            if lock_cmp is not None:
                # 处于锁定状态：当失败次数达到阈值并且未到解锁时间
                if int(user.failed_login_attempts or 0) >= 5 and now < lock_cmp:
                    return {"code": 40301, "message": "账号已锁定，请稍后再试"}
                # 若窗口/锁定已过期，重置状态
                if now >= lock_cmp and int(user.failed_login_attempts or 0) > 0:
                    user.failed_login_attempts = 0
                    user.lock_until = None
                    try:
                        db.add(user)
                        db.commit()
                    except Exception:
                        db.rollback()
                        logger.exception("reset failed attempts window failed")

            if not user.is_active:
                return {"code": 40302, "message": "账号已禁用"}

            if not verify_password(password, user.password_hash):
                # 失败计数 + 窗口策略（30 分钟；达到 5 次锁 1 小时）
                try:
                    attempts = int(user.failed_login_attempts or 0)
                    # 重新计算窗口是否有效
                    lock_cmp = self._normalize_utc(user.lock_until) if isinstance(user.lock_until, datetime) else None
                    window_active = lock_cmp is not None and now < lock_cmp and attempts > 0
                    # 若未在窗口内（空/已过/未计数），开启新窗口
                    if not window_active:
                        user.failed_login_attempts = 1
                        user.lock_until = now + timedelta(minutes=30)

                    else:
                        # 相当于：user.lock_until is not None and now < user.lock_until and attempts > 0
                        # 窗口内累加
                        attempts += 1
                        user.failed_login_attempts = attempts
                        if attempts >= 5:
                            # 达到阈值：锁定 1 小时
                            user.lock_until = now + timedelta(hours=1)
                        else:
                            # 仍在窗口内：窗口结束时间保持不变
                            pass

                    db.add(user)
                    db.commit()
                except Exception:
                    db.rollback()
                    logger.exception("update failed attempts with window failed")

                # 达到阈值并处于锁定期，直接返回 403
                lock_cmp = self._normalize_utc(user.lock_until) if isinstance(user.lock_until, datetime) else None
                if int(user.failed_login_attempts or 0) >= 5 and lock_cmp is not None and now < lock_cmp:
                    return {"code": 40301, "message": "账号已锁定，请稍后再试"}
                return {"code": 40101, "message": "用户名或密码错误"}

            # 密码通过：签发令牌，access/refresh 均携带角色
            access_token = create_access_token(user.id, user.role)
            refresh_token = create_refresh_token(user.id, user.role)

            # 解析刷新令牌以获取 jti/iat/exp（保证与 JWT 完全一致）
            claims = verify_token(refresh_token, "refresh")
            issued_at = datetime.fromtimestamp(int(claims["iat"]), UTC)
            expires_at = datetime.fromtimestamp(int(claims["exp"]), UTC)

            # 持久化刷新令牌记录
            rt = RefreshToken(
                jti=str(claims["jti"]),
                parent_jti=None,
                user_id=user.id,
                issued_at=issued_at,
                expires_at=expires_at,
                revoked=False,
                revoked_reason=None,
                device_id=device_id,
                ip=client_ip,
                user_agent=user_agent,
            )
            db.add(rt)
            # 成功登录重置失败次数
            user.failed_login_attempts = 0
            db.add(user)
            db.commit()

            # 返回 access_token；refresh_token 由控制器写入 Cookie
            return {
                "code": 0,
                "message": "ok",
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "refresh_expires_at": int(expires_at.timestamp()),
                },
            }
        except Exception:
            db.rollback()
            logger.exception("Login failed")
            return {"code": 50010, "message": "登录失败"}

    # 刷新令牌：轮换与复用检测
    def _find_root_token(self, db: Session, token: RefreshToken) -> RefreshToken:
        current = token
        # 追溯父链直至根（parent_jti 为 None）
        while current.parent_jti:
            parent = db.query(RefreshToken).filter(RefreshToken.jti == current.parent_jti).first()
            if parent is None:
                break
            current = parent
        return current

    def _collect_family_jtis(self, db: Session, root_jti: str) -> set[str]:
        # 通过逐层查询 parent_jti 构建家族成员集合（适用于小规模数据与测试场景）
        family: set[str] = {root_jti}
        frontier: set[str] = {root_jti}
        while frontier:
            children = db.query(RefreshToken).filter(RefreshToken.parent_jti.in_(list(frontier))).all()
            next_frontier: set[str] = set()
            for child in children:
                if child.jti not in family:
                    family.add(child.jti)
                    next_frontier.add(child.jti)
            frontier = next_frontier
        return family

    def _revoke_family(self, db: Session, any_member: RefreshToken, reason: str) -> None:
        root = self._find_root_token(db, any_member)
        family_jtis = self._collect_family_jtis(db, root.jti)
        tokens = db.query(RefreshToken).filter(RefreshToken.jti.in_(list(family_jtis))).all()
        now = datetime.now(UTC)
        for t in tokens:
            if not t.revoked:
                t.mark_revoked(reason)
            # 被复用的旧令牌若还未标记使用时间，这里顺带补记，便于审计
            if t.jti == any_member.jti and t.used_at is None:
                t.mark_used(now)
        db.add_all(tokens)

    def refresh(
        self,
        *,
        db: Session,
        refresh_token: str | None,
        client_ip: str | None = None,
        user_agent: str | None = None,
        device_id: str | None = None,
    ) -> dict[str, Any]:
        """
        刷新接口核心逻辑：
        - 校验 refresh_token（JWT 类型/过期/签名）
        - 复用检测：若旧 token 已 used_at，则撤销整个家族并返回 401
        - 轮换：标记旧 token.used_at，签发新 access 与新 refresh，并插入新记录（parent_jti=旧 jti）
        """
        if not refresh_token:
            return {"code": 40110, "message": "缺少刷新令牌"}

        try:
            claims = verify_token(refresh_token, "refresh")
        except TokenExpiredError:
            return {"code": 40111, "message": "刷新令牌已过期"}
        except TokenInvalidError:
            return {"code": 40110, "message": "刷新令牌无效"}
        except Exception:
            logger.exception("verify refresh token failed")
            return {"code": 40110, "message": "刷新令牌无效"}

        # 查找 DB 记录
        jti = str(claims["jti"])
        rt: RefreshToken | None = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        if rt is None:
            return {"code": 40110, "message": "刷新令牌不存在"}

        # 基本状态校验
        now = datetime.now(UTC)
        if rt.revoked:
            return {"code": 40112, "message": "刷新令牌已撤销"}
        if rt.is_expired(now):
            return {"code": 40111, "message": "刷新令牌已过期"}

        # 复用检测：同一刷新令牌再次使用
        if rt.used_at is not None:
            try:
                self._revoke_family(db, rt, "refresh token reuse detected")
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("revoke family on reuse failed")
            return {"code": 40112, "message": "检测到刷新令牌复用，会话已撤销"}

        # 正常轮换流程
        try:
            # 标记旧 token 已使用
            rt.mark_used(now)

            # 签发新令牌
            user_id = claims["sub"]
            # 始终信任 refresh token 中的角色（已验签与基础校验）
            role_value = claims.get("role")
            access_token = create_access_token(user_id, role_value)
            new_refresh = create_refresh_token(user_id, role_value)

            new_claims = verify_token(new_refresh, "refresh")
            issued_at = datetime.fromtimestamp(int(new_claims["iat"]), UTC)
            expires_at = datetime.fromtimestamp(int(new_claims["exp"]), UTC)

            new_rt = RefreshToken(
                jti=str(new_claims["jti"]),
                parent_jti=rt.jti,
                user_id=rt.user_id,
                issued_at=issued_at,
                expires_at=expires_at,
                revoked=False,
                revoked_reason=None,
                device_id=device_id,
                ip=client_ip,
                user_agent=user_agent,
            )

            db.add(rt)
            db.add(new_rt)
            db.commit()

            return {
                "code": 0,
                "message": "ok",
                "data": {
                    "access_token": access_token,
                    "refresh_token": new_refresh,
                    "refresh_expires_at": int(expires_at.timestamp()),
                },
            }
        except Exception:
            db.rollback()
            logger.exception("Refresh failed")
            return {"code": 50011, "message": "刷新失败"}

    def logout(
        self,
        *,
        db: Session,
        refresh_token: str | None,
    ) -> dict[str, Any]:
        """
        登出：撤销当前 refresh 家族（或当前链）。

        - 若缺少/无效令牌：视为幂等操作，仍返回成功（仅清 Cookie）。
        - 若令牌有效或仅过期：定位家族并撤销。
        """
        if not refresh_token:
            return {"code": 0, "message": "ok"}

        claims: dict[str, Any] | None = None
        try:
            # 优先严格校验；若仅过期则尝试解析以获取 jti
            claims = verify_token(refresh_token, "refresh")
        except TokenExpiredError:
            try:
                # 仅忽略过期进行解析，仍校验签名与必要字段
                claims = jwt.decode(
                    refresh_token,
                    settings.JWT_SECRET,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={
                        "require": ["exp", "iat", "sub", "jti", "type"],
                        "verify_exp": False,
                        "verify_iat": False,
                    },
                )
                # 类型保护
                if claims.get("type") != "refresh":
                    claims = None
            except Exception:
                claims = None
        except TokenInvalidError:
            claims = None
        except Exception:
            logger.exception("verify token in logout failed")
            claims = None

        if not claims:
            # 无法定位令牌记录，视为成功（幂等）
            return {"code": 0, "message": "ok"}

        jti = str(claims.get("jti"))
        if not jti:
            return {"code": 0, "message": "ok"}

        try:
            rt: RefreshToken | None = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
            if rt is None:
                return {"code": 0, "message": "ok"}

            self._revoke_family(db, rt, "logout")
            db.commit()
            return {"code": 0, "message": "ok"}
        except Exception:
            db.rollback()
            logger.exception("Logout revoke failed")
            # 出错也不暴露细节，返回通用失败码
            return {"code": 50012, "message": "登出失败"}
