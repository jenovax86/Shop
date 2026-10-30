from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import action
from rest_framework.response import Response

from auth.authentication import JwtAuthentication
from sessions.models import Session
from sessions.serializers import SessionSerializer, RevokeSessionSerializer


class SessionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = SessionSerializer
    authentication_classes = [JwtAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Session.objects.filter(user=self.request.user, revoked_at__isnull=True,  expires_at__gt=timezone.now()).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'revoke':
            return RevokeSessionSerializer
        return SessionSerializer

    @action(detail=False, methods=['post'])
    def revoke(self, request):
        serializer = RevokeSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        revoked_sessions = self.get_queryset().filter(pk__in=serializer.validated_data['session_ids'],
                                                      revoked_at__isnull=True).update(revoked_at=timezone.now())
        return Response({'revoked_sessions': revoked_sessions})

    @action(detail=False, methods=['post'])
    def logout(self, request):
        payload = request.auth

        if not payload['sid']:
            raise AuthenticationFailed("invalid session token.")

        self.get_queryset().filter(pk=payload['sid'], revoked_at__isnull=True).update(revoked_at=timezone.now())
        response = Response(status=status.HTTP_200_OK)
        response.delete_cookie('refresh')

        return response
