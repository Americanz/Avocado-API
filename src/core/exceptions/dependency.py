# from typing import TYPE_CHECKING, Any

# import jwt
# from fastapi import Depends, Request
# from fastapi.security import OAuth2PasswordBearer

# from src.core.common.ctx import CTX_USER_ID
# from src.core.exceptions.exceptions import (
#     HTTPException,
# )


# from src.config.settings import settings
# from src.core.utils.validators import validate_url

# oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/token")

# class StatusType(str ):
#     enable = "1"
#     disable = "2"

# if TYPE_CHECKING:
#     from src.core.models.auth.users.model import User
#     from src.core.models.auth.roles.model import Role


# def check_token(token: str) -> tuple[bool, int, Any]:
#     try:
#         options = {"verify_signature": True, "verify_aud": False, "exp": True}
#         decode_data = jwt.decode(
#             token,
#             settings.SECRET_KEY,
#             algorithms=[settings.JWT_ALGORITHM],
#             options=options,
#         )
#         return True, 0, decode_data
#     except jwt.DecodeError:
#         return False, 4010, "Invalid Token"
#     except jwt.ExpiredSignatureError:
#         return False, 4010, "Login expired"
#     except Exception as e:
#         return False, 5000, f"{repr(e)}"


# class AuthControl:
#     @classmethod
#     async def is_authed(cls, token: str = Depends(oauth2_schema)) -> Any | None:
#         from src.core.models.auth.users.model import User
#         user_id = CTX_USER_ID.get()
#         if user_id == 0:
#             status, code, decode_data = check_token(token)
#             if not status:
#                 raise HTTPException(code=code, msg=decode_data)

#             if decode_data["data"]["tokenType"] != "accessToken":
#                 raise HTTPException(code="4010", msg="The token is not an access token")

#             user_id = decode_data["data"]["userId"]

#         user = await User.filter(id=user_id).first()
#         if not user:
#             raise HTTPException(
#                 code="4040",
#                 msg=f"Authentication failed, the user_id: {user_id} does not exists in the system.",
#             )
#         CTX_USER_ID.set(int(user_id))
#         return user


# class PermissionControl:
#     @classmethod
#     async def has_permission(
#         cls, request: Request, current_user: Any = Depends(AuthControl.is_authed)
#     ) -> None:
#         user_roles: list[Role] = await current_user.roles
#         user_roles_codes: list[str] = [r.role_code for r in user_roles]
#         if "R_SUPER" in user_roles_codes:  # Super Administrator
#             return

#         if not user_roles:
#             raise HTTPException(code="4040", msg="The user is not bound to a role")

#         method = request.method.lower()
#         path = request.url.path

#         apis = [await role.apis for role in user_roles]
#         permission_apis = list(
#             set((api.method.value, api.path, api.status) for api in sum(apis, []))
#         )
#         for api_method, api_path, api_status in permission_apis:
#             if api_method == method and validate_url(
#                 api_path, request.url.path
#             ):  # API permission check passed
#                 if api_status == StatusType.disable:
#                     raise HTTPException(
#                         code="4030",
#                         msg=f"The API has been disabled, method: {method} path: {path}",
#                     )
#                 return

#         raise HTTPException(
#             code="4030", msg=f"Permission denied, method: {method} path: {path}"
#         )


# DependAuth = Depends(AuthControl.is_authed)
# DependPermission = Depends(PermissionControl.has_permission)
