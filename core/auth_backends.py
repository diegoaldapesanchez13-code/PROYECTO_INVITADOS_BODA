from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from core.services.identity import normalizar_telefono


class UsernameEmailPhoneBackend(ModelBackend):
    """Authenticate by username, email or registered phone."""

    def authenticate(
        self,
        request,
        username=None,
        password=None,
        **kwargs,
    ):
        identifier = str(
            username
            or kwargs.get("email")
            or ""
        ).strip()

        if not identifier or password is None:
            return None

        User = get_user_model()
        candidates = []

        exact_username = User.objects.filter(
            username__iexact=identifier
        ).first()
        if exact_username:
            candidates.append(exact_username)

        email_matches = list(
            User.objects.filter(
                email__iexact=identifier
            )[:2]
        )
        if len(email_matches) == 1:
            candidates.append(email_matches[0])

        phone = normalizar_telefono(
            identifier
        )
        if phone:
            phone_user = User.objects.filter(
                perfil_acceso__telefono_normalizado=phone
            ).first()
            if phone_user:
                candidates.append(phone_user)

        seen = set()
        for user in candidates:
            if user.id in seen:
                continue
            seen.add(user.id)

            if (
                user.check_password(password)
                and self.user_can_authenticate(user)
            ):
                return user

        return None
