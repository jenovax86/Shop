from rest_framework import status
from rest_framework.response import Response


class DeleteResponseMixin:
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"meta": {"message": "Deleted successfully."}},
            status=status.HTTP_200_OK,
        )
