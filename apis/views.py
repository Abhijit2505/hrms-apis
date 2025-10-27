# jdgen/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone

from .serializers import JDGenerateSerializer
from .services import build_prompt, call_together_inference
from .models import JDRequest

class GenerateJDAPIView(APIView):
    """
    POST /api/jdgen/
    Body: { payload: <json>, word_count: 500, tone: "Professional", title: "Sr. Backend Engineer" }
    """
    permission_classes = [permissions.IsAuthenticated]  # change as per your auth policy

    def post(self, request):
        serializer = JDGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        print( "Validated data:", validated )

        payload = validated["payload"]
        word_count = validated.get("word_count", 300)
        tone = validated.get("tone", "Professional")
        title = validated.get("title", "")
        language = validated.get("language", "English")

        # persist request as pending
        jd_request = JDRequest.objects.create(
            input_json=payload,
            word_count=word_count,
            tone=tone,
            language=language,
            status="pending",
        )

        prompt = build_prompt(payload, word_count=word_count, tone=tone, title=title, language=language)

        try:
            # choose max_tokens conservatively: approximate tokens = words * 1.3
            max_tokens = min(4096, int(word_count * 1.5) + 100)
            generated_text = call_together_inference(prompt, max_tokens=max_tokens, temperature=0.2)
            jd_request.output_text = generated_text
            jd_request.status = "complete"
            jd_request.save()

            return Response({
                "jd_text": generated_text,
                "word_count": word_count,
                "generated_at": timezone.now(),
                "source": "deepqueryv1.5",
                "request_id": jd_request.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            jd_request.status = "failed"
            jd_request.error = str(e)
            jd_request.save()
            return Response({"detail": "Failed to generate JD", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
