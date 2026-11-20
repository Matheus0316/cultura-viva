from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.template.loader import render_to_string
from django.http import JsonResponse
from .forms import PostForm
from comments.forms import CommentForm
from grupos.models import Grupo
from .models import Post
from django.core.paginator import Paginator

class AcervoListView(View):
    def get(self, request):
        # Filtra apenas posts relacionados a memória e acervo
        posts = Post.objects.filter(category__in=['ACERVO', 'HISTORIA', 'RELATO']).order_by('-created_at')

        paginator = Paginator(posts, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'posts': page_obj,
        }
        return render(request, 'post/acervo_list.html', context)


class PostCreateView(View):
    def get(self, request, group_token):
        if not request.user.is_authenticated:
            return redirect('home:login')

        grupo = Grupo.objects.get(id=group_token)
        is_member = grupo.membros.filter(perfil__user=request.user).exists()

        if not (request.user.is_superuser or is_member):
             return redirect('grupos:grupo_detail', id=grupo.id)

        form = PostForm()
        context = {
            'grupo': grupo,
            'form': form,
        }
        return render(request, 'post/post_create.html', context)

    def post(self, request, group_token):
        if not request.user.is_authenticated:
            return redirect('home:login')

        grupo = Grupo.objects.get(id=group_token)
        is_member = grupo.membros.filter(perfil__user=request.user).exists()

        if not (request.user.is_superuser or is_member):
             return redirect('grupos:grupo_detail', id=grupo.id)

        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.author = request.user.perfil
            new_form.grupo = grupo
            new_form.save()

            # transaction.on_commit(lambda:send_email_notification.delay(new_form.id))
            return redirect('grupos:grupo_detail', id=grupo.id)

        context = {'message': ['error', f'Erro ao criar o post. Verifique os dados e tente novamente. {form.errors}']}
        return render(request, 'post/post_create.html', context)

class PostDetailView(View):
    def get(self, request, post_id):
        post = Post.objects.get(id=post_id)
        comment_form = CommentForm()
        context = {
            'post': post,
            'comment_form': comment_form,
        }
        return render(request, 'post/post_detail.html', context)

class PostEditView(View):
    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        form = PostForm(instance=post)
        html = render_to_string('post/partials/edit_post.html', {'form': form, 'post': post}, request=request)
        return JsonResponse({'html': html})

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        else:
            html = render_to_string('post/partials/edit_post.html', {'form': form, 'post': post}, request=request)
            return JsonResponse({'status': 'error', 'html': html})


class postDeleteView(View):
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        post.delete()
        return JsonResponse({'status': 'success'})
