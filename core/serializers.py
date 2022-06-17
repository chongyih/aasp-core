from rest_framework import serializers

from core.models import CodeQuestion, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class CodeQuestionsSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)

    class Meta:
        model = CodeQuestion
        fields = ['id', 'name', 'description', 'tags', 'question_bank', 'assessment']
