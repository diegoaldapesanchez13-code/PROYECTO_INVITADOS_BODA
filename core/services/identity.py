"""Identity helpers for login and tenant account lifecycle."""

import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from core.models import PerfilAcceso


def normalizar_telefono(value):
    digits = re.sub(
        r"\D+",
        "",
        str(value or ""),
    )
    return digits or None


def perfil_acceso_de(user):
    profile, _ = PerfilAcceso.objects.get_or_create(
        usuario=user
    )
    return profile


def validar_identidad_unica(
    *,
    username,
    email="",
    phone="",
    exclude_user=None,
):
    User = get_user_model()

    username = str(username or "").strip()
    email = str(email or "").strip().lower()
    phone_norm = normalizar_telefono(phone)

    if not username:
        raise ValidationError(
            "El usuario es obligatorio."
        )

    user_qs = User.objects.all()
    if exclude_user:
        user_qs = user_qs.exclude(
            id=exclude_user.id
        )

    if user_qs.filter(
        username__iexact=username
    ).exists():
        raise ValidationError(
            "Ese nombre de usuario ya está en uso."
        )

    if (
        email
        and user_qs.filter(
            email__iexact=email
        ).exists()
    ):
        raise ValidationError(
            "Ese correo ya está asociado a otra cuenta."
        )

    profile_qs = PerfilAcceso.objects.all()
    if exclude_user:
        profile_qs = profile_qs.exclude(
            usuario=exclude_user
        )

    if (
        phone_norm
        and profile_qs.filter(
            telefono_normalizado=phone_norm
        ).exists()
    ):
        raise ValidationError(
            "Ese teléfono ya está asociado a otra cuenta."
        )

    return {
        "username": username,
        "email": email,
        "phone": str(phone or "").strip(),
        "phone_normalized": phone_norm,
    }


def actualizar_identidad_usuario(
    user,
    *,
    username=None,
    email=None,
    phone=None,
    first_name=None,
    last_name=None,
    password=None,
    active=None,
):
    data = validar_identidad_unica(
        username=(
            username
            if username is not None
            else user.username
        ),
        email=(
            email
            if email is not None
            else user.email
        ),
        phone=phone,
        exclude_user=user,
    )

    user.username = data["username"]
    user.email = data["email"]

    if first_name is not None:
        user.first_name = str(
            first_name or ""
        ).strip()

    if last_name is not None:
        user.last_name = str(
            last_name or ""
        ).strip()

    if password:
        user.set_password(password)

    if active is not None:
        user.is_active = bool(active)

    user.is_staff = False
    user.is_superuser = False
    user.save()

    profile = perfil_acceso_de(user)
    profile.telefono = data["phone"] or None
    profile.telefono_normalizado = (
        data["phone_normalized"]
    )
    profile.save(
        update_fields=[
            "telefono",
            "telefono_normalizado",
            "fecha_actualizacion",
        ]
    )

    return user


def crear_identidad_usuario(
    *,
    username,
    email="",
    phone="",
    first_name="",
    last_name="",
    password,
    active=True,
):
    data = validar_identidad_unica(
        username=username,
        email=email,
        phone=phone,
    )

    User = get_user_model()
    user = User.objects.create_user(
        username=data["username"],
        email=data["email"],
        password=password,
        first_name=str(first_name or "").strip(),
        last_name=str(last_name or "").strip(),
        is_active=bool(active),
    )

    profile = perfil_acceso_de(user)
    profile.telefono = data["phone"] or None
    profile.telefono_normalizado = (
        data["phone_normalized"]
    )
    profile.save(
        update_fields=[
            "telefono",
            "telefono_normalizado",
            "fecha_actualizacion",
        ]
    )
    return user
