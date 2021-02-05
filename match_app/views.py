from __future__ import unicode_literals
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Tag
from .forms import PostAddForm, ContactForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
import textwrap
from django.core.mail import BadHeaderError, EmailMessage
from django.db.models import Q

def is_valid_q(q):
    return q != '' and q is not None

def index(request):
    posts = Post.objects.all().order_by('-created_at')
    title_or_user = request.GET.get('title_or_user')
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')
    tag = request.GET.get('tag')

    if is_valid_q(title_or_user):
        posts = posts.filter(Q(title__icontains=title_or_user)
                        | Q(user__username__icontains=title_or_user)
                        ).distinct()

    if is_valid_q(date_min):
        posts = posts.filter(created_at__gte=date_min)

    if is_valid_q(date_max):
        posts = posts.filter(created_at__lt=date_max)

    if is_valid_q(tag) and tag != 'タグを選択...':
        posts = posts.filter(tag__tag=tag)

    return render(request, 'match_app/index.html', {'posts': posts, 'title_or_user': title_or_user , 'date_min': date_min, 'date_max': date_max ,'tag': tag})

def detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'match_app/detail.html', {'post': post})

@login_required
def add(request):
    if request.method == "POST":
        form = PostAddForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('match_app:index')
    else:
            form = PostAddForm()
    return render(request, 'match_app/add.html', {'form': form})

@login_required
def edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        form = PostAddForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('match_app:detail', post_id=post.id)
    else:
        form = PostAddForm(instance=post)
    return render(request, 'match_app/edit.html', {'form': form, 'post':post })

@login_required
def delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return redirect('match_app:index')

def contact(request):
    form = ContactForm(request.POST or None)
    if form.is_valid():
        name = form.cleaned_data['name']
        message = form.cleaned_data['message']
        email = form.cleaned_data['email']
        subject = 'お問い合わせありがとうございます。'
        contact = textwrap.dedent('''
            ※このメールはシステムからの自動返信です。

            {name} 様
        
            お問い合わせありがとうございます。
            以下の内容でお問い合わせを受け付けました。
            内容を確認させていただき、ご返信させていただきますので、少々お待ちください。

            ----------------------------------

            ・お名前
            {name}

            ・メールアドレス
            {email}

            ・メッセージ
            {message}
            -----------------------------------
            
            作成者 shinya
        ''').format(
            name=name,
            email=email,
            message=message
        )
        to_list = [email]
        bcc_list = [settings.EMAIL_HOST_USER]
        try:
            message = EmailMessage(subject=subject, body=contact, to=to_list, bcc=bcc_list)
            message.send()
        except BadHeaderError:
            return HttpResponse('無効なヘッダが検出されました。')
        return redirect('match_app:done')

    return render(request, 'match_app/contact.html',{'form': form})


def done(request):
    return render(request, 'match_app/done.html')