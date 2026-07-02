from datetime import timedelta

from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Game, GameKey, Order


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Username and password required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(
        username=username,
        password=password
    )

    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {'token': token.key},
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    game = get_object_or_404(Game, id=request.data.get("game_id"))

    with transaction.atomic():

        key = (
            GameKey.objects
            .select_for_update()
            .filter(
                game=game,
                owner__isnull=True,
                status="active"
            )
            .first()
        )

        if key is None:
            return Response(
                {"error": "No keys available"},
                status=status.HTTP_400_BAD_REQUEST
            )

        key.owner = request.user
        key.expires_at = timezone.now() + timedelta(days=30)
        key.save()

        order = Order.objects.create(
            user=request.user,
            game=game,
            key=key
        )

    return Response(
        {
            "order_id": order.id,
            "key": key.key_string,
            "expires_at": key.expires_at,
        },
        status=status.HTTP_201_CREATED
    )