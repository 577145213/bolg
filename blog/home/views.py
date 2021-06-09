from django.core.paginator import EmptyPage
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from home.models import ArticleCategory, Article
from django.http.response import HttpResponseNotFound
# Create your views here.


# 首页分类栏目# 首页分类栏目# 首页分类栏目# 首页分类栏目# 首页分类栏目# 首页分类栏目
class IndexView(View):
    def get(self,request):
        # 获取所有分类信息
        categories = ArticleCategory.objects.all()
        # 接收用户点击的分类id

        cat_id = request.GET.get('cat_id', 1)
        # 根据分类id进行分类查询
        try:
            category = ArticleCategory.objects.get(id=cat_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseNotFound('没有此分类')
        # 获取分页参数
        page_num=request.GET.get('page_num', 1)
        page_siza=request.GET.get('page_size', 10)
        # 根据分类信息 查询文章数据
        article=Article.objects.filter(category=category)
        # 创建分页器
        from django.core.paginator import Paginator
        paginator=Paginator(article,per_page=page_siza)
        # 进行分页处理
        try:
            page_articles=paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('empty page')
        # 总页数
        total_page = paginator.num_pages
        # 组织数据传递给模板

        context = {
            'categories': categories,
            'category': category,
            'articles':page_articles,
            'page_size':page_siza,
            'total_page':total_page,
            'page_num':page_num,
        }
        return render(request, 'index.html', context=context)


from home.models import Comment
# 第八点一节  文章详情
class DetailView(View):



    def get(self,request):
        # 接收文章id信息
        id=request.GET.get('id')
        # 根据文章id进行文章数据的查询
        try:
            article = Article.objects.get(id=id)
        except Article.DoesNotExist:
            return render(request,'404.html')
        else:
             # 让浏览量加1
            article.total_view+=1
            article.save()

        # 查询分类数据
        categories = ArticleCategory.objects.all()

        # 查询流量量前十文章
        hot_articles=Article.objects.order_by('-total_view')[:9]



        page_size=request.GET.get('page_size',10)
        page_num=request.GET.get('page_num',1)

        comments=Comment.objects.filter(article=article).order_by('-created')

        total_count=comments.count()
        from django.core.paginator import Paginator,EmptyPage
        paginator=Paginator(comments,page_size)

        try:
            page_comments=paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('empty page')

        total_page=paginator.num_pages


        # 组织模板数据
        context ={
            'categories': categories,
            'category': article.category,
            'article': article,
            'hot_articles':hot_articles,
            'total_count':total_count,
            'comments':page_comments,
            'page_size':page_size,
            'total_page':total_page,
            'page_num':page_num
        }
        return render(request, 'detail.html',context=context)

    def post(self,request):
        # 先接收用户信息
        user = request.user
        # 判断用户是否登陆
        if user and user.is_authenticated:
    # 登录用户可以接受form数据
             #    接收评论数据
            id=request.POST.get('id')
            content=request.POST.get('content')
            try:                  #   验证文章是否存在
                article=Article.objects.get(id=id)
            except Article.DoesNotExist:
                return HttpResponseNotFound('没有此文章')
             #    保存评论数据
            Comment.objects.create(
                content=content,
                article=article,
                user=user
            )
            article.comments_count+=1  # 修改评论的数量
            article.save()
            path=reverse('home:detail')+'?id={}'.format(article.id)
            return redirect(path)
        else:
            return render(reverse('users:login'))
