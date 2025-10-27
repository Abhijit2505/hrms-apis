
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import *
from .services import build_prompt, call_together_inference
from .models import *


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
    Generates a professional Job Description (JD) using the DeepQuery inference engine.
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
            500: openapi.Response(description="Server error / DeepQuery Engine error")
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
            usage_obj = TotalUsage.objects.first()
            if not usage_obj:
                usage_obj = TotalUsage.objects.create(request_count=1)
            else:
                usage_obj.request_count += 1
                usage_obj.save()

            return Response(resp_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            jd_request.status = "failed"
            jd_request.error = str(e)
            jd_request.save()
            return Response(
                {"detail": "Failed to generate JD", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TotalUsageView(APIView):
    """
    Retrieve total API usage statistics.
    Returns the total number of API requests processed by the system.
    """

    @swagger_auto_schema(
        operation_summary="Get total API usage",
        operation_description="""
        This endpoint retrieves the **total number of API requests** recorded by the system.  
        It returns a JSON object containing the total request count.
        """,
        responses={
            200: openapi.Response(
                description="Successful Response",
                schema=TotalUsageSerializer,
                examples={
                    "application/json": {
                        "id": 1,
                        "request_count": 472
                    }
                },
            ),
            404: "Usage record not found",
        },
        tags=["Usage Analytics"],
    )
    def get(self, request):
        """
        Handle GET request for total usage statistics.
        """
        usage = TotalUsage.objects.first()
        if not usage:
            return Response({"detail": "Usage record not found"}, status=404)
        serializer = TotalUsageSerializer(usage)
        return Response(serializer.data)
