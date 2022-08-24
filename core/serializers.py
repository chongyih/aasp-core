from rest_framework import serializers

from core.models import CodeQuestion, Tag, TestCase, Language


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ['id', 'time_limit', 'memory_limit', 'score']


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['name']


class CodeQuestionsSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    testcase_set = TestCaseSerializer(read_only=True, many=True)
    languages = LanguageSerializer(read_only=True, many=True)

    class Meta:
        model = CodeQuestion
        fields = ['id', 'name', 'description', 'tags', 'question_bank', 'assessment', 'testcase_set', 'languages']
