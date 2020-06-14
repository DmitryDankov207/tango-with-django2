from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .bing_search import run_query
from .models import Page, Category, User, UserProfile
from .forms import CategoryForm, PageForm, UserForm, UserProfileForm


class AboutView(View):
    def get(self, request):
        visitor_cookie_handler(request)
        return render(request, 'rango/about.html',
                      context={'visits': request.session['visits']})


def get_server_side_cookie(request, cookie,
                           default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val


def visitor_cookie_handler(request):
    """
    Get the number of visits to the site.
    We use the COOKIES.get() function to obtain the visits cookie.
    If the cookie exists, the value returned is casted to an integer.
    If the cookie doesn't exist, then the default value of 1 is used.
    """
    visits = int(get_server_side_cookie(request, 'visits', '1'))

    last_visit_cookie = get_server_side_cookie(request,
                                               'last_visit',
                                               str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7],
                                        '%Y-%m-%d %H:%M:%S')

    # If it's been more than a day since the last visit...
    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        # Update the last visit cookie now that we have updated the count
        request.session['last_visit'] = str(datetime.now())
    else:
        # Set the last visit cookie
        request.session['last_visit'] = last_visit_cookie

    # Update/set the visits cookie
    request.session['visits'] = visits


class IndexView(View):
    def get(self, request):
        category_list = Category.objects.order_by('-likes')[:5]
        context_dict = {}
        context_dict['bold_message'] = 'Crunchy, creamy, cookie, candy, cupcake!'
        context_dict['categories'] = category_list
        context_dict['pages'] = Page.objects.order_by('-views')[:5]

        return render(request, 'rango/index.html', context=context_dict)


class CategoryView(View):
    def get(self, request, category_name_slug):
        print(reverse('rango:index'))
        context_dict = {}
        try:
            category = Category.objects.get(slug=category_name_slug)
            category.views += 1
            category.save()

            pages = Page.objects.filter(category=category)
            context_dict['pages'] = pages
            context_dict['category'] = category
        except Category.DoesNotExist:
            context_dict['category'] = None
            context_dict['pages'] = None
        return render(request, 'rango/category.html', context=context_dict)

    def post(self, request, category_name_slug):
        query = request.POST['query'].strip()
        context_dict = {}

        if query:
            try:
                result_list = run_query(query)
                context_dict['result_list'] = result_list
            except:
                pass
            context_dict['query'] = query
        return render(request, 'rango/category.html', context=context_dict)


class ProfileView(View):
    def get_user_details(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        user_profile = UserProfile.objects.get_or_create(user=user)[0]
        form = UserProfileForm({'website': user_profile.website,
                            'picture': user_profile.picture})
        return (user, user_profile, form)

    @method_decorator(login_required)
    def get(self, request, username):
        try:
            (user, user_profile, form) = self.get_user_details(username)
        except TypeError:
            return redirect(reverse('rango:index'))

        context_dict = {'user_profile': user_profile,
                        'selected_user': user,
                        'form': form}
        return render(request, 'rango/profile.html', context_dict)

    @method_decorator(login_required)
    def post(self, request, username):
        try:
            (user, user_profile, form) = self.get_user_details(username)
        except TypeError:
            return redirect(reverse('rango:index'))
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save(commit=True)
            return redirect('rango:profile', user.username)
        else:
            print(form.errors)
        context_dict = {'user_profile': user_profile,
                        'selected_user': user,
                        'form': form}
        return render(request, 'rango/profile.html', context_dict)


class AddCategoryView(View):
    @method_decorator(login_required)
    def get(self, request):
        form = CategoryForm()
        return render(request, 'rango/add_category.html', {'form': form})

    @method_decorator(login_required)
    def post(self, request):
        form = CategoryForm()
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            return redirect(reverse('rango:index'))
        else:
            print(form.errors)
        return render(request, 'rango/add_category.html', {'form': form})


class AddPageView(View):
    def _get_category(self, category_name_slug):
        try:
            category = Category.objects.get(slug=category_name_slug)
        except:
            category = None
        return category

    @method_decorator(login_required)
    def get(self, request, category_name_slug):
        category = self._get_category(category_name_slug)
        if category is None:
            return redirect('/rango/')
        form = PageForm()
        context_dict = {'form': form, 'category': category}
        return render(request, 'rango/add_page.html', context=context_dict)

    @method_decorator(login_required)
    def post(self, request, category_name_slug):
        category = self._get_category(category_name_slug)
        if category is None:
            return redirect('/rango/')
        form = PageForm(request.POST)

        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()

                return redirect(reverse('rango:show_category', kwargs={'category_name_slug': category_name_slug}))
        else:
            print(form.errors)
        context_dict = {'form': form, 'category': category}
        return render(request, 'rango/add_page.html', context=context_dict)


@login_required
def register_profile(request):
    form = UserProfileForm()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()

            return redirect(reverse('rango:index'))
        else:
            print(form.errors)

    context_dict = {'form': form}

    return render(request, 'rango/profile_registration.html', context_dict)


@login_required
def user_logout(request):
    logout(request)
    return redirect(reverse('rango:index'))


def restricted(request):
    context = {
        'bold_message': "Since you're logged in, you can see this text!",
    }
    return render(request, 'rango/restricted.html', context)


# Not a view!
def get_result_list(request):
    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            try:
                result_list = run_query(query)
            except:
                print('Error with loading key.')

    return result_list


def search(request):
    result_list = get_result_list(request)
    return render(request, 'rango/search.html', {'result_list': result_list})


def goto_url(request, page_id):
    try:
        page = Page.objects.get(id=page_id)
    except:
        page = None

    if page is None:
        return redirect('/rango/')
    page.views += 1
    page.save()
    return redirect(page.url)


@login_required
def list_profiles(request):
    userprofile_list = UserProfile.objects.all()
    return render(request, 'rango/list_profiles.html',
                  {'user_profile_list': userprofile_list})


@login_required
def like_category(request, category_name_slug):
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']
    likes = 0
    if cat_id:
        cat = Category.objects.get(id=int(cat_id))
        if cat:
            likes = cat.likes + 1
            cat.likes = likes
            cat.save()
    return HttpResponse(likes)


def suggest_category(request):
    cat_list = []
    starts_with = ''
    if request.method == 'GET':
        starts_with = request.GET['suggestion']

    cat_list = get_category_list(8, starts_with)
    if len(cat_list) == 0:
        cat_list = Category.objects.order_by('-likes')

    return render(request,
                  'rango/categories.html',
                  {'categories': cat_list})


def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(
            name__istartswith=starts_with
        )
    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]
    return cat_list


@login_required
def auto_add_page(request, category_name_slug):
    cat_id = None
    url = None
    title = None
    context_dict = {}
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        url = request.GET['url']
        title = request.GET['title']
        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            p = Page.objects.get_or_create(category=category,
            title=title, url=url)
            pages = Page.objects.filter(category=category).order_by('-views')
            # Adds our results list to the template context under name pages.
            context_dict['pages'] = pages
    return render(request, 'rango/page_list.html', context_dict)
