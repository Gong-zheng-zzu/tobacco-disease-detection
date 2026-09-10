from django.urls import path
from .views.user import RegisteryView, LoginView, UserManage
from .views.land_parcel import CreateLandParcelView, ListLandParcelsView, DeleteLandParcelView
from .views.fertilizer import FerView
from .views.pesticide import PesticideView, PesticideFromDiseaseView
from .views.nutrient_df import ImageRecognitionView, NutrientRecognitionWithFieldView
from .views.region_fertilizer import FerRegionView
from .views.AIconsult import ChatAPIView
from .views.device import DeviceView, DeviceDetailView
from .views.nutrient_deficiency import ParcelDeficiencyView, UserAllDeficienciesView
from .views.strategy import FieldStrategyContextView
urlpatterns = [
    # ==========用户=========================================================================
    # 用户注册
    path('register/', RegisteryView.as_view(), name='register'),
    # 用户登录
    path('login/', LoginView.as_view(), name='login'),
    # 用户管理
    path('users/', UserManage.as_view(), name='user_list'),  # 获取所有用户或创建用户
    path('users/<int:pk>/', UserManage.as_view(), name='user_detail'),  # 获取、更新或删除特定用户

    #==========地块===========================================================================
    #新建地块
    path('user/<int:user_id>/fields/create/',
         CreateLandParcelView.as_view(),
         name='create_land_parcel'),
    #查看所有地块
    path('user/<int:user_id>/fields/list/',
         ListLandParcelsView.as_view(),
         name='list_land_parcels'),
    #删除地块
    path('user/<int:user_id>/fields/<int:parcel_id>/',
         DeleteLandParcelView.as_view(),
         name='delete_land_parcel'),




    #==========基本施肥记录============================================================================
    #查看某用户的一块地的所有施肥记录
    path('user/<int:user_id>/fer_records/<int:fieldnum>/',
         FerView.as_view(),
         name='fer_records'),
    #新增记录
    path('user/<int:user_id>/fer_records/create/<int:fieldnum>/',
         FerView.as_view(),
         name='create_fer_record'),
    #删除记录
    path('user/<int:user_id>/fer_records/delete/<int:fieldnum>/<int:fernum>/',
         FerView.as_view(),
         name='delete_fer_record'),

    #==========农药记录============================================================================
    path('user/<int:user_id>/pesticide_records/<int:fieldnum>/',
         PesticideView.as_view(),
         name='pesticide_records'),
    path('user/<int:user_id>/pesticide_records/create/<int:fieldnum>/',
         PesticideView.as_view(),
         name='create_pesticide_record'),
    path('user/<int:user_id>/pesticide_records/delete/<int:fieldnum>/<int:recordnum>/',
         PesticideView.as_view(),
         name='delete_pesticide_record'),
    # 根据病虫害检测结果自动添加农药记录（首页调用）
    path('user/<int:user_id>/field/<int:fieldnum>/pesticide_from_diseases/',
         PesticideFromDiseaseView.as_view(),
         name='pesticide_from_diseases'),

    #==========设备管理============================================================================
    path('user/<int:user_id>/devices/', DeviceView.as_view(), name='device_list_create'),
    path('user/<int:user_id>/devices/<int:device_id>/', DeviceDetailView.as_view(), name='device_detail'),

    #==========区域追加施肥记录============================================================================
    # 按 id 删除单条追肥记录
    path('user/<int:user_id>/field/<int:fieldnum>/fer_regions/<int:region_id>/',
         FerRegionView.as_view(),
         name='fer-region-delete-by-id'),
    # POST 创建 / GET 查询 / DELETE(按日期) 追肥记录
    path('user/<int:user_id>/field/<int:fieldnum>/fer_regions/',
         FerRegionView.as_view(),
         name='fer-region-crud'),



    path('ai/consult/',
          ChatAPIView.as_view(),),

    #========================缺素识别======================
    path('nd/',
         ImageRecognitionView.as_view(),),
    # 缺素识别（带地块选择，结果写入缺素记录并生成追肥建议）
    path('user/<int:user_id>/field/<int:fieldnum>/nd/',
         NutrientRecognitionWithFieldView.as_view(), name='nutrient-recognition-with-field'),

    # 按地块查询缺素记录（数据分析用）
    path('user/<int:user_id>/field/<int:fieldnum>/deficiencies/',
         ParcelDeficiencyView.as_view(), name='parcel-deficiencies'),
    path('user/<int:user_id>/deficiencies/',
         UserAllDeficienciesView.as_view(), name='user-all-deficiencies'),
    path('user/<int:user_id>/field/<int:fieldnum>/strategy_context/',
         FieldStrategyContextView.as_view(), name='field-strategy-context'),

]