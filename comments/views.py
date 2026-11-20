from django.shortcuts import render, redirect
from django.views import View
from .forms import CommentForm
from post.models import Post

class CommentCreateView(View):
    def post(self, request, post_id):
        form = CommentForm(request.POST)
        post = Post.objects.get(id=post_id)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.author = request.user.perfil
            instance.post = post
            instance.save()
            return redirect('post:post_detail', post_id=post.id)
        else:
            context = {'message': ['error', f'Erro ao adicionar comentário. Verifique os dados e tente novamente. {form.errors}']}
            return redirect('post:post_detail', post_id=post.id)
