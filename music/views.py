import json
import time
from django.conf import settings
from django.shortcuts import render,redirect,reverse
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest
from .models import Comment
def load_songs():
    file_path=settings.BASE_DIR/'songs.json'
    with open(file_path,'r',encoding='utf-8') as f:
        return json.load(f)
def load_artists():
    file_path = settings.BASE_DIR / 'artists.json'
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
def get_song_by_id(song_id):
    for song in load_songs():
        if song['song_id']==song_id:
            return song
    return None
def get_artist_by_id(artist_id):
    for artist in load_artists():
        if artist['artist_id']==artist_id:
            return artist
    return None
def get_songs_by_artist(artist_id):
    return [song for song in load_songs() if song['artist_id']==artist_id]
def song_list(request):
    all_songs=load_songs()
    paginator=Paginator(all_songs,20)
    total = paginator.num_pages
    page_num=request.GET.get('page',1)
    try:
        page_num=int(page_num)
    except(ValueError,TypeError):
        page_num=1
    page_num=max(1,min(page_num,total))
    if 'page' in request.GET and str(page_num) != request.GET['page']:
        params = request.GET.copy()
        params['page'] = page_num
        return redirect(f"{request.path}?{params.urlencode()}")
    page_obj=paginator.get_page(page_num)
    start=max(1,page_num-2)
    end=min(total,page_num+2)
    page_numbers=[]
    if start>1:
        page_numbers.append(1)
        if start>2:
            page_numbers.append('...')
    for num in range(start,end+1):
        page_numbers.append(num)
    if end<total:
        if end<total-1:
            page_numbers.append('...')
        page_numbers.append(total)
    context={
        'page_obj':page_obj,
        'total_pages':total,
        'current_page':page_num,
        'page_numbers':page_numbers,
    }
    return render(request,'music/song_list.html',context)
def song_detail(request,song_id):
    song=get_song_by_id(song_id)
    if not song:
        return HttpResponseBadRequest("歌曲不存在")
    if request.method=='POST':
        content=request.POST.get('content','').strip()
        if content:
            Comment.objects.create(song_id=song_id,content=content)
        return redirect(reverse('music:song_detail',args=[song_id]))
    comments=Comment.objects.filter(song_id=song_id)
    context={
        'song':song,
        'comments':comments,
    }
    return render(request,'music/song_detail.html',context)
def delete_comment(request,comment_id):
    if request.method!='POST':
        return HttpResponseBadRequest("请求方式错误")
    try:
        comment=Comment.objects.get(id=comment_id)
        song_id=comment.song_id
        comment.delete()
        return redirect(reverse('music:song_detail',args=[song_id]))
    except Comment.DoesNotExist:
        return HttpResponseBadRequest("评论不存在")
def artist_list(request):
    all_artists=load_artists()
    paginator=Paginator(all_artists,12)
    total = paginator.num_pages
    page_num=request.GET.get('page',1)
    try:
        page_num=int(page_num)
    except(ValueError,TypeError):
        page_num=1
    page_num = max(1, min(page_num, total))
    if 'page' in request.GET and str(page_num) != request.GET['page']:
        params = request.GET.copy()
        params['page'] = page_num
        return redirect(f"{request.path}?{params.urlencode()}")
    page_obj=paginator.get_page(page_num)
    start = max(1, page_num - 2)
    end = min(total, page_num + 2)
    page_numbers = []
    if start > 1:
        page_numbers.append(1)
        if start > 2:
            page_numbers.append('...')
    for num in range(start, end + 1):
        page_numbers.append(num)
    if end < total:
        if end < total - 1:
            page_numbers.append('...')
        page_numbers.append(total)
    context={
        'page_obj':page_obj,
        'total_pages':total,
        'current_page':page_num,
        'page_numbers': page_numbers,
    }
    return render(request,'music/artist_list.html',context)
def artist_detail(request,artist_id):
    artist=get_artist_by_id(artist_id)
    if not artist:
        return HttpResponseBadRequest("歌手不存在")
    artist_songs=get_songs_by_artist(artist_id)
    context={
        'artist':artist,
        'songs':artist_songs,
    }
    return render(request,'music/artist_detail.html',context)
def search(request):
    keyword=request.GET.get('keyword','').strip()
    search_type=request.GET.get('type','song')
    start_time=time.time()
    result_count=0
    if keyword:
        if search_type=='song':
            result_list=[
                song for song in load_songs()
                if keyword in song['song_name']
                or keyword in song['artist_name']
                or keyword in song['lyric']
            ]
        elif search_type=='artist':
            result_list=[
                artist for artist in load_artists()
                if keyword in artist['artist_name']
                or keyword in artist['brief_desc']
            ]
        else:
            return HttpResponseBadRequest("请搜索歌曲或歌手")
    else:
        return HttpResponseBadRequest("请输入关键词")
    result_count=len(result_list)
    cost_time=round((time.time()-start_time)*1000,2)
    paginator=Paginator(result_list,20)
    total = paginator.num_pages
    page_num=request.GET.get('page',1)
    try:
        page_num=int(page_num)
    except(ValueError,TypeError):
        page_num=1
    page_num = max(1, min(page_num, total))
    if 'page' in request.GET and str(page_num)!=request.GET['page']:
        params=request.GET.copy()
        params['page']=page_num
        return redirect(f"{request.path}?{params.urlencode()}")
    page_obj=paginator.get_page(page_num)
    start = max(1, page_num - 2)
    end = min(total, page_num + 2)
    page_numbers = []
    if start > 1:
        page_numbers.append(1)
        if start > 2:
            page_numbers.append('...')
    for num in range(start, end + 1):
        page_numbers.append(num)
    if end < total:
        if end < total - 1:
            page_numbers.append('...')
        page_numbers.append(total)
    context={
        'keyword':keyword,
        'search_type':search_type,
        'page_obj':page_obj,
        'result_count':result_count,
        'cost_time':cost_time,
        'total_pages':total,
        'current_page':page_num,
        'page_numbers':page_numbers,
    }
    return render(request,'music/search_result.html',context)