# # jdgen/views.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status, permissions
# from django.utils import timezone

# from .serializers import JDGenerateSerializer
# from .services import build_prompt, call_together_inference
# from .models import JDRequest

# class GenerateJDAPIView(APIView):
#     """
#     POST /api/jdgen/
#     Body: { payload: <json>, word_count: 500, tone: "Professional", title: "Sr. Backend Engineer" }
#     """
#     permission_classes = [permissions.IsAuthenticated]  # change as per your auth policy

#     def post(self, request):
#         serializer = JDGenerateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         validated = serializer.validated_data

#         print( "Validated data:", validated )

#         payload = validated["payload"]
#         word_count = validated.get("word_count", 300)
#         tone = validated.get("tone", "Professional")
#         title = validated.get("title", "")
#         language = validated.get("language", "English")

#         # persist request as pending
#         jd_request = JDRequest.objects.create(
#             input_json=payload,
#             word_count=word_count,
#             tone=tone,
#             language=language,
#             status="pending",
#         )

#         prompt = build_prompt(payload, word_count=word_count, tone=tone, title=title, language=language)

#         try:
#             # choose max_tokens conservatively: approximate tokens = words * 1.3
#             max_tokens = min(4096, int(word_count * 1.5) + 100)
#             generated_text = call_together_inference(prompt, max_tokens=max_tokens, temperature=0.2)
#             jd_request.output_text = generated_text
#             jd_request.status = "complete"
#             jd_request.save()

#             return Response({
#                 "jd_text": generated_text,
#                 "word_count": word_count,
#                 "generated_at": timezone.now(),
#                 "source": "deepqueryv1.5",
#                 "request_id": jd_request.id
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             jd_request.status = "failed"
#             jd_request.error = str(e)
#             jd_request.save()
#             return Response({"detail": "Failed to generate JD", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import JDGenerateSerializer, JDResponseSerializer
from .services import build_prompt, call_together_inference
from .models import JDRequest


# Optional: define an Authorization header parameter so Swagger UI shows an auth input box
auth_header = openapi.Parameter(
    name="Authorization",
    in_=openapi.IN_HEADER,
    description="JWT or DRF Token. Example: 'Bearer <access_token>' or 'Token <token>'",
    type=openapi.TYPE_STRING,
)

# Example request payload shown in Swagger UI
example_payload = {
    "payload": {
        "company": {
            "name": "Presear Softwares",
            "about": "AI-first software company building enterprise knowledge systems."
        },
        "role": "Senior Backend Engineer",
        "skills": ["Python", "Django", "Postgres", "REST", "Docker"],
        "experience": "5+ years",
        "location": "Bhubaneswar, India",
        "employment_type": "Full-time"
    },
    "word_count": 500,
    "tone": "Professional",
    "title": "Senior Backend Engineer",
    "language": "English"
}


class GenerateJDAPIView(APIView):
    """
    POST /api/jdgen/
    Generates a professional Job Description (JD) using the Together AI inference engine.
    """

    permission_classes = [permissions.IsAuthenticated]  # adjust as needed

    @swagger_auto_schema(
        operation_summary="Generate a Job Description",
        operation_description=(
            "Takes a dynamic JSON `payload` describing the role and related fields and returns "
            "a professionally formatted Job Description. The `word_count` parameter controls "
            "approximate output length. The AI will include sections such as Summary, "
            "Responsibilities, Required Qualifications, Preferred Qualifications, About the Company, "
            "and How to Apply (when relevant info exists in the payload)."
        ),
        manual_parameters=[auth_header],
        request_body=JDGenerateSerializer,
        responses={
            200: openapi.Response(
                description="Successfully generated JD",
                schema=JDResponseSerializer,
                examples={
                    "application/json": {
                        "jd_text": "Senior Backend Engineer\n\nSummary: ...",
                        "word_count": 500,
                        "generated_at": "2025-10-27T10:00:00Z",
                        "source": "deepqueryv1.5"
                    }
                }
            ),
            400: "Validation error (invalid request body)",
            401: "Authentication credentials were not provided or invalid",
            500: openapi.Response(description="Server error / AI provider error")
        },
        tags=["Job Description Generation"],
        operation_id="generateJobDescription",
    )
    def post(self, request):
        serializer = JDGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        # debug-friendly print (remove in production)
        print("Validated data:", validated)

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
            # approximate tokens = words * 1.5; cap for safety
            max_tokens = min(4096, int(word_count * 1.5) + 100)
            generated_text = call_together_inference(prompt, max_tokens=max_tokens, temperature=0.2)

            jd_request.output_text = generated_text
            jd_request.status = "complete"
            jd_request.save()

            response_payload = {
                "jd_text": generated_text,
                "word_count": word_count,
                "generated_at": timezone.now(),
                "source": "deepqueryv1.5",
                "request_id": jd_request.id
            }
            # Validate response shape (optional) before returning
            resp_serializer = JDResponseSerializer(data=response_payload)
            resp_serializer.is_valid(raise_exception=True)

            return Response(resp_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            jd_request.status = "failed"
            jd_request.error = str(e)
            jd_request.save()
            return Response(
                {"detail": "Failed to generate JD", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
