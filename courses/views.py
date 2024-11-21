from django.forms import BaseModelForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from .models import Course
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin
)
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.base import TemplateResponseMixin, View
from .forms import ModuleFormSet
from django.apps import apps
from django.forms.models import modelform_factory
from .models import Module, Content
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from django.db.models import Count
from .models import Subject
from account.models import Profile
from account.models import AccountType
from django.views.generic.detail import DetailView
from students.forms import CourseEnrollForm
from django.core.cache import cache
from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger



class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs: reverse_lazy) -> dict[str]:

        subjects = cache.get('all_subjects')
        if not subjects:
            subjects = Subject.objects.annotate(
                total_courses=Count('courses')
            )
        cache.set('all_subjects', subjects)

        
        all_courses = cache.get('all_courses')
        if not all_courses:
            all_courses = Course.objects.annotate(
                total_modules=Count('modules'),
                total_students=Count('students')
                )
        cache.set('all_courses', all_courses)

        courses_count = cache.get('courses_count')
        if not courses_count:
            courses_count = Course.objects.count()
        cache.set('courses_count', courses_count)
        
        accounts_count = cache.get('accounts_count')
        if not accounts_count:
            accounts_count = Profile.objects.filter(type=AccountType.student).count()

        accounts = cache.get('accounts')
        if not accounts:
            accounts = Profile.objects.filter(type=AccountType.student)[:4]
        cache.set('accounts', accounts)

        students_count = cache.get('students_count')
        if not students_count:
            students_count = Profile.objects.filter(type=AccountType.student).count()
        cache.set('students_count', students_count)

        teachers_count = cache.get('teachers_count')
        if not teachers_count:
            teachers_count = Profile.objects.filter(type=AccountType.teacher).count()
        cache.set('teachers_count', teachers_count)
        
        context ={
            'subjects': subjects,
            'all_courses': all_courses,
            'accounts': accounts,
            'students_count': students_count,
            'teachers_count': teachers_count, 
            'courses_count': courses_count
        }
        return context
    

class OwnerMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)
    

class OwnerEditMixin:
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
    

class OwnerCourseMixin(
    OwnerMixin,LoginRequiredMixin, PermissionRequiredMixin):
    model = Course
    fields = ['subject', 'title', 'overview','photo']
    success_url = reverse_lazy('manage_course_list')

    
class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = 'courses/manage/course/form.html'


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = 'courses/manage/course/list.html'
    permission_required = 'courses.view_course'


class CourseCreateView(OwnerCourseEditMixin, CreateView):
    permission_required = 'courses.add_course'


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = 'courses.change_course'


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'
    permission_required = 'courses.delete_course'

# Using formsets for course modules
class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/formset.html'
    course = None

    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)
    
    def dispatch(self, request, pk):
        self.course = get_object_or_404(
            Course, id=pk, owner=request.user
        )
        return super().dispatch(request, pk)
    
    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response(
        {'course': self.course, 'formset': formset}
        )
    
    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('manage_course_list')
        return self.render_to_response(
        {'course': self.course, 'formset': formset}
        )
    
#Adding content to course modules

class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None
    obj = None
    template_name = 'courses/manage/content/form.html'

    def get_model(self, model_name):
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(
            app_label='courses', model_name=model_name
            )
        return model_name
    
    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(
        model, exclude=['owner', 'order', 'created', 'updated']
        )
        return Form(*args, **kwargs)
    
    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(
        Module, id=module_id, course__owner=request.user
        )
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(
            self.model, id=id, owner=request.user
            )
        return super().dispatch(request, module_id, model_name, id)
    
    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response(
            {'form': form, 'object': self.obj}
        )
        
    
    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(
            self.model,
            instance=self.obj,
            data=request.POST,
            files=request.FILES
        )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
        if not id:
            # new content
            Content.objects.create(module=self.module, item=obj)
            return redirect('module_content_list', self.module.id)
        return self.render_to_response(
            {'form': form, 'object': self.obj}
        )

class ContentDeleteView(View):

    def post(self, request, id):
        content = get_object_or_404(
            Content, id=id, module__course__owner=request.user
        )
        module = content.module
        content.item.delete()
        content.delete()
        return redirect('module_content_list', module.id)


#Managing modules and their contents

class ModuleContentListView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/content_list.html'

    def get(self, request, module_id):
        module = get_object_or_404(
        Module, id=module_id, course__owner=request.user
        )
        return self.render_to_response({'module': module})
    

# Reordering modules and their contents

class ModuleOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):

    def post(self, request):
        for id, order in self.request_json.items():
            Module.objects.filter(
                id=id, course__owner=request.user
            ).update(order=order)
        return self.render_json_response({'saved': 'OK'})
    

class ContentOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):

    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(
                id=id, module__course__owner=request.user
            ).update(order=order)
        return self.render_json_response({'saved': 'OK'})
    

    
# Displaying the catalog of courses

class CourseListView(TemplateResponseMixin, View):
    model = Course
    template_name = 'courses/course/list.html'

    def get(self, request, subject=None):
        
        subjects = cache.get('all_subjects')
        if not subjects:
            subjects = Subject.objects.annotate(
                total_courses=Count('courses')
            )
        cache.set('all_subjects', subjects)

        all_courses = Course.objects.annotate(
        total_modules=Count('modules'),
        total_students=Count('students')
        )

        if subject:
            subject = get_object_or_404(Subject, slug=subject)
            key = f'subject_{subject.id}_courses'
            courses = cache.get(key)
            if not courses:
                courses = all_courses.filter(subject=subject)
                cache.set(key, courses)
        else:
            courses = cache.get('all_courses')
            if not courses:
                courses = all_courses
                cache.set('all_courses', courses)
       
        if request.GET.get('sort_by'):
            courses = courses.order_by(request.GET.get('sort_by'))

        paginator = Paginator(courses, 4)
        page = request.GET.get('page')
        try:
            courses = paginator.page(page)
        except PageNotAnInteger:
            courses = paginator.page(1)
        except EmptyPage:
            courses = paginator.page(paginator.num_pages)

        return self.render_to_response(
            {
                'subjects': subjects,
                'subject': subject,
                'courses': courses
            }
        )


class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instructor = context['object'].owner
        students = Course.objects.filter(owner=instructor).annotate(
            total_students=Count('students')
            )
        context['students'] = students.count()

        context['enroll_form'] = CourseEnrollForm(
            initial={'course': self.object}
        )
        return context