# jdgen/serializers.py
from rest_framework import serializers

class JDGenerateSerializer(serializers.Serializer):
    """
    Accepts dynamic JSON as `payload`. The "payload" field can be any JSON structure.
    """
    payload = serializers.JSONField()
    word_count = serializers.IntegerField(min_value=50, required=False, default=300)
    tone = serializers.CharField(max_length=64, required=False, default="Professional")
    title = serializers.CharField(max_length=256, required=False, allow_blank=True)
    language = serializers.CharField(max_length=64, required=False, default="English")
    # optional: add other constraints like location, experience_level, must_have_skills, nice_to_have

class JDResponseSerializer(serializers.Serializer):
    jd_text = serializers.CharField()
    word_count = serializers.IntegerField()
    generated_at = serializers.DateTimeField()
    source = serializers.CharField()
