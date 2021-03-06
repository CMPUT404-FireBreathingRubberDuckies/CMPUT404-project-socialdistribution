import uuid
import json
import requests
from PIL import Image
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from django.http import HttpResponseRedirect, HttpResponse
from socialp2p.models import Author, FriendRequest, Post, Node, Comment
from socialp2p import views
from api.serializations import *
from django.contrib.auth.models import User
from rest_framework import viewsets, status, permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests

@api_view(['GET', 'POST'])
@authentication_classes((SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def author_list(request):
    if request.method == 'GET':
        authors = Author.objects.all()
        serializer = AuthorSerializer(authors, many=True)
        return Response(serializer.data)

    # elif request.method == 'POST':
    #     serializer = AuthorSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@authentication_classes((SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def author_detail(request, author_uuid):
    author = None
    # try:
    #     author_uuid = uuid.UUID(author_uuid)
    # except Exception as e:
    #     return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        author = Author.objects.get(uuid=author_uuid)
    except Exception as e:
        endpoint = '/author/'
        nodes = Node.objects.all()
        response_status = 404
        for node in nodes:
            author_uuid_str = str(author_uuid)
            url = node.host + endpoint + author_uuid_str
            r = requests.get(url, auth=(node.access_username, node.access_password))
            if r.status_code == 200:
                response_status = 200
                author = r.json()
                break
        if response_status != 200:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            if request.method == 'GET':
                return Response(author)

    if request.method == 'GET':
        serializer = AuthorSerializer(author)
        return Response(serializer.data)

    elif request.method == 'POST':
	user = User.objects.get(author=author)
	edit_firstname = request.data.get('edit_firstname')
	edit_lastname = request.data.get('edit_lastname')
	edit_email = request.data.get('edit_email')
	edit_github = request.data.get('edit_github')

	if edit_firstname=='' or edit_lastname=='' or edit_email=='':
	    return HttpResponse("field cannot be empty")

	else:
		user.first_name = edit_firstname
	    	user.last_name = edit_lastname
	    	user.email = edit_email
		author.github = edit_github
		author.save()
	    	user.save()
        	if request.POST.get('edit_pic') !='':
           		cloudinary.uploader.destroy(author.photo, invalidate = True)
           		ret = cloudinary.uploader.upload(request.FILES['edit_pic'], invalidate = True)
           		image_id = ret['public_id']
       			author.photo = image_id
	    		author.save()
	    	serializer = AuthorSerializer(author)
	    	return HttpResponseRedirect(reverse('socialp2p:profile', args=[user.author.uuid]))
    elif request.method == 'DELETE':
        author.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
def friend_request(request):
    #current_user = User.objects.get(id=request.user.id)
    #current_author = Author.objects.get(user=current_user)
    #try:
        #author = Author.objects.get(uuid=author_uuid)
    #except Author.DoesNotExist:
        #return Response(status=status.HTTP_404_NOT_FOUND)
    #user = User.objects.get(author=author)

    #if request.method == 'GET':
        #requests = FriendRequest.objects.filter(requester=current_author, accepted=False)
        #serializer = FriendRequestSerializer(requests, many=True)
        #return Response(serializer.data)
    if request.method =='POST':
        if request.is_ajax():
            local =  False
            user_uuid = json.loads(request.POST.get('author'))
            author_uuid = json.loads(request.POST.get('friend'))
            author_host = json.loads(request.POST.get('host'))

            if request.POST.get('displayname'):
                author_name = request.POST.get('displayname')
            if request.POST.get('displayName'):
                author_name = request.POST.get('displayName')

            author_url = request.POST.get('author_url')
            current_author = Author.objects.get(uuid=user_uuid)

            if Author.objects.filter(uuid=author_uuid).exists():
                friend = Author.objects.get(uuid=author_uuid)
                local = True

            if local:
                if FriendRequest.objects.filter(requester=current_author, receiver=friend).exists():
                    return HttpResponse("Already added Friend")
                else:
                    friendRequest = FriendRequest(requester=current_author, receiver=friend)
                    friendRequest.save()
                    serializer = FriendRequestSerializer(friendRequest)
                    return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                nodes = Node.objects.all()
                tempuser = User(username=author_name, password='temppass')
                tempauthor = Author(user=tempuser, uuid=author_uuid, host=author_host)
                friendRequest = FriendRequest(requester=current_author, receiver=tempauthor)
                serializer = FriendRequestSerializer(friendRequest)
                if author_host == 'project-c404.rhcloud.com/api':
                    endpoint = '/friendrequest'
                    auth_host_url = 'http://' + author_host
                else:
                    endpoint = '/api/friendrequest'
                    auth_host_url = 'http://' + author_host + '/api'
                url = 'http://' + author_host + endpoint
                for node in nodes:
                    if node.host == auth_host_url:
                        print "URL: ", url
                        headers = {'Content-type': 'application/json'}
                        r = requests.post(url, auth=(node.access_username, node.access_password), json=serializer.data, headers=headers)
                        print "RESPONSE TEXT: ", r.text
                        print "STATUS CODE: ", r.status_code
                        return Response(serializer.data, status=status.HTTP_200_OK)
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        else:
            remote_author = request.data.get('author')
            author_id = request.data.get('author').get('id')
            friend_id = request.data.get('friend').get('id')
            local_author = Author.objects.get(uuid=friend_id)

            if remote_author.get('displayname'):
                author_name = remote_author.get('displayname')
            if remote_author.get('displayName'):
                author_name = remote_author.get('displayName')

            tempuser = User(username=author_name, password="temppass")
            tempuser.save()
            tempauthor = Author(user=tempuser, uuid=author_id)
            tempauthor.save()
            friendRequest = FriendRequest(requester=tempauthor, receiver=local_author)
            friendRequest.save()
            serializer = FriendRequestSerializer(friendRequest)
            return Response(status=status.HTTP_200_OK)

@api_view(['GET', 'POST', 'DELETE'])
def friends(request, author_uuid):
    current_user = User.objects.get(id=request.user.id)
    # current_user = ''
    current_author = Author.objects.get(user=current_user)
    # current_author = ''
    try:
        author = Author.objects.get(uuid=author_uuid)
    except Author.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    user = User.objects.get(author=author)

    if request.method == 'GET':
        serializer = FriendSerializer(author)
        return Response(serializer.data)
    elif request.method == 'POST':

        if request.POST.get("accept"):
            current_author.friends.add(author)
            author.friends.add(current_author)
            friendRequest = FriendRequest.objects.get(requester=author, receiver=current_author)
            friendRequest.accepted = True
            friendRequest.save()
            return HttpResponseRedirect(reverse('socialp2p:profile', args=[request.user.author.uuid]))
	elif request.POST.get("delete"):
	    current_author.friends.remove(author)
            author.friends.remove(current_author)
	    if FriendRequest.objects.filter(requester=current_author, receiver=author).exists():
	        friendRequest = FriendRequest.objects.filter(requester=current_author, receiver=author).delete
            else:
		friendRequest = FriendRequest.objects.get(requester=author, receiver=current_author)
		friendRequest.accepted = False
		friendRequest.save()
	    return HttpResponseRedirect(reverse('socialp2p:profile', args=[request.user.author.uuid]))
	elif request.POST.get("decline"):
	    friendRequest = FriendRequest.objects.filter(requester=author, receiver=current_author).delete()
	    return HttpResponseRedirect(reverse('socialp2p:profile', args=[request.user.author.uuid]))
# Currently only returning public, private, and friends posts but not friend of friend
@api_view(['GET'])
def posts(request):
    author = Author.objects.get(user=request.user)
    queryset = Post.objects.filter(visibility="PUBLIC")

    for i in author.friends.all():
        friends_posts = Post.objects.filter(author=i, visibility="FRIENDS")
        queryset = queryset | friends_posts

    private_posts = Post.objects.filter(author=author, visibility="PRIVATE")
    friends_posts = Post.objects.filter(author=author, visibility="FRIENDS")
    queryset = queryset | friends_posts | private_posts

    page = request.query_params.get('page')
    size = request.query_params.get('size')
    size = size if size else 50

    paginator = Paginator(queryset, size)

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999),
        # deliver last page of results.
        posts = paginator.page(paginator.num_pages)

    serializer = PostSerializer(posts, many=True)

    return Response({
        "query": "posts",
        "count": len(queryset),
        "next": reverse('api:posts') + "?page=" + str(posts.next_page_number()) + "&size=" + str(size) if posts.has_next() else None,
        "previous": reverse('api:posts') + "?page=" + str(posts.previous_page_number()) + "&size=" + str(size) if posts.has_previous() else None,
        "size": size,
        "posts": serializer.data
        })

# Currently only returning public, private, and friends posts but not friend of friend
@api_view(['GET'])
def author_posts(request, author_uuid):
    request_author = Author.objects.get(uuid=author_uuid)
    request_user = User.objects.get(author=request_author)
    current_author = Author.objects.get(user=request.user)

    queryset = Post.objects.filter(author=request_author, visibility='PUBLIC')
    if current_author.uuid == request_author.uuid:
        private_posts = Post.objects.filter(author=request_author, visibility='PRIVATE')
	friend_posts = Post.objects.filter(author=request_author, visibility='FRIENDS')
	my_other_posts = Post.objects.filter(author=request_author, visibility='ONL')
	local_public_posts = Post.objects.filter(author=request_author, visibility='SERVERONLY')
	fof_posts = Post.objects.filter(author=request_author, visibility='FOAF')
	queryset = queryset | private_posts | friend_posts | my_other_posts | local_public_posts | fof_posts
    else:
	for friend in current_author.friends.all():
	    for i in friend.friends.all():
		if str(i.uuid) == str(author_uuid):
	            fof_posts = Post.objects.filter(author=i, visibility='FOAF')
                    queryset = queryset | fof_posts

        if current_author.friends.filter(user=request_user).exists():
            friend_posts = Post.objects.filter(author=request_author, visibility="FRIENDS")
            queryset = queryset | friend_posts

	if current_author.host == request_author.host:
	    local_public_posts = Post.objects.filter(author=request_author, visibility='SERVERONLY')
	    queryset = queryset | local_public_host

	only_me_post = Post.objects.filter(author=request_author, visibility='ONL', user_can_view=current_author)
	queryset = queryset | only_me_post

    page = request.query_params.get('page')
    size = request.query_params.get('size')
    size = size if size else 50

    paginator = Paginator(queryset, size)

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999),
        # deliver last page of results.
        posts = paginator.page(paginator.num_pages)

    serializer = PostSerializer(posts, many=True)

    return Response({
        "query": "posts",
        "count": len(queryset),
        "next": reverse('api:author_posts') + "?page=" + str(posts.next_page_number()) + "&size=" + str(size) if posts.has_next() else None,
        "previous": reverse('api:author_posts') + "?page=" + str(posts.previous_page_number()) + "&size=" + str(size) if posts.has_previous() else None,
        "size": size,
        "posts": serializer.data
        })

# Currently returning a list of posts, needs changes to match requirements
@api_view(['GET'])
@authentication_classes((SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def public_posts(request):
    queryset = Post.objects.filter(visibility="PUBLIC")

    page = request.query_params.get('page')
    size = request.query_params.get('size')
    size = size if size else 50

    paginator = Paginator(queryset, size)

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999),
        # deliver last page of results.
        posts = paginator.page(paginator.num_pages)

    serializer = PostSerializer(posts, many=True)

    return Response({
        "query": "posts",
        "count": len(queryset),
        "next": reverse('api:public_posts') + "?page=" + str(posts.next_page_number()) + "&size=" + str(size) if posts.has_next() else None,
        "previous": reverse('api:public_posts') + "?page=" + str(posts.previous_page_number()) + "&size=" + str(size) if posts.has_previous() else None,
        "size": size,
        "posts": serializer.data
        })

@api_view(['GET','POST', 'PUT', 'DELETE'])
@authentication_classes((SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def post_detail(request, post_uuid):
    try:
        post_uuid = uuid.UUID(post_uuid)
    except Exception as e:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        post = Post.objects.get(uuid=post_uuid)
    except Post.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PostSerializer(post)
        return Response({
            "query": "posts",
            "count": 1,
            "posts": [serializer.data]
            })

    elif request.POST.get('Update'):
        edit_content = request.data.get('post_content')
	if request.POST.get('check_remove_picture') != None:
		if post.image != None:
			cloudinary.uploader.destroy(post.image, invalidate = True)
			post.image = ''

        if request.POST.get('post_content') != None:
		post.content = edit_content

	if request.POST.get('post_image') != '':
		if post.image != None:
           		cloudinary.uploader.destroy(post.image, invalidate = True)
           	ret = cloudinary.uploader.upload(request.FILES['post_image'], invalidate = True)
           	image_id = ret['public_id']
		post.image = image_id
	post.save()
	return HttpResponseRedirect(reverse('socialp2p:profile', args=[post.author.uuid]))

    elif request.POST.get('Delete'):
	post.delete()
	print "hello"
	return HttpResponseRedirect(reverse('socialp2p:profile', args=[post.author.uuid]))
	

@api_view(['GET','POST'])
@authentication_classes((SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def post_comments(request, post_uuid):
    if request.method == 'GET':
        post = Post.objects.filter(uuid=post_uuid)
        queryset = Comment.objects.filter(post=post)

        page = request.query_params.get('page')
        size = request.query_params.get('size')
        size = size if size else 50

        paginator = Paginator(queryset, size)

        try:
            comments = paginator.page(page)
        except PageNotAnInteger:
            comments = paginator.page(1)
        except EmptyPage:
            comments = paginator.page(paginator.num_pages)

        serializer = CommentSerializer(comments, many=True)

        return Response({
            "query": "comments",
            "count": len(queryset),
            "next": reverse('api:post_comments', args=[post_uuid]) + "?page=" + str(comments.next_page_number()) + "&size=" + str(size) if comments.has_next() else None,
            "previous": reverse('api:post_comments', args=[post_uuid]) + "?page=" + str(comments.previous_page_number()) + "&size=" + str(size) if comments.has_previous() else None,
            "size": size,
            "comments": serializer.data
            })

    elif request.method == 'POST':
        data = json.loads(request.body)

        # comment_content = data.get('comment')
        # uuid = data.get('id')
        # author = data.get('author')

        # comment = Comment()
        #         content = request.POST.get('content')
        # post_uuid = request.POST.get('post')
        # comment = Comment(author=Author.objects.get(user=request.user), content=content, post=Post.objects.get(uuid=post_uuid))
        # comment.save()
        return Response({"message": "ok"})
