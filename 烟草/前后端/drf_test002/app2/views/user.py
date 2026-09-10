from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
import uuid

from ..serializer  import *
from ..models import *

import datetime

import  requests
class RegisteryView(APIView):
    def post(self, request):
        username = request.data.get('username')
        phone = request.data.get('phone')
        password1 = request.data.get('password1')
        password2 = request.data.get('password2')
        if User.objects.filter(username=username):
            return Response({'msg': '该用户已注册！', 'code': 400})
        else:
            if User.objects.filter(phone=phone):
                return Response({'msg': '该手机号已用于注册！', 'code': 400})
            else:
                if password1 == password2:#校验两次输入的密码
                    user_data = {'username': username, 'phone': phone, 'password': password1}#取数据
                    user_serializer = UserRegisterSerializer(data=user_data)#序列化数据
                    if user_serializer.is_valid():#判断数据合法性
                        user_serializer.save()#保存数据
                        return Response({'msg': '注册成功！', 'code': 200})
                    else:
                        return Response({'msg': user_serializer.errors, 'code': 400})
                else:
                    return Response({'msg': '两次密码不一致！', 'code': 400})

class LoginView(APIView):
    def post(self, request):

        serializer = UserLoginSerializer(data=request.data)

        if  not serializer.is_valid():
            return Response({"msg": "校验失败", "code": 400, "detail": serializer.errors})

        instance = User.objects.filter(**serializer.validated_data).first()
        if not instance:
           return Response({"msg": "用户名或密码错误！", "code": 400})
        token = str(uuid.uuid4())
        instance.token = token
        instance.save()
        return Response({
            "msg": "登录成功", "code": 200,
            "token": token,
            "user_id": instance.id,
            "username": instance.username
        })

class UserManage(APIView):
    def get(self, request, pk=None):
        if pk:#查看特定用户
            user = User.objects.get(pk=pk)
            serializer = UserDetailSerializer(user)
            return Response(serializer.data)
        else:#查看整个用户列表
            users = User.objects.all().order_by('id')
            serializer = UserDetailSerializer(instance=users, many=True)

            context={'users': serializer.data,"code":200}
            return Response(context)
    #增加新用户基本数据
    def post(self, request):
        serializer = UserDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    #修改已有用户数据
    def put(self, request, pk):
        user = User.objects.get(pk=pk)
        serializer = UserDetailSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    #删除用户数据
    def delete(self, request, pk):
        user = User.objects.get(pk=pk)
        user.delete()
        return Response(user.username)