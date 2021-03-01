from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image")


class CommentForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'cols': 10,
                                                        'rows': 1}))

    class Meta:
        model = Comment
        fields = ("text",)
