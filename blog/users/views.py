from django.shortcuts import render
from django.http.response import HttpResponseBadRequest
import re
from users.models import User
from django.db import DatabaseError
from django.shortcuts import redirect
from django.urls import reverse

# Create your views here.
# 注册视图
from django.views import View

# 注册信息 注册信息  注册信息  注册信息 注册信息 注册信息 注册跳转  注册跳转 注册跳转 注册跳转 注册跳转 注册跳转 注册跳转
class RegisterView(View):
    def get(self,request):
        return render(request, 'register.html')
    def post(self,request):
        """
        1.接收数据
        验证数据
          参数是否齐全
          手机号格式是否正确
          密码是否符合格式
          密码 确认密码是否一样
          短信验证是否和redis一致
        保存注册信息
        返回响应跳转到指定页面
        :param request:
        :return:
        """

        # 1接收数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')
        # 2验证数据
        #   参数是否齐全
        if not all ([mobile,password,password2,smscode]):
            return HttpResponseBadRequest('缺少必要的参数')
        #   手机号格式是否正确
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return HttpResponseBadRequest('手机号不符合规则')
        #   密码是否符合格式
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return HttpResponseBadRequest('请输入正确格式的秘码')
        #   密码 确认密码是否一样
        if password != password2:
            return HttpResponseBadRequest('两次密码不一致')
        #   短信验证是否和redis一致
        redis_conn=get_redis_connection('default')
        redis_sms_code=redis_conn.get('sms:%s'%mobile)
        if redis_sms_code is None:
            return HttpResponseBadRequest('短信验证码已经过期')
        if smscode != redis_sms_code.decode():
            return HttpResponseBadRequest('短信验证码错误')
        # 保存注册信息 create_user 可以使用系统的来对密码进行加密
        try:
         user=User.objects.create_user(username=mobile,
                                      mobile=mobile,
                                      password=password)
        except DatabaseError  as  e:
           logger.error(e)
           return HttpResponseBadRequest('注册失败')

        from django.contrib.auth import login
        login(request, user)
        # 返回响应跳转到指定页面
        # 暂时返回一个注册成功的信息， 后期继续实现跳转到指定页面

        # redirect 是进行重定向
        # reverse 是可以通过 namespace：name 来获取到视图所对应的路由
        responde = redirect(reverse('home:index'))
        # return HttpResponse('注册成功，重定向到首页')

        # 设置cookie信息，以方便首页中用户信息展示的判断和用户信息的展示
        responde.set_cookie('is_login',True)
        responde.set_cookie('username',user.username, max_age=7*24*3600)
        return responde



from django.http.response import HttpResponseBadRequest
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from  django.http import HttpResponse
from django.http.response import JsonResponse
from utils.response_code import RETCODE
import  logging
logger=logging.getLogger('django')
from random import randint
from libs.yuntongxun.sms import CCP


# 图片验证
class ImageCodeView(View):
    def get(self,request):
        """
        1.接收前端传递过来的uuid
        2.判断uuid是否获取到
        3.通过调用captcha 来生成图片验证码（图片二进制和图片内容）
        4.将图片内容保存到redis中 uuid作为一个key ，图片内容作为一个value同时我们还需要设置一个实效
        5.图片二进制返回给前端
        :param request:
        :return:
        """
# 图片验证 图片验证 图片验证 图片验证 图片验证 图片验证 图片验证 图片验证 图片验证 图片验证 图片验证
        uuid=request.GET.get('uuid')                             # 1.接收前端传递过来的uuid
        if uuid is None:
            return HttpResponseBadRequest('没有传递uuid')         # 2.判断uuid是否获取到id
        text, image = captcha.generate_captcha()                 # 3.通过调用captcha 来生成图片验证码（图片二进制和图片内容）
        redis_conn = get_redis_connection('default')
        # key 设置为uuid
        # seconds 过期秒数
        # value text 生成图片二进制的内容
        redis_conn.setex('img:%s'%uuid, 300, text)               #  4.将图片内容保存到redis中 uuid作为一个key图片内容作为一个value同时我们还需要设置一个实效

        return HttpResponse(image,content_type='image/jpeg')     #  5.图片二进制返回给前端

        pass     ##

# 短信验证
class SmsCodeView(View):
    def get(self, request):
       mobile = request.GET.get('mobile')
       image_code=request.GET.get('image_code')
       uuid=request.GET.get('uuid')

# 验证码验证 验证码验证 验证码验证 验证码验证 验证码验证 验证码验证 验证码验证 验证码验证 验证码验证 验证码验证
       if not all ([mobile,image_code,uuid]):
           return  JsonResponse({'code':RETCODE.NECESSARYPARAMERR,'errmsg':'缺少必要参数'})


       redis_conn=get_redis_connection('default')
       redis_image_code=redis_conn.get('img:%s'%uuid)


       if redis_image_code is None:
           return  JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图片验证码已过期'})



       try:
         redis_conn.delete('img:%d'%uuid)
       except Exception as  e:
           logger.error(e)


       if redis_image_code.decode().lower() !=image_code.lower():
           return  JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图片验证码'})


       sms_code='%06d'%randint(0,999999)
       logger.info(sms_code)


       redis_conn.setex('sms:%s'%mobile,300,sms_code)


       CCP().send_template_sms(mobile,[sms_code,5],1)


       return  JsonResponse({'code':RETCODE.OK,'errmsg':'短信发送成功'})

# 登录实现
class LoginView(View):
    def get(self, request):

        return render(request, 'login.html')

    """
           接收参数
           参数的验证
             验证手机号
             验证密码是否符合规则
           用户登录认证
           状态的保持
           根据用户选择的是否记住登录状态来进行判断
           为了首页显示 需要设置一些cookie 信息
           返回响应
           :param request:
           :return:
           """

    def post(self, request):
        # 接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        # 参数的验证
        #   验证手机号
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号不符合规则')

        #   验证密码是否符合规则
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return HttpResponseBadRequest('密码不符合规则')
        # 用户登录认证
        # 采用系统自带的认证方式 如果用户名和密码正确 会返回user 如果用户名和密码不正确 会返回None
        from django.contrib.auth import authenticate  # 默认的认证方法 是针对username字段进行 用户名的判断 当前判断信息是手机号 so我need修改认证字段
        # wo need 到 user模型中进行修改 等测试出现问题时 在修改

        user = authenticate(mobile=mobile, password=password)
        if user is None:
            return  HttpResponseBadRequest('用户名或密码错误')

        # 状态的保持
        from django.contrib.auth import login
        login(request, user)
        # 根据用户选择的是否记住登录状态来进行判断
        # 为了首页显示 需要设置一些cookie 信息

        # 根据next参数来进行页面的跳转
        next_page=request.GET.get('next')
        if next_page:
            response=redirect(next_page)
        else:
            response = redirect(reverse('home:index'))
        if remember != 'on':  # 没有记住用户信息
            request.session.set_expiry(0)    # 浏览器关闭之后 结束
            response.set_cookie('is_login',True)
            response.set_cookie('username',user.username,max_age=14*24*3600)

        else:                 # 记住用户信息
            request.session.set_expiry(None)  # NOne 默认记住两周
            response.set_cookie('is_login',True,max_age=14*24*3600)
            response.set_cookie('username',user.username,max_age=14*24*3600)


        # 返回响应
        return response

# 退出登录
from django.contrib.auth import logout
class LogoutView(View):
    def get(self, request):

        # session数据的清除
        logout(request)
        # cookie数据的部分删除
        response = redirect(reverse('home:index'))
        response.delete_cookie('is_login')
        # 跳转到首页
        return response

# 忘记密码
class ForgetPasswordView(View):

    def get(self,request):


        return render(request,'forget_password.html')

    def post(self,request):
        """
        接收数据
        验证数据
           判断参数是否齐全
           手机号师傅符合规则
           判断密码是否符合规则
           判断确认密码和密码是否一致
           判断短信验证吗是否正确
        根据手机号进行用户信息的查询
        如果手机号查询出用户信息则进行用户密码的修改
        如果手机号没有查询出用户信息   则进行新用户的创建
        进行页面的跳转 跳转到登录页面
        :param request:
        :return:
        """

        # 接收数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')
        # 验证数据
        #    判断参数是否齐全
        if not all([mobile, password ,password2 ,smscode]):
            return HttpResponseBadRequest('参数不齐')
        #    手机号师傅符合规则
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return HttpResponseBadRequest('手机号不符合规则')
        #    判断密码是否符合规则
        if not  re.match(r'^[0-9A-Za_z]{8,20}$',password):
            return HttpResponseBadRequest('密码不符合规则')
        #    判断确认密码和密码是否一致
        if password2 != password:
            return HttpResponseBadRequest('密码不一致')
        #    判断短信验证吗是否正确
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s'%mobile)
        if redis_sms_code is None:
            return HttpResponseBadRequest('短信验证码已过期')
        if redis_sms_code.decode() != smscode:
            return HttpResponseBadRequest('短信验证码错误')
        # 根据手机号进行用户信息的查询
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果手机号没有查询出用户信息   则进行新用户的创建
            try:
               User.objects.create_user(username=mobile,
                                     mobile=mobile,
                                     password=password)
            except Exception:
                return HttpResponseBadRequest('修改失败请稍后再试')
        else:
            # 如果手机号查询出用户信息则进行用户密码的修改
            user.set_password(password)
            # 注意 保存用户信息
            user.save()


        # 进行页面的跳转 跳转到登录页面
        response = redirect(reverse('users:login'))

        return response

# 个人中心 个人中心的展示 个人中心的修改    个人中心 个人中心的展示 个人中心的修改
from django.contrib.auth.mixins import LoginRequiredMixin
# 如果用户未登录的话 则会进行默认跳转 默认的跳转的链接是/accounts/login/?next=/xxx
class UserCenterView(LoginRequiredMixin,View):

    def get(self,request):
        # 获得登录用户的信息
        user=request.user
        # 组织获取用户的信息
        context = {
            'usersname':user.username,
            'mobile':user.mobile,
            'avatar':user.avatar.url if user.avatar else None,
            'user_desc':user.user_desc
        }
        return render(request,'center.html',context=context)

    def post(self,request):
        """
        接收参数
        将参数保存起来
        更新cookie中的usernam信息
        刷新当前页面（重定向）
        返回响应
        :param request:
        :return:
        """
        user=request.user
        # 接收参数
        username = request.POST.get('username', user.username)
        user_desc = request.POST.get('desc', user.user_desc)
        avatar = request.FILES.get('avatar')
        # 将参数保存起来
        try:
            user.username = username
            user.user_desc = user_desc
            if avatar:
                user.avatar=avatar
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('修改失败，请稍后再试')
        # 更新cookie中的usernam信息
        # 刷新当前页面（重定向）
        response = redirect(reverse('users:center'))
        response.set_cookie('username', user.username, max_age=14*3600*24)
        # 返回响应
        return response



# 写博客。。。。。。。
from home.models import ArticleCategory,Article
class WriteBlogView(LoginRequiredMixin,View):

    def get(self, request):
        # 查询所有分类模型
        categories = ArticleCategory.objects.all()
        context = {
            'categories': categories
        }

        return render(request, 'write_blog.html', context=context)


    def post(self,request):
        # 接受数据
        avatar = request.FILES.get('avatar')
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        tags = request.POST.get('tags')
        sumary = request.POST.get('sumary')
        content = request.POST.get('content')
        user = request.user

        # 验证数据
        if not all([avatar, title, category_id, sumary, content]):
            return HttpResponseBadRequest('参数不全')

        try:
            category = ArticleCategory.objects.get(id=category_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseBadRequest('没有次分类')
        # 数据入库
        try:
            article=Article.objects.create(
                author=user,
                avatar=avatar,
                category=category,
                tags=tags,
                title=title,
                sumary=sumary,
                content=content
            )
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('发布失败，请稍后再试')
        # 跳转到指定页面

        return redirect(reverse('home:index'))







